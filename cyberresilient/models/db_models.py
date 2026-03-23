"""
SQLAlchemy ORM models for CyberResilient data persistence.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from cyberresilient.database import Base


# ── Risk Register ───────────────────────────────────────────
class RiskRow(Base):
    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    likelihood: Mapped[int] = mapped_column(Integer)
    impact: Mapped[int] = mapped_column(Integer)
    risk_score: Mapped[int] = mapped_column(Integer)
    residual_score: Mapped[float] = mapped_column(Float, nullable=True)
    mitigation_effectiveness: Mapped[str] = mapped_column(String(20), default="None")
    evidence_date: Mapped[str] = mapped_column(String(20), default="")
    sign_off_by: Mapped[str] = mapped_column(String(100), default="")
    owner: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    mitigation: Mapped[str] = mapped_column(Text)
    asset: Mapped[str] = mapped_column(String(200))
    target_date: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "residual_score": self.residual_score,
            "mitigation_effectiveness": self.mitigation_effectiveness or "None",
            "evidence_date": self.evidence_date or "",
            "sign_off_by": self.sign_off_by or "",
            "owner": self.owner,
            "status": self.status,
            "mitigation": self.mitigation,
            "asset": self.asset,
            "target_date": self.target_date,
            "notes": self.notes,
        }


# ── Systems ─────────────────────────────────────────────────
class SystemRow(Base):
    __tablename__ = "systems"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    department: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    hosting: Mapped[str] = mapped_column(String(100), default="")
    tier: Mapped[int] = mapped_column(Integer)
    rto_target_hours: Mapped[float] = mapped_column(Float)
    rpo_target_hours: Mapped[float] = mapped_column(Float)
    current_dr_strategy: Mapped[str] = mapped_column(String(100))
    last_tested: Mapped[str] = mapped_column(String(20), default="")
    test_result: Mapped[str] = mapped_column(String(50), default="")
    dependencies: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "type": self.type,
            "hosting": self.hosting,
            "tier": self.tier,
            "rto_target_hours": self.rto_target_hours,
            "rpo_target_hours": self.rpo_target_hours,
            "current_dr_strategy": self.current_dr_strategy,
            "last_tested": self.last_tested,
            "test_result": self.test_result,
            "dependencies": json.loads(self.dependencies) if self.dependencies else [],
            "description": self.description,
        }


# ── Scenarios ───────────────────────────────────────────────
class ScenarioRow(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    affected_systems: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    impact_json: Mapped[str] = mapped_column(Text, default="{}")  # JSON object
    recovery_steps: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    rto_impact_multiplier: Mapped[float] = mapped_column(Float)
    rpo_impact_multiplier: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "affected_systems": json.loads(self.affected_systems) if self.affected_systems else [],
            "impact": json.loads(self.impact_json) if self.impact_json else {},
            "recovery_steps": json.loads(self.recovery_steps) if self.recovery_steps else [],
            "rto_impact_multiplier": self.rto_impact_multiplier,
            "rpo_impact_multiplier": self.rpo_impact_multiplier,
        }


# ── Policies ────────────────────────────────────────────────
class PolicyRow(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    owner: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50))
    last_reviewed: Mapped[str] = mapped_column(String(20))
    next_review: Mapped[str] = mapped_column(String(20))
    approved_by: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    review_alert_sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "version": self.version,
            "status": self.status,
            "last_reviewed": self.last_reviewed,
            "next_review": self.next_review,
            "approved_by": self.approved_by,
            "description": self.description,
            "review_alert_sent": bool(self.review_alert_sent),
        }


# ── KPI Metrics ─────────────────────────────────────────────
class KPIMetricRow(Base):
    __tablename__ = "kpi_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    trend: Mapped[str] = mapped_column(String(20), default="")
    lower_is_better: Mapped[int] = mapped_column(Integer, default=0)  # boolean as int
    snapshot_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "trend": self.trend,
            "lower_is_better": bool(self.lower_is_better),
        }


# ── Monthly Incidents ───────────────────────────────────────
class MonthlyIncidentRow(Base):
    __tablename__ = "monthly_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(10))
    count: Mapped[int] = mapped_column(Integer)
    critical: Mapped[int] = mapped_column(Integer, default=0)

    def to_dict(self) -> dict:
        return {"month": self.month, "count": self.count, "critical": self.critical}


# ── Audit Log ───────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user: Mapped[str] = mapped_column(String(100), default="system")
    action: Mapped[str] = mapped_column(String(50))  # CREATE, UPDATE, DELETE, LOGIN, SEED
    entity_type: Mapped[str] = mapped_column(String(50))  # risk, system, scenario, policy, etc.
    entity_id: Mapped[str] = mapped_column(String(50), default="")
    before_json: Mapped[str] = mapped_column(Text, default="")
    after_json: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "user": self.user,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
        }


# ── DR Simulation History ──────────────────────────────────
class SimulationHistoryRow(Base):
    __tablename__ = "simulation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user: Mapped[str] = mapped_column(String(100), default="system")
    system_id: Mapped[str] = mapped_column(String(20))
    system_name: Mapped[str] = mapped_column(String(200))
    scenario_name: Mapped[str] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(20))
    rto_target: Mapped[float] = mapped_column(Float)
    rto_estimated: Mapped[float] = mapped_column(Float)
    rto_met: Mapped[int] = mapped_column(Integer)  # boolean as int
    rpo_target: Mapped[float] = mapped_column(Float)
    rpo_estimated: Mapped[float] = mapped_column(Float)
    rpo_met: Mapped[int] = mapped_column(Integer)  # boolean as int
    overall_pass: Mapped[int] = mapped_column(Integer)  # boolean as int
    dr_strategy: Mapped[str] = mapped_column(String(100), default="")
    result_json: Mapped[str] = mapped_column(Text, default="{}")  # full result

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "user": self.user,
            "system_id": self.system_id,
            "system_name": self.system_name,
            "scenario_name": self.scenario_name,
            "severity": self.severity,
            "rto_target": self.rto_target,
            "rto_estimated": self.rto_estimated,
            "rto_met": bool(self.rto_met),
            "rpo_target": self.rpo_target,
            "rpo_estimated": self.rpo_estimated,
            "rpo_met": bool(self.rpo_met),
            "overall_pass": bool(self.overall_pass),
            "dr_strategy": self.dr_strategy,
            "result": json.loads(self.result_json) if self.result_json else {},
        }


# ── Users (for auth) ───────────────────────────────────────
class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), default="")
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="student")  # admin, analyst, auditor, student
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": bool(self.is_active),
        }
