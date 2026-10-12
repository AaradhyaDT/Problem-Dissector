#!/usr/bin/env python3
"""
dissect.py - Algorithmic Problem Dissector CLI
Deconstructs competitive programming tasks into constraints, patterns, observations, and blueprints.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Fix Windows unicode stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add repo root to path
CLI_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLI_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dissector.adapters.ieee_xtreme import IEEEXtremeAdapter
from dissector.engine import dissect_problem
from dissector.models import DissectionReport


class Colors:
    ENABLED = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    RESET = "\033[0m" if ENABLED else ""
    BOLD = "\033[1m" if ENABLED else ""
    DIM = "\033[2m" if ENABLED else ""
    GREEN = "\033[92m" if ENABLED else ""
    YELLOW = "\033[93m" if ENABLED else ""
    CYAN = "\033[96m" if ENABLED else ""
    RED = "\033[91m" if ENABLED else ""
    MAGENTA = "\033[95m" if ENABLED else ""


def render_report_markdown(report: DissectionReport) -> str:
    md = f"""# 🧠 Problem Dissection: {report.title} (`{report.slug}`)

- **Platform:** {report.platform.upper()}
- **Difficulty:** `{report.difficulty}`
- **Source URL:** {report.source_url or 'N/A'}

---

## 1. ⏱️ Constraint-Complexity Budget Analysis

- **Time Limit:** `{report.constraints.time_limit_ms} ms`
- **Memory Limit:** `{report.constraints.memory_limit_mb} MB`
- **Parsed Variable Bounds:**
"""
    for k, v in report.constraints.variables.items():
        md += f"  - ${k} \\leq {int(v) if v.is_integer() else v}$\n"

    target = report.constraints.target_complexity
    if target:
        md += f"""
### Admissible Asymptotics:
- **Target Time Complexity:** `{target.admissible_time_complexity}`
- **Target Space Complexity:** `{target.admissible_space_complexity}`
- **Operations Budget:** `~{target.max_operations:.1e}` operations
- **Rationale:** {target.explanation}
"""

    md += "\n---\n\n## 2. 🎯 Algorithmic Archetype Matching\n\n"
    for a in report.archetypes:
        md += f"- **[{a.archetype_id}] {a.name}** (Confidence: `{int(a.confidence * 100)}%`)\n"
        md += f"  - *Matched Clues:* {', '.join(a.matched_keywords)}\n"
        md += f"  - *Recommended Paradigms:* {', '.join(a.recommended_paradigms)}\n"

    md += "\n---\n\n## 3. 💡 Key Mathematical & Structural Observations\n\n"
    for obs in report.key_observations:
        md += f"- {obs}\n"

    md += f"\n---\n\n## 4. ⚠️ Traps & Edge Cases\n\n"
    for trap in report.pitfalls_and_traps:
        md += f"- **{trap.category}:** {trap.description}\n"
        md += f"  - *Mitigation:* {trap.mitigation}\n"

    md += f"\n---\n\n{report.solution_blueprint}\n"
    return md


def main():
    parser = argparse.ArgumentParser(description="Algorithmic Problem Dissector CLI")
    parser.add_argument("--slug", help="Task slug to dissect (e.g. matrix_exploration, 0-k-multiple)")
    parser.add_argument("--export", action="store_true", help="Export report to outputs/<slug>.md and outputs/<slug>.json")
    parser.add_argument("--all", action="store_true", help="Batch dissect all tasks in corpus")
    parser.add_argument("--limit", type=int, default=10, help="Limit when running with --all")

    args = parser.parse_args()

    adapter = IEEEXtremeAdapter()

    if args.slug:
        problem = adapter.load_problem(args.slug)
        if not problem:
            print(f"{Colors.RED}❌ Error: Problem '{args.slug}' not found in IEEE-Xtreme corpus.{Colors.RESET}")
            sys.exit(1)

        report = dissect_problem(problem)
        rendered_md = render_report_markdown(report)

        print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================================{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🧠 PROBLEM DISSECTOR: {report.title} ({report.slug}){Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}======================================================================{Colors.RESET}\n")

        # Constraints overview
        comp = report.constraints.target_complexity
        print(f"{Colors.BOLD}Admissible Time:{Colors.RESET}   {Colors.GREEN}{comp.admissible_time_complexity if comp else 'N/A'}{Colors.RESET}")
        print(f"{Colors.BOLD}Admissible Space:{Colors.RESET}  {Colors.GREEN}{comp.admissible_space_complexity if comp else 'N/A'}{Colors.RESET}")
        print(f"{Colors.BOLD}Primary Archetype:{Colors.RESET} {Colors.YELLOW}{report.archetypes[0].name if report.archetypes else 'Unknown'}{Colors.RESET}")
        print(f"{Colors.BOLD}Rationale:{Colors.RESET}         {comp.explanation if comp else 'N/A'}\n")

        print(f"{Colors.BOLD}Key Observations:{Colors.RESET}")
        for obs in report.key_observations:
            print(f"  • {obs}")

        print(f"\n{Colors.BOLD}Traps & Edge Cases:{Colors.RESET}")
        for t in report.pitfalls_and_traps:
            print(f"  ⚠️  [{Colors.RED}{t.category}{Colors.RESET}] {t.description}")

        if args.export:
            out_dir = REPO_ROOT / "outputs"
            out_dir.mkdir(exist_ok=True)
            md_path = out_dir / f"{report.slug}.md"
            json_path = out_dir / f"{report.slug}.json"

            md_path.write_text(rendered_md, encoding="utf-8")
            json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

            print(f"\n{Colors.GREEN}✓ Exported Dissection Report to:{Colors.RESET}")
            print(f"  Markdown: {md_path}")
            print(f"  JSON:     {json_path}")

    elif args.all:
        slugs = adapter.list_slugs()[:args.limit]
        print(f"{Colors.CYAN}Dissecting {len(slugs)} tasks...{Colors.RESET}")
        out_dir = REPO_ROOT / "outputs"
        out_dir.mkdir(exist_ok=True)

        for s in slugs:
            prob = adapter.load_problem(s)
            if prob:
                rep = dissect_problem(prob)
                md = render_report_markdown(rep)
                (out_dir / f"{rep.slug}.md").write_text(md, encoding="utf-8")
                print(f"  ✓ Processed: {rep.slug:<28} -> {rep.archetypes[0].name if rep.archetypes else 'General'}")

        print(f"\n{Colors.GREEN}✓ Batch dissection completed! Saved to {out_dir}{Colors.RESET}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
