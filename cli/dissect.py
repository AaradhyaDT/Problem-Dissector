#!/usr/bin/env python3
"""CLI for dissecting a corpus task or a standalone statement file."""
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        pass

CLI_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLI_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dissector.adapters.base import RawProblemData
from dissector.adapters.ieee_xtreme import IEEEXtremeAdapter
from dissector.engine import build_agent_contract, dissect_problem
from dissector.models import DissectionReport


class Colors:
    ENABLED = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    RESET = "\033[0m" if ENABLED else ""
    BOLD = "\033[1m" if ENABLED else ""
    GREEN = "\033[92m" if ENABLED else ""
    YELLOW = "\033[93m" if ENABLED else ""
    CYAN = "\033[96m" if ENABLED else ""
    RED = "\033[91m" if ENABLED else ""


def render_report_markdown(report: DissectionReport) -> str:
    lines = [
        f"# Problem Dissection: {report.title} ({report.slug})",
        "",
        f"- **Platform:** {report.platform}",
        f"- **Difficulty:** {report.difficulty}",
        f"- **Source URL:** {report.source_url or 'N/A'}",
        "",
        "## Constraint analysis (heuristic)",
        "",
        f"- **Time limit:** {report.constraints.time_limit_ms} ms",
        f"- **Memory limit:** {report.constraints.memory_limit_mb} MB",
        "- **Parsed upper bounds:**",
    ]
    if report.constraints.variables:
        lines.extend(
            f"  - {name} <= {value:g}"
            for name, value in report.constraints.variables.items()
        )
    else:
        lines.append("  - No bounds were confidently parsed.")

    target = report.constraints.target_complexity
    if target:
        lines.extend([
            "",
            f"- **Complexity ceiling:** {target.admissible_time_complexity}",
            f"- **Memory guidance:** {target.admissible_space_complexity}",
            f"- **Nominal operation budget:** {target.max_operations:,} (rule of thumb, not a guarantee)",
            f"- **Rationale:** {target.explanation}",
        ])

    lines.extend(["", "## Algorithmic archetype hypotheses", ""])
    if not report.archetypes:
        lines.append("No archetype received keyword evidence.")
    for match in report.archetypes:
        lines.extend([
            f"- **[{match.archetype_id}] {match.name}** — heuristic keyword-match score: {match.confidence:.2f}",
            f"  - **Matched clues:** {', '.join(match.matched_keywords)}",
            f"  - **Candidate paradigms:** {', '.join(match.recommended_paradigms)}",
        ])
    lines.append("")
    lines.append("Scores are not calibrated probabilities and do not prove an approach is correct.")

    lines.extend(["", "## Candidate observations", ""])
    lines.extend(f"- {observation}" for observation in report.key_observations)

    lines.extend(["", "## Pitfalls and edge cases", ""])
    for trap in report.pitfalls_and_traps:
        lines.append(f"- **{trap.category}:** {trap.description}")
        lines.append(f"  - **Mitigation:** {trap.mitigation}")

    warnings = list(report.constraints.warnings)
    if target:
        warnings.extend(target.warnings)
    if warnings:
        lines.extend(["", "## Analysis warnings", ""])
        lines.extend(f"- {warning}" for warning in dict.fromkeys(warnings))

    lines.extend(["", report.solution_blueprint])
    return "\n".join(lines).rstrip() + "\n"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-_")
    if not slug:
        raise ValueError("Could not derive a safe output slug from the input.")
    return slug[:120]


def _load_statement_file(path: Path, title: str | None, platform: str,
                         time_limit: str, memory_limit: str) -> RawProblemData:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Statement file does not exist: {resolved}")
    slug = _safe_slug(resolved.stem)
    return RawProblemData(
        slug=slug,
        title=title or resolved.stem.replace("_", " ").replace("-", " ").title(),
        statement_markdown=resolved.read_text(encoding="utf-8"),
        time_limit_str=time_limit,
        memory_limit_str=memory_limit,
        platform=platform,
        source_url=None,
    )


