import re
from typing import List
from dissector.adapters.base import RawProblemData
from dissector.constraint_analyzer import analyze_constraints
from dissector.contract import AgentDissectionContract, AsymptoticCeiling, ImplementationGuidelines
from dissector.models import DissectionReport, EdgeCaseTrap
from dissector.pattern_matcher import classify_archetypes


def parse_time_ms(limit_str: str) -> int:
    m = re.search(r"(\d+)\s*ms", limit_str, re.I)
    if m:
        return int(m.group(1))
    m_s = re.search(r"([0-9.]+)\s*s", limit_str, re.I)
    if m_s:
        return int(float(m_s.group(1)) * 1000)
    return 1000


def parse_memory_mb(limit_str: str) -> int:
    m = re.search(r"(\d+)\s*mb", limit_str, re.I)
    if m:
        return int(m.group(1))
    return 256


def derive_observations(problem: RawProblemData, archetypes) -> List[str]:
    observations = []
    text = problem.statement_markdown.lower()

    if "palindrome" in text:
        observations.append("Subproblem exhibits optimal substructure around matching string ends: $S[i] == S[j]$.")
    if "tree" in text or "acyclic" in text:
        observations.append("Graph is a connected acyclic structure (N-1 edges). Path between any two vertices is unique.")
    if "grid" in text or "matrix" in text:
        observations.append("State can be modeled as implicit 2D/3D graph where transitions are restricted to 4 or 8 neighboring cells.")
    if "modulo" in text:
        observations.append("Arithmetic operations must apply modular reduction after every addition, subtraction, and multiplication.")
    if "permutation" in text:
        observations.append(r"Elements are a bijection of $\{1, \dots, N\}$. Cycle decomposition or inversion count may apply.")
    if not observations:
        observations.append("Problem requires transforming given input constraints into a canonical sequence of deterministic operations.")

    return observations


def derive_traps(problem: RawProblemData, constraints) -> List[EdgeCaseTrap]:
    traps = []
    text = problem.statement_markdown.lower()

    # Integer overflow check
    has_large_vals = any(v > 2e9 for v in constraints.variables.values())
    if has_large_vals or "large" in text or "sum" in text:
        traps.append(EdgeCaseTrap(
            category="Integer Overflow",
            description="Accumulating sums or computing products will exceed 32-bit signed integer limits ($2^{31}-1$).",
            mitigation="Use `long long` in C++ or arbitrary-precision integers in Python."
        ))

    # Empty / Single element
    traps.append(EdgeCaseTrap(
        category="Boundary Extremes",
        description="Verify edge scenarios where N = 1, empty operations, or when all inputs are identical/zero.",
        mitigation="Add explicit guard clauses for initial values before entering processing loops."
    ))

    # Fast I/O check
    if any(v >= 1e5 for v in constraints.variables.values()):
        traps.append(EdgeCaseTrap(
            category="I/O Bottleneck (TLE)",
            description="Input size exceeds $10^5$ tokens; default unsynced I/O will cause false Time Limit Exceeded (TLE).",
            mitigation="Include `cin.tie(NULL); ios_base::sync_with_stdio(false);` in C++ or `sys.stdin.read().split()` in Python."
        ))

    return traps


def generate_blueprint(problem: RawProblemData, target_comp, archetypes) -> str:
    primary = archetypes[0].name if archetypes else "Greedy / Simulation"
    paradigms = archetypes[0].recommended_paradigms if archetypes else ["Linear Scan"]
    
    return f"""### 🛠️ Algorithmic Blueprint & Architecture

1. **Target Complexity**: `{target_comp.admissible_time_complexity}` Time | `{target_comp.admissible_space_complexity}` Space
2. **Primary Paradigm**: **{primary}** ({', '.join(paradigms[:2])})
3. **Execution Steps**:
   - **Step 1 (Ingestion)**: Read input with fast I/O stream; parse bounds into primitives.
   - **Step 2 (State Representation)**: Pre-allocate static memory buffers or containers adhering to `{target_comp.admissible_space_complexity}`.
   - **Step 3 (Core Execution)**: Traverse/process items ensuring per-element transitions do not exceed admissible complexity budget.
   - **Step 4 (Formatting)**: Output computed scalar or sequence adhering to standard whitespace and newline invariants.
"""


