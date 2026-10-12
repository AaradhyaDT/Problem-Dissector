import json
import warnings
from pathlib import Path

import pytest

from dissector.adapters.ieee_xtreme import IEEEXtremeAdapter
from dissector.adapters.base import RawProblemData
from dissector.constraint_analyzer import analyze_constraints, parse_numeric_val
from dissector.engine import derive_observations


def test_numeric_expressions_and_invalid_input():
    assert parse_numeric_val(r"3 \cdot 10^{4}") == 30000.0
    assert parse_numeric_val("10^9+7") == 1000000007.0
    assert parse_numeric_val("2 x 10^5") == 200000.0
    assert parse_numeric_val("not a number") == 0.0


def test_constraint_bounds_and_multiple_dimension_warning():
    statement = r"""# Sample
### Constraints
$1 \leq N \leq 10^5$
$1 \leq M \leq 2 \cdot 10^5$
"""
    parsed = analyze_constraints(statement)
    assert parsed.variables["N"] == 100000.0
    assert parsed.variables["M"] == 200000.0
    assert any("Multiple dimensions" in warning for warning in parsed.warnings)
    assert any("best-effort" in warning for warning in parsed.warnings)
    assert parsed.target_complexity.estimated_operations_by_candidate["O(N^2)"] > parsed.target_complexity.max_operations


def test_aggregate_constraint_is_flagged():
    parsed = analyze_constraints("# Problem\n### Constraints\nThe sum of N over all test cases is at most 200000.")
    assert any("Aggregate/summation" in warning for warning in parsed.warnings)


def test_missing_constraints_returns_warning():
    parsed = analyze_constraints("# Problem\nSome prose with N <= 1000.")
    assert parsed.variables.get("N") == 1000.0
    assert any("No dedicated Constraints" in warning for warning in parsed.warnings)


def test_observations_are_qualified_not_asserted_as_proof():
    problem = RawProblemData(
        slug="grid-example", title="Grid example",
        statement_markdown="You are given a grid. Find the route from A to B.",
    )
    observations = derive_observations(problem, [])
    assert any("do not assume 4- or 8-neighbor movement" in item for item in observations)


def test_adapter_is_configurable_and_rejects_unsafe_slugs(tmp_path: Path):
    tasks = tmp_path / "platforms" / "csacademy" / "tasks" / "demo_task"
    tasks.mkdir(parents=True)
    (tasks / "statement.md").write_text("# Demo\nFind a value.", encoding="utf-8")
    (tmp_path / "ledger").mkdir()
    (tmp_path / "ledger" / "tasks_index.json").write_text(
        json.dumps([{"slug": "demo_task"}, {"slug": "../outside"}, {"name": "bad"}]),
        encoding="utf-8",
    )
    adapter = IEEEXtremeAdapter(tmp_path)
    assert adapter.list_slugs() == ["demo_task"]
    assert adapter.load_problem("demo_task").title == "Demo Task"
    with pytest.raises(ValueError):
        adapter.load_problem("../outside")


def test_malformed_index_falls_back_to_folder_scan(tmp_path: Path):
    tasks = tmp_path / "platforms" / "csacademy" / "tasks" / "safe-task"
    tasks.mkdir(parents=True)
    (tmp_path / "ledger").mkdir()
    (tmp_path / "ledger" / "tasks_index.json").write_text("{invalid", encoding="utf-8")
    adapter = IEEEXtremeAdapter(tmp_path)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        assert adapter.list_slugs() == ["safe-task"]
    assert seen
