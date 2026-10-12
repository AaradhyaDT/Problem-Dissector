# Problem Dissector 🧠⚡

Algorithmic Problem Dissector & Cognitive Deconstruction Engine for Competitive Programming.

Analyzes raw competitive programming problem statements and extracts structured cognitive artifacts:
- **Constraint-Complexity Mapping**: Mathematically derives admissible Big-O asymptotic limits from input bounds ($N \leq 10^5 \implies O(N \log N)$).
- **Algorithmic Archetype Matching**: Maps problems to 10 foundational competitive programming paradigms (Dynamic Programming, Graph Theory, Range Queries, Combinatorics, etc.).
- **Cognitive Decomposition**: Formulates mathematical invariants, core observations, solution blueprints, and edge-case traps.
- **Corpus Agnostic**: Adapters for IEEE-Xtreme / CS Academy, with extensible interfaces for Codeforces, LeetCode, and AtCoder.

## Architecture

```
Problem-Dissector/
├── cli/
│   └── dissect.py                 # Interactive & batch CLI runner
├── dissector/
│   ├── __init__.py
│   ├── models.py                  # Pydantic data schemas
│   ├── constraint_analyzer.py     # Deterministic complexity bound derivation
│   ├── pattern_matcher.py         # 10-Archetype rule & heuristic classifier
│   ├── engine.py                  # Core hybrid deconstruction orchestrator
│   └── adapters/
│       ├── __init__.py
│       ├── base.py                # Abstract corpus adapter
│       └── ieee_xtreme.py         # Adapter for IEEE-Xtreme-Archive
├── schemas/
│   └── dissection.schema.json     # Standardized JSON schema
├── outputs/                       # Rendered markdown & JSON dissections
├── tests/                         # Pytest test suite
├── sync.bat / sync.ps1            # Repository synchronization & PR engine
└── AGENTS.md                      # Agent operational guidelines
```

## Quick Start

```powershell
# Dissect a single problem from the IEEE-Xtreme corpus
python cli/dissect.py --slug matrix_exploration

# Dissect with Markdown export
python cli/dissect.py --slug 0-k-multiple --export

# Run verification suite
pytest tests/ -v
```
