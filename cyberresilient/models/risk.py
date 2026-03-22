"""
Risk data models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

LIKELIHOOD_LABELS: dict[int, str] = {
    1: "Rare",
    2: "Unlikely",
    3: "Possible",
    4: "Likely",
    5: "Almost Certain",
}

IMPACT_LABELS: dict[int, str] = {
    1: "Negligible",
    2: "Minor",
    3: "Moderate",
    4: "Major",
    5: "Catastrophic",
}

RISK_LEVEL_RANGES: list[tuple[int, int, str]] = [
    (1, 4, "Low"),
    (5, 9, "Medium"),
    (10, 15, "High"),
    (16, 25, "Very High"),
]

RISK_LEVEL_COLORS: dict[str, str] = {
    "Low": "#4CAF50",
    "Medium": "#FFC107",
    "High": "#FF9800",
    "Very High": "#F44336",
}


class Risk(BaseModel):
    id: str
    title: str
    category: str
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    risk_score: int = Field(ge=1, le=25)
    owner: str
    status: str  # Open, Mitigating, Monitoring, Closed
    mitigation: str
    asset: str
    target_date: str
    notes: str = ""


class ArchitectureCheck(BaseModel):
    id: str
    control: str
    framework: str
    question: str
    risk_if_missing: str
    recommendation: str


def get_risk_level(score: int) -> str:
    for lo, hi, level in RISK_LEVEL_RANGES:
        if lo <= score <= hi:
            return level
    return "Unknown"


def get_risk_color(score: int) -> str:
    return RISK_LEVEL_COLORS.get(get_risk_level(score), "#9E9E9E")
