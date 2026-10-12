"""Keyword-based archetype ranking; scores are not calibrated probabilities."""
import re
from typing import Dict, List

from dissector.models import ArchetypeMatch


ARCHETYPE_RULES: Dict[str, Dict] = {
    "01": {"name": "Dynamic Programming", "keywords": ["subsequence", "maximum profit", "minimum cost", "ways to", "number of ways", "modulo 10^9+7", "modulo 1000000007", "knapsack", "partition", "longest", "optimal choice"], "paradigms": ["Linear DP", "Bitmask DP", "Tree DP", "Divide & Conquer DP", "Matrix Exponentiation"]},
    "02": {"name": "Graph Theory & Network Flows", "keywords": ["graph", "vertices", "edges", "path", "cycle", "shortest path", "grid", "connected component", "bipartite", "flow", "network", "adjacency", "directed", "undirected", "tree of edges"], "paradigms": ["BFS / 0-1 BFS", "Dijkstra", "Floyd-Warshall", "Tarjan SCC / Bridges", "Dinic Max Flow"]},
    "03": {"name": "Trees & Lowest Common Ancestor", "keywords": ["tree", "root", "ancestor", "subtree", "parent", "leaf", "binary tree", "lca", "lowest common ancestor", "diameter of tree", "centroid"], "paradigms": ["Binary Lifting (LCA)", "Heavy-Light Decomposition", "Tree DP", "Centroid Decomposition"]},
    "04": {"name": "Range Queries & Data Structures", "keywords": ["query", "update", "range", "interval", "segment", "sum of range", "max of range", "point update", "range update", "subarray sum", "fenwick", "disjoint set", "dsu"], "paradigms": ["Segment Tree", "Fenwick (Binary Indexed) Tree", "Sparse Table", "Mo's Algorithm", "DSU"]},
    "05": {"name": "Combinatorics & Number Theory", "keywords": ["prime", "divisor", "gcd", "lcm", "modulo", "divisible", "combinations", "permutations", "factorial", "coprime", "remainder", "modular inverse", "powers of"], "paradigms": ["Sieve of Eratosthenes", "Fast Exponentiation", "Inclusion-Exclusion", "Extended Euclidean", "NTT/FFT"]},
    "06": {"name": "Greedy Algorithms & Two Pointers", "keywords": ["greedy", "sort", "sorted", "two pointers", "sliding window", "interval", "minimum operations", "maximize", "minimize", "lexicographically smallest", "monotonic", "binary search on answer"], "paradigms": ["Greedy Exchange Arguments", "Two Pointers / Sliding Window", "Binary Search on Value Range", "Prefix Sums"]},
    "07": {"name": "Computational Geometry & Convex Hull", "keywords": ["coordinate", "point", "polygon", "distance", "angle", "euclidean", "convex hull", "bounding box", "area", "intersect", "plane", "circle", "vector", "slope"], "paradigms": ["Cross Product & Orientation", "Graham Scan / Monotone Chain", "Rotating Calipers", "Line Sweep"]},
    "08": {"name": "String Algorithms", "keywords": ["string", "substring", "prefix", "suffix", "palindrome", "anagram", "character", "alphabet", "pattern matching", "lexicographical", "concatenation"], "paradigms": ["KMP / Prefix Function", "Z-Algorithm", "Rolling Hash (Rabin-Karp)", "Trie / Aho-Corasick", "Manacher"]},
    "09": {"name": "Game Theory & Nim Games", "keywords": ["game", "player", "turns", "win", "lose", "draw", "optimal play", "moves", "nim", "piles", "stones", "first player"], "paradigms": ["Sprague-Grundy Theorem", "Nim-Sum (XOR Invariant)", "Minimax with Memoization", "Retrograde Analysis"]},
    "10": {"name": "Constructive & Interactive Algorithms", "keywords": ["construct", "interaction", "interactor", "query protocol", "flush", "find the hidden", "ask at most", "guarantee", "reconstruct", "permutation construction"], "paradigms": ["Interactive Binary Search", "Parity & Invariant Induction", "Iterative Construction", "Graph Construction"]},
}


def classify_archetypes(statement_text: str, top_k: int = 3) -> List[ArchetypeMatch]:
    """Rank by keyword evidence. The score must not be read as a probability."""
    if top_k <= 0:
        return []
    text_lower = statement_text.lower()
    scores: List[ArchetypeMatch] = []
    for arch_id, data in ARCHETYPE_RULES.items():
        matched_kw, weight = [], 0
        for keyword in data["keywords"]:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
                matched_kw.append(keyword)
                weight += 2 if " " in keyword else 1
        if matched_kw:
            scores.append(ArchetypeMatch(
                archetype_id=arch_id, name=data["name"],
                confidence=min(0.99, round(weight / 8.0, 2)),
                matched_keywords=matched_kw[:6],
                recommended_paradigms=data["paradigms"],
            ))
    scores.sort(key=lambda match: match.confidence, reverse=True)
    return scores[:top_k]
