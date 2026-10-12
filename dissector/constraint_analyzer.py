import re
from typing import Dict, List, Tuple
from dissector.models import ComplexityTarget, ParsedConstraints


def parse_numeric_val(val_str: str) -> float:
    r"""Parse latex or plain expressions like 10^5, 1000, 2 * 10^5, 1\,000, 1 000 into float."""
    # First collapse digit-space-digit patterns like '1 000' or '10 000'
    clean = re.sub(r"(\d)\s+(\d{3})\b", r"\1\2", val_str)
    clean = clean.replace(r"\,", "").replace(",", "").replace(r"\ ", "").strip()
    
    # Check scientific / power 10^X or 10^{X}
    m_pow = re.search(r"10\^\{?(\d+)\}?", clean)
    if m_pow:
        power = int(m_pow.group(1))
        # Check multiplier like 2 * 10^5 or 2 \cdot 10^5
        m_mult = re.search(r"(\d+(?:\.\d+)?)\s*(?:\*|\\cdot|x)\s*10\^", clean)
        multiplier = float(m_mult.group(1)) if m_mult else 1.0
        return multiplier * (10 ** power)

    # Simple integer / float
    m_num = re.search(r"(\d+(?:\.\d+)?)", clean)
    if m_num:
        return float(m_num.group(1))
    return 0.0


def derive_admissible_complexity(max_n: float, time_limit_ms: int = 1000) -> ComplexityTarget:
    """
    Derives admissible Big-O asymptotic limits from max N and execution time.
    Standard rule of thumb: ~10^8 operations per second in C++ / CP judges.
    """
    judge_ops_budget = int(1e8 * (time_limit_ms / 1000.0))

    if max_n <= 12:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N!) or O(2^N * N^2)",
            admissible_space_complexity="O(N)",
            explanation=f"With N <= {int(max_n)}, factorial permutations or Hamiltonian DP/TSP is fully feasible."
        )
    elif max_n <= 22:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(2^N * N) or O(2^N)",
            admissible_space_complexity="O(2^N) or O(N)",
            explanation=f"With N <= {int(max_n)}, bitmask dynamic programming or meet-in-the-middle subset generation is optimal."
        )
    elif max_n <= 50:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N^4) or O(N^3)",
            admissible_space_complexity="O(N^2)",
            explanation=f"With N <= {int(max_n)}, 3D/4D DP, Floyd-Warshall, or Gaussian elimination fits well within {judge_ops_budget} ops."
        )
    elif max_n <= 500:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N^3)",
            admissible_space_complexity="O(N^2)",
            explanation=f"With N <= {int(max_n)}, cubic algorithms (Floyd-Warshall, interval DP, matrix multiplication) will pass comfortably."
        )
    elif max_n <= 5000:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N^2)",
            admissible_space_complexity="O(N^2) or O(N)",
            explanation=f"With N <= {int(max_n)}, quadratic algorithms (nested loops, 2D DP table, all-pairs checks) fit within budget."
        )
    elif max_n <= 200000:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N log N) or O(N log^2 N)",
            admissible_space_complexity="O(N)",
            explanation=f"With N <= {int(max_n)}, sorting, divide & conquer, Segment Trees, Fenwick Trees, or Priority Queues are required."
        )
    elif max_n <= 10000000:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(N) or O(N log log N)",
            admissible_space_complexity="O(N)",
            explanation=f"With N <= {int(max_n)}, linear scans, two pointers, prefix sums, or linear prime sieves (Sieve of Eratosthenes) are mandatory."
        )
    else:
        return ComplexityTarget(
            max_operations=judge_ops_budget,
            admissible_time_complexity="O(log N) or O(1) or O(sqrt(N))",
            admissible_space_complexity="O(1)",
            explanation=f"With N up to {max_n:.0e}, values exceed 10^7. Requires logarithmic binary search, matrix exponentiation, prime factorization O(sqrt(N)), or closed-form math."
        )


def analyze_constraints(statement_text: str, time_limit_ms: int = 1000, memory_limit_mb: int = 256) -> ParsedConstraints:
    """Extract constraint variables from problem statement and calculate admissible complexity."""
    constraints_section = ""
    
    # Locate constraints section (supports Constraints, Restrictions, Notes, etc.)
    m_section = re.search(r"###\s*(?:Constraints|Restrictions).*?\n(.*?)(?:\n###|\n\||\Z)", statement_text, re.DOTALL | re.I)
    if m_section:
        constraints_section = m_section.group(1).strip()
    else:
        # Fallback to whole text
        constraints_section = statement_text

    raw_lines = [line.strip() for line in constraints_section.splitlines() if line.strip()]
    variables: Dict[str, float] = {}

    # Pattern for bounds: e.g., $1 \leq N \leq 10^5$, $1 \leq N \leq 1 000$, or $N \le 2000$
    bound_patterns = [
        r"(?:[\$0-9\.\s\\leleq]+)?\s*([A-Za-z](?:_[A-Za-z0-9]+)?)\s*(?:\\le|\\leq|<=|<)\s*([0-9\^\{\}\\\,\.\s]+?)(?:(?=\$)|;|\n|\Z)",
        r"([A-Za-z](?:_[A-Za-z0-9]+)?)\s*(?:is between|between)\s*.*?(?:and|\sto\s)\s*([0-9\^\{\}\\\,\.\s]+)",
    ]

    for line in raw_lines:
        for pat in bound_patterns:
            matches = re.finditer(pat, line)
            for m in matches:
                var_name = m.group(1).replace("$", "").strip()
                val_raw = m.group(2).replace("$", "").strip()
                val = parse_numeric_val(val_raw)
                if val > 0:
                    # Keep maximum bound discovered for this variable
                    if var_name not in variables or val > variables[var_name]:
                        variables[var_name] = val

    # Find dominant dimension for time complexity derivation (usually N or M or length)
    dominant_n = 100000.0  # Safe default if none found
    for cand in ["N", "n", "M", "m", "K", "k", "L", "length"]:
        if cand in variables:
            dominant_n = variables[cand]
            break
    if dominant_n == 100000.0 and variables:
        dominant_n = max(variables.values())

    target_comp = derive_admissible_complexity(dominant_n, time_limit_ms)

    return ParsedConstraints(
        variables=variables,
        raw_constraints=raw_lines[:15],
        time_limit_ms=time_limit_ms,
        memory_limit_mb=memory_limit_mb,
        target_complexity=target_comp
    )
