"""Stable, typed payload for downstream coding agents."""
from typing import List

from pydantic import BaseModel, Field


class AsymptoticCeiling(BaseModel):
    time_complexity: str = Field(..., description="Heuristic ceiling, not a mandated or proven Big-O bound")
    space_complexity: str = Field(..., description="Rough memory guidance; validate with the real representation")
    ops_budget: int = Field(..., description="Nominal rule-of-thumb budget, not a runtime guarantee")
    dominant_dimension: str = Field(..., description="Largest parsed numeric bound used as a proxy, not a full dimensional model")


class ImplementationGuidelines(BaseModel):
    recommended_language: str = "C++20"
    data_structures: List[str] = Field(default_factory=list)
    fast_io_may_help: bool = Field(
        default=False,
        description="I/O optimization may help for large token counts; dimension size alone does not make it mandatory",
    )
    fast_io_required: bool = Field(
        default=False,
        description="Compatibility field: the heuristic cannot prove I/O optimization is mandatory; see fast_io_may_help and analysis caveats",
    )
    overflow_risk: bool = False
    integer_types: str = "Choose integer width from proven input and accumulator bounds"


class AgentDissectionContract(BaseModel):
    """Structured task contract; heuristics must be verified against the full statement."""
    version: str = "1.1.0"
    task_slug: str
    title: str
    platform: str = "csacademy"
    difficulty: str = "UNKNOWN"
    asymptotics: AsymptoticCeiling
    archetype_id: str
    archetype_name: str
    core_invariants: List[str] = Field(default_factory=list)
    forbidden_approaches: List[str] = Field(default_factory=list)
    edge_case_checklist: List[str] = Field(default_factory=list)
    guidelines: ImplementationGuidelines
    analysis_caveats: List[str] = Field(default_factory=list)
    agent_prompt_summary: str = Field(..., description="Instruction preserving uncertainty and verification requirements")
