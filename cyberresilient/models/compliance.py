"""
Compliance and policy data models.
"""

from __future__ import annotations

from pydantic import BaseModel

STATUS_WEIGHTS: dict[str, float] = {
    "Implemented": 1.0,
    "Partial": 0.5,
    "Gap": 0.0,
    "Not Implemented": 0.0,
}


class NISTCategory(BaseModel):
    name: str
    status: str  # Implemented, Partial, Gap
    evidence: str = ""


class NISTFunction(BaseModel):
    description: str
    categories: dict[str, NISTCategory]


class ISO27001Domain(BaseModel):
    id: str
    name: str
    total: int
    implemented: int
    partial: int


class Policy(BaseModel):
    id: str
    name: str
    owner: str
    version: str
    status: str  # Current, Under Review, Draft, Expired
    last_review: str
    next_review: str
    description: str = ""


class KPI(BaseModel):
    name: str
    value: float
    unit: str
    trend: str = ""
    trend_value: float = 0.0
    lower_is_better: bool = False
