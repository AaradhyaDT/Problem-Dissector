---
name: problem-dissector
description: Analyze competitive programming statements locally into advisory dissection contracts with parsed bounds, candidate algorithm families and edge-case warnings. Use for offline task triage before solver reasoning.
---

# Problem Dissector Skill (`problem-dissector`)

Run these commands from the Problem-Dissector repository root. Supply the actual archive root explicitly; examples assume a sibling `Competitive-Programming` checkout. No network or model calls are needed for dissection.

For the full statement-ingestion, source-preservation, sample-extraction and verified-cache workflow, use the installed sibling skill `ieee-xtreme-preflight`, maintained in `Competitive-Programming/skills/ieee-xtreme-preflight`. Its packet builder keeps the original statement authoritative and limits solver context to one selected task.

---

## 1. Core Operating Principles

1. **Analyze without solving**: Produce advisory hypotheses without solution code. Parsed values and keyword matches do not establish an algorithm or its proof.
2. **Preserve source evidence**: Keep complete semantics, multidimensional bounds, sums across test cases, subtasks, numeric ranges and interaction rules. The largest numeric bound can understate a product such as `N*M`.
3. **Keep context bounded**: Read the selected task's output rather than batch statements or full archive logs. Batch processing and worker dispatch require a request for that scope.

---

## 2. CLI Execution Modes

The raw CLI can substitute 1000 ms and 256 MB for missing limits. Treat absent limits as unknown; verify source limits before relying on any complexity guidance. The preflight wrapper skips analysis when explicit limits are missing, conflicting or unsupported.

### Mode A: Emit Pure Agent Contract (JSON to stdout or Pipe)
```powershell
python cli/dissect.py --corpus-root ../Competitive-Programming --slug matrix_exploration --contract --quiet
```

### Mode B: Full heuristic report
```powershell
python cli/dissect.py --corpus-root ../Competitive-Programming --slug 0-k-multiple
```

### Mode C: Export Artifacts (Markdown + JSON + Contract)
Exports to `outputs/<slug>.md`, `outputs/<slug>.json`, and `outputs/contracts/<slug>.contract.json`:
```powershell
python cli/dissect.py --corpus-root ../Competitive-Programming --slug matrix_exploration --export
```

`--contract --export` exports only the contract. `--export` without `--contract` exports all three artifacts. `--output-dir` selects an explicit artifact location.

### Mode D: Bounded batch dissection
This is a finite command, not a daemon. Use only when a batch is requested:
```powershell
python cli/dissect.py --corpus-root ../Competitive-Programming --all --limit 50 --quiet
```

---

## 3. Contract Schema & Downstream Consumption

Inspect the actual emitted JSON rather than assuming a legacy example schema. Operation budgets and complexity ceilings are rules of thumb. Archetype scores are keyword evidence, not calibrated probabilities. The legacy `core_invariants` field can contain candidate observations and must not be treated as a proof.

Standalone source supports explicit limits without requiring an archive:

```powershell
python cli/dissect.py --statement-file statement.md --platform custom --time-limit "1000 ms" --memory-limit "128 MB" --contract --quiet
```

Preserve the original statement and provenance next to the advisory contract. Resolve extraction gaps before choosing an algorithm. For live contests, establish the task's AI policy before exposing its statement to an agent.

---

## 4. Integration with Fleet-Orchestrator

When a user requests solver dispatch, give the worker only the selected task packet and advisory contract. Capture JSON as UTF-8 rather than relying on shell-dependent redirection encoding. The worker verifies complete semantics and bounds, derives an approach and proof, then implements and tests. Dissection does not authorize dispatch, solution assembly or submission on its own.
