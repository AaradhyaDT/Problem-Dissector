#!/usr/bin/env python3
"""Evaluate Problem-Dissector against a local IEEE-Xtreme-Archive checkout.

This script does not copy corpus data into this repository. It reports constraint
extraction coverage for available statements and classifier metrics on the small
curated set linked from the archive's briefings/catalog.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dissector.adapters.ieee_xtreme import IEEEXtremeAdapter
from dissector.engine import dissect_problem


ARCHETYPE_HEADING = re.compile(
    r"^[ \t]*###[ \t]+(?P<id>0[1-9]|10)\.[ \t]+\[",
    re.MULTILINE,
)
TASK_LINK = re.compile(
    r"\]\(\.\./platforms/csacademy/tasks/(?P<slug>[A-Za-z0-9_-]+)/statement\.md\)"
)


def parse_catalog_labels(catalog_text: str) -> Tuple[Dict[str, str], List[str]]:
    """Extract curated slug -> archetype ID labels from the catalog's featured-task section.

    Only links inside section 3 (Algorithmic Archetype Profiles & Canonical Slugs)
    are treated as labels. Later cross-references elsewhere in the catalog must not
    silently inflate the benchmark or inherit the last archetype heading.
    """
    taxonomy_section = re.search(
        r"^##[ \t]+3\.[ \t]+Algorithmic Archetype Profiles[^\r\n]*\r?\n"
        r"(.*?)(?=^##[ \t]+\d+\.[ \t]|\Z)",
        catalog_text,
        re.MULTILINE | re.DOTALL,
    )
    if not taxonomy_section:
        return {}, []

    labels_by_slug: Dict[str, Set[str]] = defaultdict(set)
    current_id: Optional[str] = None
    for line in taxonomy_section.group(1).splitlines():
        heading = ARCHETYPE_HEADING.match(line)
        if heading:
            current_id = heading.group("id")
        for match in TASK_LINK.finditer(line):
            if current_id:
                labels_by_slug[match.group("slug")].add(current_id)

    ambiguous = sorted(slug for slug, labels in labels_by_slug.items() if len(labels) > 1)
    labels = {
        slug: next(iter(ids))
        for slug, ids in labels_by_slug.items()
        if len(ids) == 1
    }
    return labels, ambiguous

def _rate(numerator: int, denominator: int) -> Optional[float]:
    return round(numerator / denominator, 4) if denominator else None


def evaluate_archive(
    corpus_root: Path,
    catalog_path: Optional[Path] = None,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Run extraction diagnostics over the corpus and classification on catalog labels."""
    root = corpus_root.expanduser().resolve()
    adapter = IEEEXtremeAdapter(root)
    indexed_slugs = adapter.list_slugs()
    if limit is not None:
        indexed_slugs = indexed_slugs[:max(0, limit)]

    catalog = catalog_path or (root / "briefings" / "catalog.md")
    if catalog.is_file():
        labels, ambiguous = parse_catalog_labels(catalog.read_text(encoding="utf-8"))
    else:
        labels, ambiguous = {}, []

    rows: List[Dict[str, Any]] = []
    missing_statements: List[str] = []
    failed_tasks: List[Dict[str, str]] = []
    no_bounds: List[str] = []
    loaded = 0
    bound_task_count = 0
    heading_detected_count = 0
    multi_dimension_count = 0
    aggregate_warning_count = 0
    total_bounds = 0
    difficulty_counts: Dict[str, int] = defaultdict(int)
    confusion: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for slug in indexed_slugs:
        try:
            problem = adapter.load_problem(slug)
            if problem is None:
                missing_statements.append(slug)
                continue
            report = dissect_problem(problem)
        except Exception as exc:
            failed_tasks.append({"slug": slug, "error": f"{type(exc).__name__}: {exc}"})
            continue

        loaded += 1
        constraints = report.constraints
        variables = constraints.variables
        bounds_count = len(variables)
        total_bounds += bounds_count
        has_bounds = bounds_count > 0
        if has_bounds:
            bound_task_count += 1
        else:
            no_bounds.append(slug)

        warning_text = "\n".join(constraints.warnings)
        has_heading = "No dedicated Constraints/Restrictions heading was found" not in warning_text
        has_multiple_dimensions = any("Multiple dimensions" in w for w in constraints.warnings)
        has_aggregate_warning = any("Aggregate/summation" in w for w in constraints.warnings)
        heading_detected_count += int(has_heading)
        multi_dimension_count += int(has_multiple_dimensions)
        aggregate_warning_count += int(has_aggregate_warning)

        expected = labels.get(slug)
        predicted = [match.archetype_id for match in report.archetypes]
        top1 = predicted[0] if predicted else None
        top1_correct = expected is not None and top1 == expected
        top3_correct = expected is not None and expected in predicted[:3]
        if expected is not None and top1 is not None:
            confusion[expected][top1] += 1

        difficulty = str(problem.difficulty or "UNKNOWN").upper()
        difficulty_counts[difficulty] += 1
        rows.append({
            "slug": slug,
            "title": problem.title,
            "difficulty": difficulty,
            "parsed_bounds": bounds_count,
            "bounds": variables,
            "has_bounds": has_bounds,
            "constraints_heading_detected": has_heading,
            "multiple_dimensions_detected": has_multiple_dimensions,
            "aggregate_constraint_warning": has_aggregate_warning,
            "expected_archetype_id": expected,
            "predicted_top1_archetype_id": top1,
            "predicted_top3_archetype_ids": predicted[:3],
            "top1_correct": top1_correct if expected is not None else None,
            "top3_correct": top3_correct if expected is not None else None,
            "matched_keywords_top1": report.archetypes[0].matched_keywords if report.archetypes else [],
            "constraint_warnings": constraints.warnings,
            "analysis_url": problem.source_url,
        })

    labeled_rows = [row for row in rows if row["expected_archetype_id"] is not None]
    top1_correct_count = sum(bool(row["top1_correct"]) for row in labeled_rows)
    top3_correct_count = sum(bool(row["top3_correct"]) for row in labeled_rows)
    per_archetype: Dict[str, Dict[str, Any]] = {}
    for archetype_id in sorted(set(labels.values())):
        class_rows = [row for row in labeled_rows if row["expected_archetype_id"] == archetype_id]
        class_top1 = sum(bool(row["top1_correct"]) for row in class_rows)
        class_top3 = sum(bool(row["top3_correct"]) for row in class_rows)
        per_archetype[archetype_id] = {
            "evaluated": len(class_rows),
            "top1_correct": class_top1,
            "top1_accuracy": _rate(class_top1, len(class_rows)),
            "top3_correct": class_top3,
            "top3_accuracy": _rate(class_top3, len(class_rows)),
        }

    summary = {
        "schema_version": "problem-dissector.archive-evaluation.v1",
        "corpus_root": str(root),
        "catalog_path": str(catalog) if catalog.is_file() else None,
        "scope": "limited sample" if limit is not None else "full indexed corpus",
        "indexed_tasks_considered": len(indexed_slugs),
        "loadable_statements": loaded,
        "missing_statements": len(missing_statements),
        "failed_tasks": len(failed_tasks),
        "statement_load_rate": _rate(loaded, len(indexed_slugs)),
        "tasks_with_parsed_bounds": bound_task_count,
        "bound_extraction_coverage": _rate(bound_task_count, loaded),
        "mean_parsed_bounds_per_statement": round(total_bounds / loaded, 3) if loaded else None,
        "constraints_heading_detected": heading_detected_count,
        "constraints_heading_detection_rate": _rate(heading_detected_count, loaded),
        "tasks_flagged_as_multidimensional": multi_dimension_count,
        "aggregate_constraint_warning_count": aggregate_warning_count,
        "curated_catalog_labels": len(labels),
        "ambiguous_catalog_labels_excluded": ambiguous,
        "curated_labeled_tasks_evaluated": len(labeled_rows),
        "curated_top1_accuracy": _rate(top1_correct_count, len(labeled_rows)),
        "curated_top3_accuracy": _rate(top3_correct_count, len(labeled_rows)),
        "difficulty_distribution": dict(sorted(difficulty_counts.items())),
        "per_archetype": per_archetype,
        "top1_confusion_counts": {key: dict(value) for key, value in confusion.items()},
        "tasks_without_parsed_bounds": no_bounds,
        "missing_statement_slugs": missing_statements,
        "failed_tasks_details": failed_tasks,
        "interpretation": (
            "Constraint coverage is a diagnostic, not an accuracy score. Taxonomy metrics use only "
            "catalog featured examples (normally 50, five per archetype); these are curated labels, "
            "not an independently reviewed exhaustive ground-truth benchmark. A high score does not "
            "prove algorithmic correctness or solution quality."
        ),
    }
    return summary, rows


