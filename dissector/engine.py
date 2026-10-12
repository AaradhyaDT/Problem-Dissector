"""Problem dissection pipeline; hypotheses must not be mistaken for proofs."""
import re
from typing import List

from dissector.adapters.base import RawProblemData
from dissector.constraint_analyzer import analyze_constraints
from dissector.contract import AgentDissectionContract, AsymptoticCeiling, ImplementationGuidelines
from dissector.models import DissectionReport, EdgeCaseTrap
from dissector.pattern_matcher import classify_archetypes


def parse_time_ms(limit_str: str) -> int:
    text = str(limit_str or "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*ms\b", text, re.IGNORECASE)
    if match:
        return max(1, int(float(match.group(1))))
    seconds = re.search(r"(\d+(?:\.\d+)?)\s*s\b", text, re.IGNORECASE)
    if seconds:
        return max(1, int(float(seconds.group(1)) * 1000))
    return 1000


def parse_memory_mb(limit_str: str) -> int:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mib|mb)\b", str(limit_str or ""), re.IGNORECASE)
    return max(1, int(float(match.group(1)))) if match else 256


def derive_observations(problem: RawProblemData, archetypes) -> List[str]:
    """Return qualified clues rather than asserting unproven invariants."""
    observations: List[str] = []
    text = problem.statement_markdown.lower()

    if re.search(r"\bpalindrome(s)?\b", text):
        observations.append(
            "Potential string clue: palindrome conditions often compare mirrored positions; derive the exact invariant from the statement before selecting a string or DP technique."
        )
    if re.search(r"\btrees?\b", text):
        observations.append(
            "Structural clue: if the input is guaranteed to be a tree, it is connected and acyclic and each vertex pair has a unique simple path; confirm the guarantee and scope."
        )
    if re.search(r"\bgrid\b|\bmatrix\b", text):
        observations.append(
            "State-model clue: grid cells may be modeled as graph states. Allowed moves, blocked cells, diagonals, and wraparound must come from the statement; do not assume 4- or 8-neighbor movement."
        )
    if "modulo" in text or re.search(r"\bmod\s+\d+", text):
        observations.append(
            "Modular-arithmetic clue: establish which outputs or intermediate values require the modulus; handle subtraction and multiplication according to the language and required output."
        )
    if re.search(r"\bpermutation(s)?\b", text):
        observations.append(
            "Input-structure clue: if input is guaranteed to be a permutation, each permitted value occurs exactly once. Cycle decomposition or inversion counting applies only if it supports the objective."
        )
    if not observations:
        observations.append(
            "No high-confidence structural observation was inferred from keywords. Derive invariants from the formal statement, examples, and constraints; archetype ranking is not proof."
        )
    return observations


def derive_traps(problem: RawProblemData, constraints) -> List[EdgeCaseTrap]:
    traps: List[EdgeCaseTrap] = []
    text = problem.statement_markdown.lower()
    bounds = list(constraints.variables.values())
    possible_overflow = (
        any(value > 2**31 - 1 for value in bounds)
        or bool(re.search(r"\b(sum|product|multiply|squared|square)\b", text))
    )
    if possible_overflow:
        traps.append(EdgeCaseTrap(
            category="Potential Integer Overflow",
            description="Large values or arithmetic operations may exceed a 32-bit signed integer; this is a risk flag, not proof that overflow occurs.",
            mitigation="Derive maximum intermediate values from constraints and use a sufficiently wide type (such as int64_t in C++) when required.",
        ))

    traps.append(EdgeCaseTrap(
        category="Boundary Extremes",
        description="Check minimum-size cases, empty-operation cases if allowed, duplicates, all-equal values, zero/negative values, and unreachable states where relevant.",
        mitigation="Build edge cases from the statement's guarantees; do not assume N=0 or negative values are valid.",
    ))
    if any(value >= 100000 for value in bounds):
        traps.append(EdgeCaseTrap(
            category="Large-Input Performance",
            description="At least one parsed dimension reaches 100000. Check total input volume and aggregate test cases; nested quadratic scans may be too expensive.",
            mitigation="Estimate actual total work. Fast I/O may help with large token counts, but dimension size alone does not prove an I/O bottleneck.",
        ))
    return traps


def generate_blueprint(problem: RawProblemData, target_comp, archetypes) -> str:
    primary = archetypes[0].name if archetypes else "Unclassified"
    paradigms = archetypes[0].recommended_paradigms if archetypes else []
    return f"""### Preliminary implementation checklist (not a proven solution)

1. **Constraint ceiling:** {target_comp.admissible_time_complexity}; {target_comp.admissible_space_complexity}.
2. **Keyword-based archetype hypothesis:** {primary}. Possible paradigms: {", ".join(paradigms[:2]) if paradigms else "none inferred"}.
3. **Verify the model:** identify input guarantees, state space, valid transitions, objective, and output from the full statement.
4. **Validate complexity:** account for every dimension, all test cases, preprocessing, and auxiliary memory.
5. **Test the reasoning:** check examples and construct boundary cases from the actual guarantees.

The analyzer does not prove a solution or infer problem-specific transitions. Verify the algorithm independently.
"""


