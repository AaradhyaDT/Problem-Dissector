"""Best-effort constraint extraction and conservative complexity estimates."""
import math
import re
from typing import Dict, List, Tuple

from dissector.models import ComplexityTarget, ParsedConstraints

_ESTIMATE_CAP = 10**30
_BOUND_RE = re.compile(
    r"\b(?P<var>[A-Za-z][A-Za-z0-9_]*(?:\[[^\]]+\])?)\s*"
    r"(?:\\leq?|<=|<|≤|≦)\s*(?P<bound>[^$;,\n]+)",
    re.IGNORECASE,
)


def parse_numeric_val(val_str: str) -> float:
    """Parse common bounds such as 10^5, 10^{5}, 2 * 10^5, 1\\,000, and 1e5."""
    clean = str(val_str).strip().replace("$", "")
    clean = clean.replace(r"\,", "").replace(r"\;", "").replace(r"\!", "")
    clean = clean.replace(r"\cdot", "*").replace(r"\times", "*").replace("×", "*")
    clean = clean.replace(",", "")
    previous = None
    while clean != previous:
        previous = clean
        clean = re.sub(r"(?<=\d)\s+(?=\d{3}(?:\D|$))", "", clean)

    multiplied_power = re.search(
        r"(?P<mult>\d+(?:\.\d+)?)\s*(?:\*|x)\s*10\s*\^\s*"
        r"\{?(?P<power>\d+)\}?(?:\s*\+\s*(?P<offset>\d+))?",
        clean, re.IGNORECASE,
    )
    if multiplied_power:
        value = float(multiplied_power.group("mult")) * (10 ** int(multiplied_power.group("power")))
        return value + float(multiplied_power.group("offset") or 0)

    power = re.search(r"10\s*\^\s*\{?(?P<power>\d+)\}?(?:\s*\+\s*(?P<offset>\d+))?", clean)
    if power:
        return float(10 ** int(power.group("power"))) + float(power.group("offset") or 0)

    scientific = re.search(r"\d+(?:\.\d+)?\s*[eE]\s*[+-]?\s*\d+", clean)
    if scientific:
        try:
            return float(re.sub(r"\s+", "", scientific.group(0)))
        except ValueError:
            return 0.0

    number = re.search(r"\d+(?:\.\d+)?", clean)
    if number:
        try:
            return float(number.group(0))
        except ValueError:
            return 0.0
    return 0.0


def _capped(value: int) -> int:
    return min(max(0, int(value)), _ESTIMATE_CAP)


def _operation_estimates(n: int) -> Dict[str, int]:
    """Return rough operation proxies, capped to keep numbers manageable."""
    n = max(1, int(n))
    log_n = max(1, math.ceil(math.log2(max(2, n))))
    factorial = math.factorial(n) if n <= 30 else _ESTIMATE_CAP
    exponential = (2**n) * n if n <= 100 else _ESTIMATE_CAP
    return {
        "O(N!)": _capped(factorial),
        "O(2^N * N)": _capped(exponential),
        "O(N^4)": _capped(n**4),
        "O(N^3)": _capped(n**3),
        "O(N^2)": _capped(n**2),
        "O(N log N)": _capped(n * log_n),
        "O(N)": _capped(n),
        "O(log N)": _capped(log_n),
        "O(1)": 1,
    }


