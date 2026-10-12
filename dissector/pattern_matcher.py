"""Evidence-weighted keyword ranking for algorithmic archetypes.

Scores are heuristic evidence totals, not calibrated probabilities. More specific
problem signals outweigh generic objective words such as "maximize" or "edges".
"""
import re
from typing import Dict, List, Tuple

from dissector.models import ArchetypeMatch


ARCHETYPE_RULES: Dict[str, Dict] = {
    "01": {
        "name": "Dynamic Programming",
        "keywords": [
            "subsequence", "maximum profit", "minimum cost", "ways to",
            "number of ways", "modulo 10^9+7", "modulo 1000000007",
            "knapsack", "partition", "longest", "optimal choice",
            "recurrence", "state transition", "subproblem",
        ],
        "paradigms": ["Linear DP", "Bitmask DP", "Tree DP", "Divide & Conquer DP", "Matrix Exponentiation"],
    },
    "02": {
        "name": "Graph Theory & Network Flows",
        "keywords": [
            "graph", "vertices", "edges", "path", "cycle", "shortest path",
            "routes", "route", "connected component", "bipartite", "flow",
            "network", "adjacency", "directed", "undirected", "tree of edges",
            "shortest route", "shortest routes", "bfs", "dfs", "dijkstra",
            "reachable", "four directions", "up, down, left or right",
        ],
        "paradigms": ["BFS / 0-1 BFS", "Dijkstra", "Floyd-Warshall", "Tarjan SCC / Bridges", "Dinic Max Flow"],
    },
    "03": {
        "name": "Trees & Lowest Common Ancestor",
        "keywords": [
            "tree", "root", "ancestor", "subtree", "parent", "leaf",
            "binary tree", "lca", "lowest common ancestor",
            "diameter of tree", "centroid", "rooted tree",
        ],
        "paradigms": ["Binary Lifting (LCA)", "Heavy-Light Decomposition", "Tree DP", "Centroid Decomposition"],
    },
    "04": {
        "name": "Range Queries & Data Structures",
        "keywords": [
            "query", "update", "range", "interval", "segment", "sum of range",
            "max of range", "point update", "range update", "subarray sum",
            "fenwick", "disjoint set", "dsu", "frequency", "frequencies",
            "count occurrences", "appear in the array", "at least k times",
            "segment tree", "range query", "range queries", "point updates",
        ],
        "paradigms": ["Segment Tree", "Fenwick (Binary Indexed) Tree", "Sparse Table", "Mo's Algorithm", "DSU"],
    },
    "05": {
        "name": "Combinatorics & Number Theory",
        "keywords": [
            "prime", "divisor", "gcd", "lcm", "modulo", "divisible",
            "combinations", "permutations", "factorial", "coprime",
            "remainder", "modular inverse", "powers of", "addition",
            "sum", "integer values", "consecutive integers",
        ],
        "paradigms": ["Sieve of Eratosthenes", "Fast Exponentiation", "Inclusion-Exclusion", "Extended Euclidean", "NTT/FFT"],
    },
    "06": {
        "name": "Greedy Algorithms & Two Pointers",
        "keywords": [
            "greedy", "sort", "sorted", "two pointers", "sliding window",
            "interval", "minimum operations", "maximize", "minimize",
            "lexicographically smallest", "monotonic", "binary search on answer",
            "minimum number", "maximum number", "minimum time",
            "minimum moment", "minimum moment in time", "selling", "sell",
        ],
        "paradigms": ["Greedy Exchange Arguments", "Two Pointers / Sliding Window", "Binary Search on Value Range", "Prefix Sums"],
    },
    "07": {
        "name": "Computational Geometry & Convex Hull",
        "keywords": [
            "coordinate", "point", "polygon", "distance", "angle", "euclidean",
            "convex hull", "bounding box", "area", "intersect", "plane",
            "circle", "vector", "slope", "matrix", "rotation", "rotations",
            "rotate", "rotated", "square matrix",
        ],
        "paradigms": ["Cross Product & Orientation", "Graham Scan / Monotone Chain", "Rotating Calipers", "Line Sweep"],
    },
    "08": {
        "name": "String Algorithms",
        "keywords": [
            "string", "strings", "substring", "prefix", "suffix", "palindrome",
            "anagram", "alphabet", "pattern matching", "lexicographical",
            "concatenation", "word", "words", "letter", "letters",
            "binary string", "binary complement", "occurrence of",
        ],
        "paradigms": ["KMP / Prefix Function", "Z-Algorithm", "Rolling Hash (Rabin-Karp)", "Trie / Aho-Corasick", "Manacher"],
    },
    "09": {
        "name": "Game Theory & Nim Games",
        "keywords": [
            "game", "player", "players", "turns", "win", "lose", "draw",
            "optimal play", "moves", "nim", "piles", "stones", "first player",
            "both play optimally", "take turns", "takes turns", "game ends",
        ],
        "paradigms": ["Sprague-Grundy Theorem", "Nim-Sum (XOR Invariant)", "Minimax with Memoization", "Retrograde Analysis"],
    },
    "10": {
        "name": "Constructive & Interactive Algorithms",
        "keywords": [
            "construct", "construction", "interaction", "interactor",
            "query protocol", "flush", "find the hidden", "ask at most",
            "guarantee", "reconstruct", "permutation construction",
            "flip the prefix", "output any", "find any", "write n as a sum",
            "consecutive integers", "representing the smallest and the largest terms",
            "interactive",
        ],
        "paradigms": ["Interactive Binary Search", "Parity & Invariant Induction", "Iterative Construction", "Graph Construction"],
    },
}


