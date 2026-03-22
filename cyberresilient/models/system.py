"""
System and DR scenario data models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class System(BaseModel):
    id: str
    name: str
    department: str
    type: str  # IT, OT, Cloud, Provincial Cloud
    tier: int = Field(ge=1, le=3)
    rto_target_hours: float
    rpo_target_hours: float
    current_dr_strategy: str
    dependencies: list[str] = []
    last_test_date: str = ""
    last_test_result: str = ""


class ScenarioImpact(BaseModel):
    departments_affected: list[str]
    public_impact: str
    estimated_citizens_affected: int = 0


class Scenario(BaseModel):
    id: str
    name: str
    type: str
    severity: str  # Critical, High, Medium, Low
    description: str
    rto_impact_multiplier: float
    rpo_impact_multiplier: float
    recovery_steps: list[str]
    impact: ScenarioImpact
    affected_systems: list[str] = []


class SimulationResult(BaseModel):
    system_name: str
    system_id: str
    scenario_name: str
    scenario_type: str
    severity: str
    timestamp: str
    rto_target_hours: float
    rto_estimated_hours: float
    rto_met: bool
    rto_gap_hours: float
    rpo_target_hours: float
    rpo_estimated_hours: float
    rpo_met: bool
    rpo_gap_hours: float
    overall_pass: bool
    dr_strategy: str
    recovery_steps: list[str]
    departments_affected: list[str]
    public_impact: str
    recommendations: list[str]


class RACIEntry(BaseModel):
    activity: str
    responsible: str
    accountable: str
    consulted: str
    informed: str
