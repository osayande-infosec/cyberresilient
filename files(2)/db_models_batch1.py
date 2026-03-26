"""
cyberresilient/models/db_models.py — Batch 1 additions

Add these three classes to your existing db_models.py.
Also add EvidenceArtifactRow, RiskTreatmentRow, ControlTestRow
to your Base.metadata.create_all() call if you use it directly.
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EvidenceArtifactRow(Base):
    __tablename__ = "evidence_artifacts"

    id = Column(String(36), primary_key=True)           # UUID
    entity_type = Column(String(16), nullable=False)    # "risk" | "control"
    entity_id = Column(String(64), nullable=False)
    original_filename = Column(String(256), nullable=False)
    stored_filename = Column(String(256), nullable=False)
    description = Column(Text, default="")
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(String(128), nullable=False)
    uploaded_at = Column(String(10), nullable=False)    # YYYY-MM-DD

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class RiskTreatmentRow(Base):
    __tablename__ = "risk_treatments"

    id = Column(String(36), primary_key=True)           # UUID
    risk_id = Column(String(16), nullable=False)
    treatment_type = Column(String(16), nullable=False) # Mitigate|Accept|Transfer|Avoid
    mitigation_plan = Column(Text, default="")
    target_date = Column(String(10), default="")        # YYYY-MM-DD
    justification = Column(Text, default="")
    sign_off_by = Column(String(128), default="")
    policy_reference = Column(String(256), default="")
    third_party = Column(String(256), default="")
    notes = Column(Text, default="")
    recorded_by = Column(String(128), nullable=False)
    recorded_at = Column(String(10), nullable=False)    # YYYY-MM-DD
    active = Column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ControlTestRow(Base):
    __tablename__ = "control_tests"

    id = Column(String(36), primary_key=True)           # UUID
    control_id = Column(String(64), nullable=False)
    framework = Column(String(32), nullable=False)      # "nist_csf" | "iso27001"
    test_method = Column(String(32), nullable=False)
    result = Column(String(16), nullable=False)         # Pass|Partial|Fail
    result_weight = Column(Float, nullable=False)
    tester = Column(String(128), nullable=False)
    finding = Column(Text, default="")
    corrective_action_id = Column(String(36), default="")
    notes = Column(Text, default="")
    tested_at = Column(String(10), nullable=False)      # YYYY-MM-DD
    retest_due = Column(String(10), nullable=False)     # YYYY-MM-DD

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
