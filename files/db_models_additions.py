"""
db_models.py additions — paste these new columns into your existing RiskRow
and PolicyRow classes. Shown as a complete RiskRow for clarity.
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RiskRow(Base):
    __tablename__ = "risks"

    id = Column(String(16), primary_key=True)
    title = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False)
    likelihood = Column(Integer, nullable=False)
    impact = Column(Integer, nullable=False)

    # --- existing ---
    risk_score = Column(Integer, nullable=False)  # inherent score

    # --- new: residual risk ---
    residual_score = Column(Integer, nullable=False, default=0)
    mitigation_effectiveness = Column(String(32), nullable=False, default="None")

    # --- new: evidence & sign-off ---
    evidence_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    sign_off_by = Column(String(128), nullable=False, default="")

    # --- existing ---
    owner = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    mitigation = Column(Text, default="")
    asset = Column(String(256), default="")
    target_date = Column(String(10), default="")
    notes = Column(Text, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "residual_score": self.residual_score,
            "mitigation_effectiveness": self.mitigation_effectiveness,
            "evidence_date": self.evidence_date,
            "sign_off_by": self.sign_off_by,
            "owner": self.owner,
            "status": self.status,
            "mitigation": self.mitigation,
            "asset": self.asset,
            "target_date": self.target_date,
            "notes": self.notes,
        }


class PolicyRow(Base):
    __tablename__ = "policies"

    id = Column(String(16), primary_key=True)
    title = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False)
    owner = Column(String(128), nullable=False)

    # --- new: expiry proximity alert ---
    review_date = Column(String(10), nullable=True)  # YYYY-MM-DD

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "review_date": self.review_date,
        }