def _write_outputs(output_dir: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    csv_fields = [
        "slug", "title", "difficulty", "parsed_bounds", "bounds", "has_bounds",
        "constraints_heading_detected", "multiple_dimensions_detected",
        "aggregate_constraint_warning", "expected_archetype_id",
        "predicted_top1_archetype_id", "predicted_top3_archetype_ids",
        "top1_correct", "top3_correct", "matched_keywords_top1",
        "constraint_warnings", "analysis_url",
    ]
    with (output_dir / "per_task.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(row.get(key), ensure_ascii=False)
                if isinstance(row.get(key), (dict, list)) else row.get(key)
                for key in csv_fields
            })

    def pct(value: Optional[float]) -> str:
        return "n/a" if value is None else f"{value * 100:.1f}%"

    lines = [
        "# Problem-Dissector Archive Evaluation",
        "",
        f"- **Scope:** {summary['scope']}",
        f"- **Indexed tasks considered:** {summary['indexed_tasks_considered']}",
        f"- **Statements loaded:** {summary['loadable_statements']}",
        f"- **Statements missing:** {summary['missing_statements']}",
        f"- **Per-task processing failures:** {summary['failed_tasks']}",
        f"- **Statement-load rate:** {pct(summary['statement_load_rate'])}",
        f"- **Bound extraction coverage:** {pct(summary['bound_extraction_coverage'])}",
        f"- **Constraint-heading detection:** {pct(summary['constraints_heading_detection_rate'])}",
        f"- **Mean parsed variables per statement:** {summary['mean_parsed_bounds_per_statement']}",
        "",
        "## Curated archetype classification slice",
        "",
        f"- **Catalog labels:** {summary['curated_catalog_labels']}",
        f"- **Labeled tasks evaluated:** {summary['curated_labeled_tasks_evaluated']}",
        f"- **Top-1 accuracy:** {pct(summary['curated_top1_accuracy'])}",
        f"- **Top-3 accuracy:** {pct(summary['curated_top3_accuracy'])}",
        "",
        "This is a diagnostic benchmark, not a proof of algorithm correctness. See summary.json for caveats and per-archetype results.",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure Problem-Dissector extraction coverage and curated archetype ranking on IEEE-Xtreme-Archive."
    )
    parser.add_argument("--corpus-root", type=Path, required=True,
                        help="Local IEEE-Xtreme-Archive root (contains platforms/csacademy/tasks)")
    parser.add_argument("--catalog", type=Path, default=None,
                        help="Optional catalog Markdown path (default: <corpus-root>/briefings/catalog.md)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Optional task limit for a quick smoke run; omit to evaluate the full index")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/archive-evaluation"),
                        help="Directory for JSON, CSV, and Markdown results")
    args = parser.parse_args(argv)

    root = args.corpus_root.expanduser().resolve()
    if not (root / "platforms" / "csacademy" / "tasks").is_dir():
        parser.error(f"Not an archive root: {root} (expected platforms/csacademy/tasks)")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    try:
        summary, rows = evaluate_archive(root, args.catalog, args.limit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    _write_outputs(args.output_dir, summary, rows)
    print(json.dumps({
        "summary": str(args.output_dir / "summary.json"),
        "per_task_csv": str(args.output_dir / "per_task.csv"),
        "statements_loaded": summary["loadable_statements"],
        "bounds_coverage": summary["bound_extraction_coverage"],
        "curated_labeled_tasks_evaluated": summary["curated_labeled_tasks_evaluated"],
        "curated_top1_accuracy": summary["curated_top1_accuracy"],
        "curated_top3_accuracy": summary["curated_top3_accuracy"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
