"""
cyberresilient/models/db_models.py — Batch 2 additions

Add RiskReviewRow, CAPRow, VendorRow, VendorAssessmentRow to your db_models.py.
Also add last_reviewed_at column to existing RiskRow.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RiskReviewRow(Base):
    __tablename__ = "risk_reviews"

    id = Column(String(36), primary_key=True)
    risk_id = Column(String(16), nullable=False)
    reviewer = Column(String(128), nullable=False)
    outcome = Column(String(32), nullable=False)
    notes = Column(Text, default="")
    residual_score_at_review = Column(Integer, default=0)
    reviewed_at = Column(String(10), nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CAPRow(Base):
    __tablename__ = "corrective_action_plans"

    id = Column(String(36), primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    owner = Column(String(128), nullable=False)
    priority = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False, default="Open")
    target_date = Column(String(10), nullable=False)
    linked_control_id = Column(String(64), default="")
    linked_risk_id = Column(String(16), default="")
    linked_test_id = Column(String(36), default="")
    resolution_notes = Column(Text, default="")
    created_by = Column(String(128), nullable=False)
    created_at = Column(String(10), nullable=False)
    closed_at = Column(String(10), default="")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class VendorRow(Base):
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True)
    name = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False)
    criticality = Column(String(16), nullable=False)
    data_classification = Column(String(64), nullable=False)
    contact_name = Column(String(128), default="")
    contact_email = Column(String(256), default="")
    contract_reference = Column(String(256), default="")
    contract_expiry = Column(String(10), default="")
    notes = Column(Text, default="")
    current_risk_tier = Column(String(32), default="Not Assessed")
    last_assessment_score = Column(Integer, nullable=True)
    last_assessed_at = Column(String(10), default="")
    reassessment_due = Column(String(10), nullable=False)
    created_by = Column(String(128), nullable=False)
    created_at = Column(String(10), nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class VendorAssessmentRow(Base):
    __tablename__ = "vendor_assessments"

    id = Column(String(36), primary_key=True)
    vendor_id = Column(String(36), nullable=False)
    score_pct = Column(Integer, nullable=False)
    risk_tier = Column(String(32), nullable=False)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    assessed_by = Column(String(128), nullable=False)
    assessed_at = Column(String(10), nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
