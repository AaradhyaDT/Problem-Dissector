# Problem Dissector

A Python tool that performs a best-effort first pass over competitive-programming problem statements. It extracts likely numeric bounds, ranks algorithmic archetypes from keyword evidence, and emits a structured report and downstream-agent contract.

## What it does (and does not do)

- **Constraint extraction:** finds common upper-bound forms such as N <= 10^5, N <= 100000, and 2 * 10^5.
- **Complexity screening:** compares rough operation-count proxies against a rule-of-thumb budget. This is a heuristic ceiling, not a proof that an algorithm passes or a claim that the problem requires that complexity.
- **Archetype ranking:** reports keyword evidence and candidate paradigms. Scores are not calibrated probabilities.
- **Candidate observations:** emits qualified structural clues, not proven invariants or a solved algorithm.
- **Agent contract:** exports typed JSON while carrying caveats and parsing warnings forward.

The original statement remains the source of truth. Always verify the constraints, all test cases, problem semantics, time/memory limits, and every candidate algorithm.

## Install

Requires Python 3.10 or later.

~~~bash
python -m pip install -e ".[dev]"
pytest -q
~~~

## Quick start

Analyze a statement file without downloading or configuring a corpus:

~~~bash
problem-dissector --statement-file ./problem.md
python cli/dissect.py --statement-file ./problem.md --json
python cli/dissect.py --statement-file ./problem.md --contract
python cli/dissect.py --statement-file ./problem.md --export --output-dir ./analysis-output
~~~

To analyze a task inside the CS Academy layout in IEEE-Xtreme-Archive, configure the archive root explicitly:

~~~bash
python cli/dissect.py --corpus-root /path/to/IEEE-Xtreme-Archive --slug matrix_exploration
~~~

Or set PROBLEM_DISSECTOR_CORPUS_ROOT to that path. The root must contain platforms/csacademy/tasks; the reader no longer assumes a developer-specific drive or directory.

Batch processing:

~~~bash
python cli/dissect.py --corpus-root /path/to/IEEE-Xtreme-Archive --all --limit 10 --export
~~~

The problem-dissector console command becomes available after running python -m pip install -e . Reports can be written as Markdown, a full JSON report, and a contract JSON file.

## Architecture

~~~text
Problem-Dissector/
├── cli/
│   └── dissect.py                 # Standalone-file and corpus CLI
├── dissector/
│   ├── models.py                  # Pydantic report models
│   ├── constraint_analyzer.py     # Best-effort bounds and operation estimates
│   ├── pattern_matcher.py         # Keyword-evidence archetype ranking
│   ├── contract.py                # Downstream-agent contract models
│   ├── engine.py                  # Analysis orchestration and caveats
│   └── adapters/
│       ├── base.py                # Adapter interface and raw problem model
│       └── ieee_xtreme.py         # Configurable local corpus reader
├── tests/                         # Unit tests and reliability regressions
└── .github/workflows/tests.yml    # Automated test suite
~~~

## Portability and corpus layout

The CS Academy adapter reads task files from:

- platforms/csacademy/tasks/<slug>/statement.md
- Optional metadata at platforms/csacademy/tasks/<slug>/problem.json
- Optional task index at ledger/tasks_index.json

Supply the archive root through --corpus-root or PROBLEM_DISSECTOR_CORPUS_ROOT. For other sources, use --statement-file or implement the adapter interface.

## Accuracy and limitations

Current archetype ranking uses keyword matches rather than semantic proof. Bounds parsing is best-effort and may not represent aggregate constraints such as sum(N), multi-dimensional complexity, or unusual statement formats accurately. Complexity estimates use a nominal rule of thumb and simplified memory assumptions. Outputs include warnings to make these limitations visible, but do not remove the need for manual review.

Before using this as an autonomous coding-agent input, build and evaluate a manually reviewed benchmark corpus and measure classification, extraction, and unsupported-observation errors.
