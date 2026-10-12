"""Adapter interface for loading problems from external repositories/datasets."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RawProblemData(BaseModel):
    slug: str
    title: str
    statement_markdown: str
    time_limit_str: str = "1000 ms"
    memory_limit_str: str = "256 MB"
    difficulty: str = "UNKNOWN"
    platform: str = "csacademy"
    source_url: Optional[str] = None
    extra_metadata: Dict[str, Any] = {}


class BaseCorpusAdapter(ABC):
    @abstractmethod
    def list_slugs(self) -> List[str]:
        """List all available problem slugs in the corpus."""
        pass

    @abstractmethod
    def load_problem(self, slug: str) -> Optional[RawProblemData]:
        """Load full problem statement and limits by slug."""
        pass
