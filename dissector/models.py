"""Typed output models for reports and downstream contracts."""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DifficultyTier(str, Enum):
    TUTORIAL = "TUTORIAL"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class ComplexityTarget(BaseModel):
    max_operations: int = Field(description="Nominal operation budget heuristic; not a runtime guarantee")
    admissible_time_complexity: str = Field(description="Heuristic complexity ceiling, not a proven algorithm requirement")
    admissible_space_complexity: str = Field(description="Rough memory guidance, not a proven space requirement")
    explanation: str
    estimated_operations_by_candidate: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ParsedConstraints(BaseModel):
    variables: Dict[str, float] = Field(default_factory=dict, description="Best-effort upper bounds, e.g. N: 100000")
    raw_constraints: List[str] = Field(default_factory=list)
    time_limit_ms: int = 1000
    memory_limit_mb: int = 256
    target_complexity: Optional[ComplexityTarget] = None
    warnings: List[str] = Field(default_factory=list)


class ArchetypeMatch(BaseModel):
    archetype_id: str
    name: str
    confidence: float = Field(description="Legacy numeric keyword-match score; not a calibrated probability")
    score_semantics: str = Field(
        default="heuristic_keyword_match_not_probability",
        description="Keyword evidence score, not a probability",
    )
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
