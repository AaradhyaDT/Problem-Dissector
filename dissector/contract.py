from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AsymptoticCeiling(BaseModel):
    time_complexity: str = Field(..., description="Mandated maximum Big-O time bound, e.g. O(N log N)")
    space_complexity: str = Field(..., description="Mandated maximum Big-O auxiliary space bound, e.g. O(N)")
    ops_budget: int = Field(..., description="Estimated safe operation count ceiling (e.g. 1e8 for 1s)")
    dominant_dimension: str = Field(..., description="Variable driving the complexity (e.g. N = 100000)")


class ImplementationGuidelines(BaseModel):
    recommended_language: str = "C++20"
    data_structures: List[str] = Field(default_factory=list)
    fast_io_required: bool = True
    overflow_risk: bool = False
    integer_types: str = "int (32-bit)"


class AgentDissectionContract(BaseModel):
    """
    Standardized, high-density cognitive contract specifically formulated
    for consumption by downstream coding agents (Fleet workers, Copilot, LLMs).
    """
    version: str = "1.0.0"
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
    agent_prompt_summary: str = Field(..., description="Concise, laser-focused instruction directive for the agent")
