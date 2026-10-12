import json
from pathlib import Path
from typing import List, Optional
from dissector.adapters.base import BaseCorpusAdapter, RawProblemData

DEFAULT_ARCHIVE_PATH = Path("F:/Aaradhya-Dev-Tamrakar/IEEE-Xtreme-Archive")


class IEEEXtremeAdapter(BaseCorpusAdapter):
    def __init__(self, root_path: Optional[Path] = None):
        self.root = root_path or DEFAULT_ARCHIVE_PATH
        self.tasks_dir = self.root / "platforms" / "csacademy" / "tasks"
        self.index_file = self.root / "ledger" / "tasks_index.json"

    def list_slugs(self) -> List[str]:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [item["slug"] for item in data if "slug" in item]
            except Exception:
                pass

        if self.tasks_dir.exists():
            return sorted([d.name for d in self.tasks_dir.iterdir() if d.is_dir()])
        return []

    def load_problem(self, slug: str) -> Optional[RawProblemData]:
        task_dir = self.tasks_dir / slug
        if not task_dir.exists():
            return None

        stmt_file = task_dir / "statement.md"
        prob_file = task_dir / "problem.json"

        if not stmt_file.exists():
            return None

        statement_md = stmt_file.read_text(encoding="utf-8")
        title = slug.replace("_", " ").replace("-", " ").title()
        time_lim = "1000 ms"
        mem_lim = "256 MB"
        diff = "UNKNOWN"
        url = f"https://csacademy.com/contest/archive/task/{slug}/"
        extra = {}

        if prob_file.exists():
            try:
                with open(prob_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    title = meta.get("title", title)
                    time_lim = meta.get("time_limit", time_lim)
                    mem_lim = meta.get("memory_limit", mem_lim)
                    diff = meta.get("difficulty") or "UNKNOWN"
                    url = meta.get("url", url)
                    extra = meta
            except Exception:
                pass

        return RawProblemData(
            slug=slug,
            title=title,
            statement_markdown=statement_md,
            time_limit_str=time_lim,
            memory_limit_str=mem_lim,
            difficulty=diff,
            platform="csacademy",
            source_url=url,
            extra_metadata=extra
        )