# These are deliberately strong, high-signal clues. Other listed keywords provide
# weak support only. This keeps generic words from dominating domain-specific clues.
STRONG_KEYWORD_WEIGHTS: Dict[str, Dict[str, int]] = {
    "01": {
        "dynamic programming": 6, "state transition": 5, "recurrence": 4,
        "subproblem": 4, "subsequence": 4, "maximum profit": 4,
        "number of ways": 4, "knapsack": 5, "longest increasing subsequence": 5,
        "longest common subsequence": 5, "optimal substructure": 5,
    },
    "02": {
        "shortest path": 5, "shortest route": 5, "shortest routes": 5,
        "connected component": 4, "bipartite": 4, "network flow": 5,
        "dijkstra": 5, "breadth first search": 5, "bfs": 3, "dfs": 3,
        "four directions": 4, "up, down, left or right": 4,
        "graph": 3, "reachable": 3,
    },
    "03": {
        "tree": 5, "rooted tree": 6, "lowest common ancestor": 6,
        "subtree": 4, "ancestor": 4, "diameter of tree": 6,
        "binary tree": 5, "centroid": 4,
    },
    "04": {
        "segment tree": 6, "fenwick": 5, "range query": 5,
        "range queries": 5, "point update": 5, "range update": 5,
        "frequency": 3, "frequencies": 3, "count occurrences": 4,
        "at least k times": 4,
    },
    "05": {
        "addition": 4, "sum of two integers": 6,
        "compute and output their sum": 6, "prime": 4, "divisor": 3,
        "gcd": 4, "lcm": 4, "modular inverse": 5, "prime factorization": 6,
        "coprime": 4,
    },
    "06": {
        "greedy": 6, "two pointers": 5, "sliding window": 5,
        "minimum number of bottles": 5, "minimum moment in time": 4,
        "minimum time": 3, "binary search on answer": 4,
        "minimum operations": 3,
    },
    "07": {
        "convex hull": 6, "matrix rotations": 6, "rotate a matrix": 6,
        "rotating a matrix": 6, "rotated by 90": 5, "rotation": 3,
        "rotations": 3, "polygon": 4, "euclidean": 4, "point": 2,
    },
    "08": {
        "substring": 5, "palindrome": 5, "anagram": 5,
        "pattern matching": 5, "lexicographically smallest": 4,
        "string": 3, "strings": 3, "word": 3, "words": 3,
        "letter": 3, "letters": 3, "binary complement": 4,
        "occurrence of": 3,
    },
    "09": {
        "game": 4, "both play optimally": 6, "optimal play": 5,
        "take turns": 5, "takes turns": 5, "first player": 4,
        "game ends": 4, "nim": 5, "piles": 3, "stones": 3,
    },
    "10": {
        "construct": 4, "construction": 4, "interactive": 6,
        "query protocol": 6, "find the hidden": 5, "ask at most": 5,
        "flush": 4, "permutation construction": 5, "flip the prefix": 6,
        "output any": 3, "find any": 3,
        "representing the smallest and the largest terms": 4,
    },
}


def _matches_keyword(keyword: str, text: str) -> bool:
    """Match a phrase across flexible whitespace while preserving word boundaries."""
    escaped = re.escape(keyword).replace(r"\\ ", r"\\s+")
    return re.search(r"\\b" + escaped + r"\\b", text, re.IGNORECASE) is not None


def classify_archetypes(statement_text: str, top_k: int = 3) -> List[ArchetypeMatch]:
    """Rank hypotheses by weighted keyword evidence; scores are not probabilities."""
    if top_k <= 0:
        return []

    text = re.sub(r"\\s+", " ", statement_text or "").lower()
    ranked: List[Tuple[float, int, float, int, ArchetypeMatch]] = []

    for order, (arch_id, data) in enumerate(ARCHETYPE_RULES.items()):
        strong_weights = STRONG_KEYWORD_WEIGHTS.get(arch_id, {})
        all_keywords = list(dict.fromkeys(list(data["keywords"]) + list(strong_weights)))
        evidence: List[Tuple[int, str]] = []
        score = 0.0
        strong_hits = 0
        strongest_hit = 0

        for keyword in all_keywords:
            if not _matches_keyword(keyword, text):
                continue
            default_weight = 2 if " " in keyword else 1
            weight = strong_weights.get(keyword, default_weight)
            score += weight
            evidence.append((weight, keyword))
            if keyword in strong_weights:
                strong_hits += 1
                strongest_hit = max(strongest_hit, weight)

        if score <= 0:
            continue

        evidence.sort(key=lambda item: (-item[0], -len(item[1]), item[1]))
        ranked.append((
            score,
            strong_hits,
            strongest_hit,
            -order,
            ArchetypeMatch(
                archetype_id=arch_id,
                name=data["name"],
                # Preserve the legacy field while clearly marking it as a heuristic score.
                confidence=min(0.99, round(score / 12.0, 2)),
                matched_keywords=[keyword for _, keyword in evidence[:6]],
                recommended_paradigms=data["paradigms"],
            ),
        ))

    ranked.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
    return [item[4] for item in ranked[:top_k]]
