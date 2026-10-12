"""Reader for the CS Academy task layout inside IEEE-Xtreme-Archive."""
import json
import os
import re
import warnings
from pathlib import Path
from typing import List, Optional

from dissector.adapters.base import BaseCorpusAdapter, RawProblemData


SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DEFAULT_TASKS_RELATIVE_PATH = Path("platforms") / "csacademy" / "tasks"


class IEEEXtremeAdapter(BaseCorpusAdapter):
    def __init__(self, root_path: Optional[Path] = None):
        configured_root = root_path or os.environ.get("PROBLEM_DISSECTOR_CORPUS_ROOT")
        # Defaults to the current directory; --corpus-root removes ambiguity.
        self.root = Path(configured_root or Path.cwd()).expanduser().resolve()
        self.tasks_dir = self.root / DEFAULT_TASKS_RELATIVE_PATH
        self.index_file = self.root / "ledger" / "tasks_index.json"

    def list_slugs(self) -> List[str]:
        if self.index_file.is_file():
            try:
                data = json.loads(self.index_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return [
                        item["slug"] for item in data
                        if isinstance(item, dict)
                        and isinstance(item.get("slug"), str)
                        and SLUG_PATTERN.fullmatch(item["slug"])
                    ]
                warnings.warn(f"Ignoring malformed corpus index (expected a list): {self.index_file}", RuntimeWarning)
            except (OSError, json.JSONDecodeError) as exc:
                warnings.warn(f"Could not read corpus index {self.index_file}: {exc}; scanning task folders instead.", RuntimeWarning)

        if self.tasks_dir.is_dir():
            return sorted(
                path.name for path in self.tasks_dir.iterdir()
                if path.is_dir() and SLUG_PATTERN.fullmatch(path.name)
            )
        return []

    def load_problem(self, slug: str) -> Optional[RawProblemData]:
        if not SLUG_PATTERN.fullmatch(slug):
            raise ValueError("Invalid problem slug. Use letters, digits, underscores, and hyphens only.")

        task_dir = (self.tasks_dir / slug).resolve()
        if not task_dir.is_relative_to(self.tasks_dir.resolve()) or not task_dir.is_dir():
            return None

        stmt_file = task_dir / "statement.md"
        prob_file = task_dir / "problem.json"
        if not stmt_file.is_file():
            return None

        statement_md = stmt_file.read_text(encoding="utf-8")
        title = slug.replace("_", " ").replace("-", " ").title()
        time_lim, mem_lim, difficulty = "1000 ms", "256 MB", "UNKNOWN"
        url = f"https://csacademy.com/contest/archive/task/{slug}/"
        extra = {}

        if prob_file.is_file():
            try:
                meta = json.loads(prob_file.read_text(encoding="utf-8"))
                if isinstance(meta, dict):
                    title = meta.get("title", title)
                    time_lim = meta.get("time_limit", time_lim)
                    mem_lim = meta.get("memory_limit", mem_lim)
                    difficulty = meta.get("difficulty") or "UNKNOWN"
                    url = meta.get("url", url)
                    extra = meta
                else:
                    warnings.warn(f"Ignoring non-object metadata in {prob_file}", RuntimeWarning)
            except (OSError, json.JSONDecodeError) as exc:
                warnings.warn(f"Could not read optional metadata {prob_file}: {exc}; using defaults.", RuntimeWarning)

        return RawProblemData(
            slug=slug, title=title, statement_markdown=statement_md,
            time_limit_str=str(time_lim), memory_limit_str=str(mem_lim),
            difficulty=str(difficulty), platform="csacademy",
            source_url=str(url) if url else None, extra_metadata=extra,
        )
