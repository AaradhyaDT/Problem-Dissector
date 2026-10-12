from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DifficultyTier(str, Enum):
    TUTORIAL = "TUTORIAL"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class ComplexityTarget(BaseModel):
    max_operations: int
    admissible_time_complexity: str
    admissible_space_complexity: str
    explanation: str


class ParsedConstraints(BaseModel):
    variables: Dict[str, float] = Field(default_factory=dict, description="Variable bounds like N: 100000")
    raw_constraints: List[str] = Field(default_factory=list)
    time_limit_ms: int = 1000
    memory_limit_mb: int = 256
    target_complexity: Optional[ComplexityTarget] = None


class ArchetypeMatch(BaseModel):
    archetype_id: str
    name: str
    confidence: float
    matched_keywords: List[str] = Field(default_factory=list)
    recommended_paradigms: List[str] = Field(default_factory=list)


class EdgeCaseTrap(BaseModel):
    category: str
    description: str
    mitigation: str


class DissectionReport(BaseModel):
    slug: str
    title: str
    platform: str = "csacademy"
    difficulty: DifficultyTier = DifficultyTier.UNKNOWN
    constraints: ParsedConstraints
    archetypes: List[ArchetypeMatch]
    key_observations: List[str] = Field(default_factory=list)
    solution_blueprint: str
    pitfalls_and_traps: List[EdgeCaseTrap] = Field(default_factory=list)
    source_url: Optional[str] = None
