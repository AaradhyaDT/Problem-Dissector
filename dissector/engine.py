import re
from typing import List
from dissector.adapters.base import RawProblemData
from dissector.constraint_analyzer import analyze_constraints
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