def _export_report(report: DissectionReport, contract, output_dir: Path,
                   markdown: str, export_contract_only: bool = False) -> None:
    slug = _safe_slug(report.slug)
    output_dir.mkdir(parents=True, exist_ok=True)
    if export_contract_only:
        contract_dir = output_dir / "contracts"
        contract_dir.mkdir(parents=True, exist_ok=True)
        (contract_dir / f"{slug}.contract.json").write_text(
            contract.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        return

    (output_dir / f"{slug}.md").write_text(markdown, encoding="utf-8")
    (output_dir / f"{slug}.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    contract_dir = output_dir / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / f"{slug}.contract.json").write_text(
        contract.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze a programming problem statement with best-effort heuristics."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--slug", help="Task slug from the CS Academy corpus")
    source.add_argument("--statement-file", type=Path, help="Analyze a local Markdown/text statement without a corpus")
    source.add_argument("--all", action="store_true", help="Batch-process tasks in the configured corpus")
    parser.add_argument("--corpus-root", type=Path, help="Archive root containing platforms/csacademy/tasks")
    parser.add_argument("--title", help="Title override for --statement-file")
    parser.add_argument("--platform", default="custom", help="Platform label for --statement-file (default: custom)")
    parser.add_argument("--time-limit", default="1000 ms", help="Time limit for --statement-file")
    parser.add_argument("--memory-limit", default="256 MB", help="Memory limit for --statement-file")
    parser.add_argument("--contract", action="store_true", help="Emit the downstream agent contract as JSON")
    parser.add_argument("--json", action="store_true", help="Emit the full dissection report as JSON")
    parser.add_argument("--export", action="store_true", help="Write Markdown, JSON, and contract files")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "outputs", help="Export destination")
    parser.add_argument("--limit", type=int, default=10, help="Maximum problems for --all")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress decorative console output")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be zero or greater")

    adapter = IEEEXtremeAdapter(args.corpus_root)
    if args.statement_file:
        try:
            problems: Iterable[RawProblemData] = [
                _load_statement_file(
                    args.statement_file, args.title, args.platform,
                    args.time_limit, args.memory_limit
                )
            ]
        except (OSError, UnicodeError, ValueError) as exc:
            parser.error(str(exc))
    elif args.slug:
        try:
            problem = adapter.load_problem(args.slug)
        except ValueError as exc:
            parser.error(str(exc))
        if problem is None:
            parser.error(
                f"Problem {args.slug!r} was not found under {adapter.tasks_dir}. "
                "Pass --corpus-root or set PROBLEM_DISSECTOR_CORPUS_ROOT."
            )
        problems = [problem]
    elif args.all:
        slugs = adapter.list_slugs()[: args.limit]
        if not slugs:
            parser.error(
                f"No tasks found under {adapter.tasks_dir}. Pass --corpus-root or set PROBLEM_DISSECTOR_CORPUS_ROOT."
            )
        loaded = [adapter.load_problem(slug) for slug in slugs]
        problems = [problem for problem in loaded if problem is not None]
    else:
        parser.print_help()
        return 0

    count = 0
    for problem in problems:
        report = dissect_problem(problem)
        contract = build_agent_contract(report)
        markdown = render_report_markdown(report)

        if args.export:
            _export_report(
                report, contract, args.output_dir, markdown,
                export_contract_only=args.contract,
            )

        output = (
            contract.model_dump_json(indent=2) if args.contract else
            report.model_dump_json(indent=2) if args.json else markdown
        )
        print(output, end="" if output.endswith("\n") else "\n")

        if not args.quiet and args.export:
            print(
                f"{Colors.GREEN}Exported outputs for {report.slug} to "
                f"{args.output_dir.expanduser().resolve()}{Colors.RESET}",
                file=sys.stderr,
            )
        count += 1

    if args.all and not args.quiet:
        print(f"Processed {count} task(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