def dissect_problem(problem: RawProblemData) -> DissectionReport:
    constraints = analyze_constraints(
        problem.statement_markdown,
        time_limit_ms=parse_time_ms(problem.time_limit_str),
        memory_limit_mb=parse_memory_mb(problem.memory_limit_str),
    )
    archetypes = classify_archetypes(problem.statement_markdown)
    observations = derive_observations(problem, archetypes)
    traps = derive_traps(problem, constraints)
    blueprint = generate_blueprint(problem, constraints.target_complexity, archetypes)
    difficulty = problem.difficulty.upper() if problem.difficulty else "UNKNOWN"
    if difficulty not in {"TUTORIAL", "EASY", "MEDIUM", "HARD", "UNKNOWN"}:
        difficulty = "UNKNOWN"
    return DissectionReport(
        slug=problem.slug, title=problem.title, platform=problem.platform,
        difficulty=difficulty, constraints=constraints, archetypes=archetypes,
        key_observations=observations, solution_blueprint=blueprint,
        pitfalls_and_traps=traps, source_url=problem.source_url,
    )


def build_agent_contract(report: DissectionReport) -> AgentDissectionContract:
    """Build a structured contract with uncertainty carried forward."""
    comp = report.constraints.target_complexity
    time_bound = comp.admissible_time_complexity if comp else "No reliable ceiling inferred; analyze manually"
    space_bound = comp.admissible_space_complexity if comp else "No reliable space guidance inferred"
    ops_budget = comp.max_operations if comp else 0

    if report.constraints.variables:
        dominant_var, dominant_val = max(report.constraints.variables.items(), key=lambda item: item[1])
    else:
        dominant_var, dominant_val = "N", 100000.0

    caveats = list(report.constraints.warnings)
    if comp:
        caveats.extend(comp.warnings)
    caveats.extend([
        "Archetype scores are keyword-match scores, not calibrated probabilities.",
        "Generated observations are candidate clues, not proven solution invariants.",
        "Validate every recommendation against the full statement before implementation.",
    ])
    caveats = list(dict.fromkeys(caveats))

    overflow_risk = any("Overflow" in trap.category for trap in report.pitfalls_and_traps)
    integer_types = (
        "Prove maximum intermediate values; use int64_t/long long where required"
        if overflow_risk else
        "Choose integer width from proven input and accumulator bounds"
    )
    fast_io_may_help = dominant_val >= 100000.0

    primary = report.archetypes[0] if report.archetypes else None
    arch_id = primary.archetype_id if primary else "00"
    arch_name = primary.name if primary else "Unclassified (no keyword evidence)"
    structure_map = {
        "01": ["Choose a DP state/table only after proving a recurrence"],
        "02": ["Choose graph representation and BFS/Dijkstra/etc. from graph and edge-weight semantics"],
        "03": ["Use tree structures only if the input is guaranteed to be a tree"],
        "04": ["Consider Segment Tree/Fenwick/DSU only if query/update operations justify them"],
        "05": ["Choose number-theory tools from the exact mathematical requirements"],
        "06": ["Use greedy/two pointers only after establishing ordering or an exchange argument"],
        "07": ["Use geometry techniques only if the constraints and objective require them"],
        "08": ["Choose string algorithms after identifying the matching or substring requirement"],
        "09": ["Prove game states and winning conditions before using Grundy/minimax methods"],
        "10": ["Derive the construction or interaction protocol from the statement"],
    }
    recommended_structures = structure_map.get(
        arch_id, ["No specific data structure is justified by the available keyword evidence"]
    )

    estimates = comp.estimated_operations_by_candidate if comp else {}
    forbidden = []
    if estimates.get("O(N^2)", 0) > ops_budget:
        forbidden.append("Do not use a quadratic algorithm without a stronger bound or proof that the real workload is smaller.")
    if overflow_risk:
        forbidden.append("Do not assume 32-bit arithmetic is safe; prove intermediate bounds or use a wider type.")

    prompt_summary = (
        f"Implement in C++20 only after independently verifying the algorithm. "
        f"Constraint analysis suggests: {time_bound}; space guidance: {space_bound}. "
        f"Primary keyword hypothesis: {arch_name}. Check the caveats and derive actual invariants, "
        f"transitions, total test-case work, and integer bounds from the full statement."
    )

    return AgentDissectionContract(
        task_slug=report.slug, title=report.title, platform=report.platform,
        difficulty=str(report.difficulty),
        asymptotics=AsymptoticCeiling(
            time_complexity=time_bound, space_complexity=space_bound, ops_budget=ops_budget,
            dominant_dimension=f"{dominant_var} <= {int(dominant_val)} (largest parsed bound proxy)",
        ),
        archetype_id=arch_id, archetype_name=arch_name,
        core_invariants=report.key_observations, forbidden_approaches=forbidden,
        edge_case_checklist=[trap.description for trap in report.pitfalls_and_traps],
        guidelines=ImplementationGuidelines(
            recommended_language="C++20", data_structures=recommended_structures,
            fast_io_may_help=fast_io_may_help, overflow_risk=overflow_risk, integer_types=integer_types,
        ),
        analysis_caveats=caveats, agent_prompt_summary=prompt_summary,
    )
