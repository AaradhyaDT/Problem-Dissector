import pytest
from dissector.constraint_analyzer import analyze_constraints, parse_numeric_val, derive_admissible_complexity
from dissector.pattern_matcher import classify_archetypes
from dissector.adapters.base import RawProblemData
from dissector.models import DissectionReport
from dissector.engine import dissect_problem


def test_parse_numeric_val():
    assert parse_numeric_val("10^5") == 100000.0
    assert parse_numeric_val("2 * 10^5") == 200000.0
    assert parse_numeric_val(r"1\,000") == 1000.0
    assert parse_numeric_val("500") == 500.0


def test_derive_admissible_complexity():
    c_small = derive_admissible_complexity(10)
    assert "O(N!)" in c_small.admissible_time_complexity

    c_bitmask = derive_admissible_complexity(20)
    assert "O(2^N" in c_bitmask.admissible_time_complexity

    c_quad = derive_admissible_complexity(2000)
    assert "O(N^2)" in c_quad.admissible_time_complexity

    c_nlogn = derive_admissible_complexity(100000)
    assert "O(N log N)" in c_nlogn.admissible_time_complexity


def test_classify_archetypes():
    tree_text = "Given a tree with N nodes and N-1 edges, find the lowest common ancestor."
    matches = classify_archetypes(tree_text)
    assert len(matches) > 0
    assert matches[0].archetype_id == "03"  # Trees & LCA

    dp_text = "Find the maximum profit to partition the array into subsets modulo 10^9+7."
    matches_dp = classify_archetypes(dp_text)
    assert len(matches_dp) > 0
    assert matches_dp[0].archetype_id == "01"  # Dynamic Programming


def test_dissect_problem():
    mock_prob = RawProblemData(
        slug="test_task",
        title="Test Task",
        statement_markdown=r"""# Test Task
You are given a tree of $N$ vertices. Find path between pairs.
### Constraints
$1 \leq N \leq 10^5$
$1 \leq M \leq 10^5$
""",
        time_limit_str="1000 ms",
        memory_limit_str="128 MB"
    )

    report = dissect_problem(mock_prob)
    assert isinstance(report, DissectionReport)
    assert report.slug == "test_task"
    assert "N" in report.constraints.variables
    assert report.constraints.variables["N"] == 100000.0
    assert "O(N log N)" in report.constraints.target_complexity.admissible_time_complexity
    assert len(report.archetypes) > 0
    assert len(report.pitfalls_and_traps) > 0


def test_build_agent_contract():
    from dissector.engine import build_agent_contract
    from dissector.contract import AgentDissectionContract

    mock_prob = RawProblemData(
        slug="grid_task",
        title="Grid Task",
        statement_markdown=r"""# Grid Task
You are given a grid of $N \times M$. Find shortest path between cells.
### Constraints
$1 \leq N \leq 1000$
$1 \leq M \leq 1000$
""",
        time_limit_str="1000 ms",
        memory_limit_str="256 MB"
    )

    report = dissect_problem(mock_prob)
    contract = build_agent_contract(report)

    assert isinstance(contract, AgentDissectionContract)
    assert contract.task_slug == "grid_task"
    assert contract.asymptotics.time_complexity == "O(N^2)"
    assert contract.guidelines.recommended_language == "C++20"
    assert "queue" in " ".join(contract.guidelines.data_structures).lower()
    assert len(contract.forbidden_approaches) > 0
    assert "Implement in C++20" in contract.agent_prompt_summary
