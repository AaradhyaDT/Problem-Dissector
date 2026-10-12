from dissector.constraint_analyzer import analyze_constraints, parse_numeric_val, derive_admissible_complexity
from dissector.pattern_matcher import classify_archetypes
from dissector.adapters.base import RawProblemData
from dissector.models import DissectionReport
from dissector.engine import dissect_problem


def test_parse_numeric_val():
    assert parse_numeric_val("10^5") == 100000.0
    assert parse_numeric_val("10^{5}") == 100000.0
    assert parse_numeric_val("2 * 10^5") == 200000.0
    assert parse_numeric_val(r"2 \cdot 10^5") == 200000.0
    assert parse_numeric_val(r"1\,000") == 1000.0
    assert parse_numeric_val("1 000 000") == 1000000.0
    assert parse_numeric_val("1e5") == 100000.0
    assert parse_numeric_val("500") == 500.0


def test_derive_admissible_complexity():
    c_small = derive_admissible_complexity(10)
    assert "O(N!)" in c_small.admissible_time_complexity

    c_bitmask = derive_admissible_complexity(20)
    assert "O(2^N * N)" in c_bitmask.admissible_time_complexity

    c_quad = derive_admissible_complexity(2000)
    assert "O(N^2)" in c_quad.admissible_time_complexity
    assert c_quad.estimated_operations_by_candidate["O(N^3)"] > c_quad.max_operations

    c_nlogn = derive_admissible_complexity(100000)
    assert "O(N log N)" in c_nlogn.admissible_time_complexity
    assert "not an algorithm recommendation" in c_nlogn.warnings[0]


def test_classify_archetypes():
    tree_text = "Given a tree with N nodes and N-1 edges, find the lowest common ancestor."
    matches = classify_archetypes(tree_text)
    assert len(matches) > 0
    assert matches[0].archetype_id == "03"
    dp_text = "Find the maximum profit to partition the array into subsets modulo 10^9+7."
    matches_dp = classify_archetypes(dp_text)
    assert len(matches_dp) > 0
    assert matches_dp[0].archetype_id == "01"
    assert matches_dp[0].score_semantics == "heuristic_keyword_match_not_probability"
    assert classify_archetypes(dp_text, top_k=0) == []


def test_dissect_problem():
    mock_prob = RawProblemData(
        slug="test_task",
        title="Test Task",
        statement_markdown=r"""# Test Task
You are given a tree of N vertices. Find path between pairs.
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
    assert report.constraints.variables["N"] == 100000.0
    assert "O(N log N)" in report.constraints.target_complexity.admissible_time_complexity
    assert report.archetypes and report.pitfalls_and_traps
    assert any("if the input is guaranteed to be a tree" in item for item in report.key_observations)


def test_build_agent_contract():
    from dissector.engine import build_agent_contract
    from dissector.contract import AgentDissectionContract

    mock_prob = RawProblemData(
        slug="grid_task",
        title="Grid Task",
        statement_markdown=r"""# Grid Task
You are given a grid of N x M. Find shortest path between cells.
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
    assert "O(N^2)" in contract.asymptotics.time_complexity
    assert contract.guidelines.recommended_language == "C++20"
    assert "graph" in " ".join(contract.guidelines.data_structures).lower()
    assert contract.analysis_caveats
    assert "independently verifying" in contract.agent_prompt_summary