def dissect_problem(problem: RawProblemData) -> DissectionReport:
    time_ms = parse_time_ms(problem.time_limit_str)
    mem_mb = parse_memory_mb(problem.memory_limit_str)

    # 1. Constraint Analysis
    constraints = analyze_constraints(problem.statement_markdown, time_ms, mem_mb)

    # 2. Archetype Pattern Matching
    archetypes = classify_archetypes(problem.statement_markdown)

    # 3. Key Observations
    observations = derive_observations(problem, archetypes)

    # 4. Traps
    traps = derive_traps(problem, constraints)

    # 5. Blueprint
    blueprint = generate_blueprint(problem, constraints.target_complexity, archetypes)

    diff = problem.difficulty.upper() if problem.difficulty else "UNKNOWN"

    return DissectionReport(
        slug=problem.slug,
        title=problem.title,
        platform=problem.platform,
        difficulty=diff,
        constraints=constraints,
        archetypes=archetypes,
        key_observations=observations,
        solution_blueprint=blueprint,
        pitfalls_and_traps=traps,
        source_url=problem.source_url
    )


def build_agent_contract(report: DissectionReport) -> AgentDissectionContract:
    """Transform a full dissection report into a concise cognitive contract for downstream agents."""
    comp = report.constraints.target_complexity
    time_bound = comp.admissible_time_complexity if comp else "O(N log N)"
    space_bound = comp.admissible_space_complexity if comp else "O(N)"
    ops_budget = comp.max_operations if comp else int(1e8)

    dominant_var = "N"
    dominant_val = 100000.0
    if report.constraints.variables:
        for k in ["N", "n", "M", "m", "K", "k"]:
            if k in report.constraints.variables:
                dominant_var = k
                dominant_val = report.constraints.variables[k]
                break

    # Determine integer width and fast I/O
    overflow_risk = any(t.category == "Integer Overflow" for t in report.pitfalls_and_traps)
    int_types = "long long / int64_t" if overflow_risk else "int (32-bit)"
    fast_io = dominant_val >= 100000.0 or any(t.category == "I/O Bottleneck (TLE)" for t in report.pitfalls_and_traps)

    # Data structures selection based on archetype
    primary_arch = report.archetypes[0] if report.archetypes else None
    arch_id = primary_arch.archetype_id if primary_arch else "00"
    arch_name = primary_arch.name if primary_arch else "General Algorithmic"

    ds_map = {
        "01": ["std::vector (1D/2D DP table)", "std::array"],
        "02": ["std::vector<std::vector<int>> (Adjacency list)", "std::queue (BFS)", "std::priority_queue (Dijkstra)"],
        "03": ["std::vector<std::vector<int>> (Tree Adj)", "int up[N][20] (Binary lifting table)"],
        "04": ["Segment Tree / Fenwick Tree (BIT)", "Disjoint Set Union (DSU)"],
        "05": ["Sieve vector<bool>", "Modular arithmetic functions"],
        "06": ["std::vector with std::sort", "Two pointers indices", "std::deque"],
        "07": ["struct Point { long long x, y; }", "std::vector<Point>"],
        "08": ["std::string", "std::vector<int> (Prefix/Z table)", "Trie Node struct"],
        "09": ["int grundy[MAX]", "Memoization cache"],
        "10": ["Query response loop with std::flush / cout << endl"],
    }
    rec_ds = ds_map.get(arch_id, ["std::vector", "std::unordered_map"])

    # Forbidden approaches based on Big-O
    forbidden = []
    if "O(N log N)" in time_bound or "O(N)" in time_bound:
        forbidden.append(f"Nested O({dominant_var}^2) iterations — will exceed judge operations budget ({ops_budget:.1e}) and trigger TLE.")
    if overflow_risk:
        forbidden.append("Using signed 32-bit int for accumulated sums/products — triggers silent integer overflow.")
    forbidden.append("Unbuffered slow standard I/O streams without fast I/O optimization.")

    # Edge cases
    edge_cases = [t.description for t in report.pitfalls_and_traps]

    prompt_summary = (
        f"Implement in C++20 with {time_bound} time and {space_bound} space complexity. "
        f"Archetype: {arch_name}. Integer types: {int_types}. "
        f"Ensure fast I/O is enabled and avoid {', '.join(forbidden[:1])}."
    )

    asymptotics = AsymptoticCeiling(
        time_complexity=time_bound,
        space_complexity=space_bound,
        ops_budget=ops_budget,
        dominant_dimension=f"{dominant_var} <= {int(dominant_val)}"
    )

    guidelines = ImplementationGuidelines(
        recommended_language="C++20",
        data_structures=rec_ds,
        fast_io_required=fast_io,
        overflow_risk=overflow_risk,
        integer_types=int_types
    )

    return AgentDissectionContract(
        task_slug=report.slug,
        title=report.title,
        platform=report.platform,
        difficulty=str(report.difficulty),
        asymptotics=asymptotics,
        archetype_id=arch_id,
        archetype_name=arch_name,
        core_invariants=report.key_observations,
        forbidden_approaches=forbidden,
        edge_case_checklist=edge_cases,
        guidelines=guidelines,
        agent_prompt_summary=prompt_summary
    )