def derive_admissible_complexity(
    max_n: float, time_limit_ms: int = 1000, memory_limit_mb: int = 256
) -> ComplexityTarget:
    """Return a rough single-dimension complexity ceiling, not a solution recommendation."""
    finite_n = max_n if math.isfinite(max_n) else 100000.0
    n = max(1, int(math.ceil(finite_n)))
    time_ms = max(1, int(time_limit_ms))
    memory_mb = max(1, int(memory_limit_mb))
    operation_budget = max(1, int(1e8 * (time_ms / 1000.0)))
    estimates = _operation_estimates(n)

    candidate = "O(1)"
    for label, estimate in estimates.items():
        if estimate <= operation_budget:
            candidate = label
            break

    memory_budget_bytes = int(memory_mb * 1024 * 1024 * 0.5)
    if n * n * 8 <= memory_budget_bytes:
        space_guidance = "O(N^2) may fit a rough 8-byte-per-state budget; verify overhead"
    else:
        space_guidance = "Prefer O(N) auxiliary space; O(N^2) may exceed the memory limit"

    warnings = [
        "This is a heuristic ceiling, not an algorithm recommendation or a pass guarantee.",
        "The operation budget is a rule of thumb; constants, language, total test cases, and judge behavior vary.",
        "The memory estimate assumes 8 bytes per state and excludes container/runtime overhead.",
    ]
    explanation = (
        f"Using N={n:,} as a one-dimensional proxy, {candidate} is the highest checked "
        f"growth class whose rough estimate ({estimates[candidate]:,} operations) fits the "
        f"nominal budget ({operation_budget:,}). Validate against the actual algorithm, "
        "all dimensions, aggregate constraints, and implementation details."
    )
    return ComplexityTarget(
        max_operations=operation_budget,
        admissible_time_complexity=f"Up to {candidate} under a rough operation-count ceiling; validate against the problem",
        admissible_space_complexity=space_guidance,
        explanation=explanation,
        estimated_operations_by_candidate=estimates,
        warnings=warnings,
    )


def _constraints_section(statement_text: str) -> Tuple[str, bool]:
    section = re.search(
        r"^\s*#{1,6}\s*(?:input\s+)?(?:constraints|restrictions)\s*:?\s*$"
        r"\s*(.*?)(?=^\s*#{1,6}\s|\Z)",
        statement_text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if section:
        return section.group(1).strip(), True
    return statement_text, False


def analyze_constraints(
    statement_text: str, time_limit_ms: int = 1000, memory_limit_mb: int = 256
) -> ParsedConstraints:
    """Extract upper bounds and attach warnings whenever the inference is incomplete."""
    constraints_section, has_heading = _constraints_section(statement_text)
    raw_lines = [line.strip() for line in constraints_section.splitlines() if line.strip()]
    variables: Dict[str, float] = {}

    for line in raw_lines:
        for match in _BOUND_RE.finditer(line):
            name = match.group("var").strip()
            value = parse_numeric_val(match.group("bound"))
            if value > 0 and math.isfinite(value):
                variables[name] = max(variables.get(name, 0.0), value)

        for match in re.finditer(
            r"\b(?P<var>[A-Za-z][A-Za-z0-9_]*)\s+(?:is\s+)?at\s+most\s+"
            r"(?P<bound>[\d\s,^.{}+\-]+)", line, re.IGNORECASE,
        ):
            value = parse_numeric_val(match.group("bound"))
            if value > 0 and math.isfinite(value):
                name = match.group("var")
                variables[name] = max(variables.get(name, 0.0), value)

    warnings: List[str] = []
    if not has_heading:
        warnings.append("No dedicated Constraints/Restrictions heading was found; extraction used the full statement.")
    if not variables:
        warnings.append("No variable upper bounds were confidently parsed; the complexity estimate uses fallback N=100000.")
    if len(variables) > 1:
        names = ", ".join(sorted(variables))
        warnings.append(f"Multiple dimensions were parsed ({names}); this single-dimension estimate may understate costs such as O(N*M).")
    if any(re.search(r"\b(sum|summation|total over|Σ|∑)\b", line, re.IGNORECASE) for line in raw_lines):
        warnings.append("Aggregate/summation constraints may not be represented faithfully in the variable map; inspect raw_constraints.")
    warnings.append("Constraint extraction is best-effort. Review raw_constraints and verify the reported bounds before relying on the estimate.")

    if variables:
        dominant_name, dominant_value = max(variables.items(), key=lambda item: item[1])
    else:
        dominant_name, dominant_value = "N", 100000.0

    target = derive_admissible_complexity(
        dominant_value, time_limit_ms=time_limit_ms, memory_limit_mb=memory_limit_mb
    )
    target.warnings = list(dict.fromkeys(target.warnings + warnings))
    target.explanation += f" Parsed proxy dimension: {dominant_name} <= {dominant_value:g}."
    return ParsedConstraints(
        variables=variables,
        raw_constraints=raw_lines[:30],
        time_limit_ms=max(1, int(time_limit_ms)),
        memory_limit_mb=max(1, int(memory_limit_mb)),
        target_complexity=target,
        warnings=warnings,
    )
