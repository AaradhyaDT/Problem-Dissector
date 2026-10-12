from pathlib import Path

from scripts.evaluate_archive import evaluate_archive, parse_catalog_labels


def test_parse_catalog_labels_uses_archetype_sections_and_marks_ambiguity():
    catalog = """# Master Catalog

### 01. [Dynamic Programming](01_dynamic_programming.md)
- [dp-task](../platforms/csacademy/tasks/dp-task/statement.md)
- [shared-task](../platforms/csacademy/tasks/shared-task/statement.md)

### 02. [Graph Theory & Network Flows](02_graph.md)
- [graph-task](../platforms/csacademy/tasks/graph-task/statement.md)
- [shared-task](../platforms/csacademy/tasks/shared-task/statement.md)
"""
    labels, ambiguous = parse_catalog_labels(catalog)
    assert labels == {"dp-task": "01", "graph-task": "02"}
    assert ambiguous == ["shared-task"]


def test_evaluate_archive_reports_missing_statements_and_curated_scores(tmp_path: Path):
    tasks_root = tmp_path / "platforms" / "csacademy" / "tasks"
    tasks_root.mkdir(parents=True)
    problem = tasks_root / "addition"
    problem.mkdir()
    statement_text = r"""# Addition
### Constraints and notes
$1 \leq A \leq 100$
"""
    (problem / "statement.md").write_text(statement_text, encoding="utf-8")
    (problem / "problem.json").write_text(
        '{"slug":"addition","title":"Addition","difficulty":"TUTORIAL","time_limit":"500 ms","memory_limit":"128 MB"}',
        encoding="utf-8",
    )
    (tasks_root / "not-archived").mkdir()
    (tmp_path / "ledger").mkdir()
    (tmp_path / "ledger" / "tasks_index.json").write_text(
        '[{"slug":"addition"},{"slug":"not-archived"}]', encoding="utf-8"
    )
    (tmp_path / "briefings").mkdir()
    (tmp_path / "briefings" / "catalog.md").write_text(
        "### 05. [Combinatorics & Number Theory](05.md)\n"
        "- [addition](../platforms/csacademy/tasks/addition/statement.md)\n",
        encoding="utf-8",
    )

    summary, rows = evaluate_archive(tmp_path)

    assert summary["indexed_tasks_considered"] == 2
    assert summary["loadable_statements"] == 1
    assert summary["missing_statements"] == 1
    assert summary["tasks_with_parsed_bounds"] == 1
    assert summary["constraints_heading_detected"] == 1
    assert summary["curated_labeled_tasks_evaluated"] == 1
    assert len(rows) == 1
    assert rows[0]["expected_archetype_id"] == "05"
