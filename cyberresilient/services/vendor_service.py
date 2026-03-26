"""
cyberresilient/services/vendor_service.py

Vendor / Third-Party Risk Registry Service.

Persists vendor assessment results as an ongoing registry with:
  - Vendor profile (name, category, criticality, data classification)
  - Assessment history (architecture assessment scores over time)
  - Current risk tier derived from latest assessment score
  - Re-assessment due date based on criticality
  - Contract and SLA metadata

Re-assessment intervals by criticality:
  Critical  → 6 months
  High      → 12 months
  Medium    → 18 months
  Low       → 24 months
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Optional

VENDOR_CRITICALITIES = ["Critical", "High", "Medium", "Low"]

DATA_CLASSIFICATIONS = [
    "Highly Sensitive (PHI/PII/Financial)",
    "Sensitive (Internal)",
    "Public",
    "None",
]

VENDOR_CATEGORIES = [
    "Cloud / SaaS", "Managed Security", "IT Infrastructure",
    "Professional Services", "Software Vendor", "Hardware",
    "Telecommunications", "Other",
]

REASSESSMENT_INTERVALS: dict[str, int] = {
    "Critical": 180,
    "High":     365,
    "Medium":   547,
    "Low":      730,
}


def _score_to_tier(score_pct: int) -> str:
    if score_pct >= 90:
        return "Low Risk"
    if score_pct >= 70:
        return "Medium Risk"
    if score_pct >= 50:
        return "High Risk"
    return "Critical Risk"


def _reassessment_due(criticality: str, from_date: Optional[str] = None) -> str:
    base = date.fromisoformat(from_date) if from_date else date.today()
    days = REASSESSMENT_INTERVALS.get(criticality, 365)
    return (base + timedelta(days=days)).isoformat()


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("vendors")
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Vendor CRUD
# ---------------------------------------------------------------------------

def create_vendor(
    name: str,
    category: str,
    criticality: str,
    data_classification: str,
    contact_name: str = "",
    contact_email: str = "",
    contract_reference: str = "",
    contract_expiry: str = "",
    notes: str = "",
    created_by: str = "system",
) -> dict:
    record = {
        "id": str(uuid.uuid4()),
        "name": name,
        "category": category,
        "criticality": criticality,
        "data_classification": data_classification,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contract_reference": contract_reference,
        "contract_expiry": contract_expiry,
        "notes": notes,
        "current_risk_tier": "Not Assessed",
        "last_assessment_score": None,
        "last_assessed_at": "",
        "reassessment_due": _reassessment_due(criticality),
        "created_by": created_by,
        "created_at": date.today().isoformat(),
    }
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import VendorRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(VendorRow(**record))
            log_action(session, action="create_vendor",
                       entity_type="vendor", entity_id=record["id"],
                       user=created_by, after=record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return record


def load_vendors() -> list[dict]:
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import VendorRow
    session = get_session()
    try:
        return [r.to_dict() for r in session.query(VendorRow).order_by(VendorRow.name).all()]
    finally:
        session.close()


def get_vendor(vendor_id: str) -> Optional[dict]:
    vendors = load_vendors()
    return next((v for v in vendors if v["id"] == vendor_id), None)


# ---------------------------------------------------------------------------
# Assessment recording
# ---------------------------------------------------------------------------

def record_assessment(
    vendor_id: str,
    score_pct: int,
    assessment_detail: dict,    # full run_architecture_assessment() result
    assessed_by: str = "system",
) -> dict:
    """
    Persist an architecture assessment result against a vendor.
    Updates the vendor's current_risk_tier and reassessment_due.
    """
    record = {
        "id": str(uuid.uuid4()),
        "vendor_id": vendor_id,
        "score_pct": score_pct,
        "risk_tier": _score_to_tier(score_pct),
        "passed": assessment_detail.get("passed", 0),
        "failed": assessment_detail.get("failed", 0),
        "assessed_by": assessed_by,
        "assessed_at": date.today().isoformat(),
    }

    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import VendorAssessmentRow, VendorRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(VendorAssessmentRow(**record))
            # Update vendor's current tier
            vendor_row = session.query(VendorRow).filter_by(id=vendor_id).first()
            if vendor_row:
                vendor_row.current_risk_tier = record["risk_tier"]
                vendor_row.last_assessment_score = score_pct
                vendor_row.last_assessed_at = record["assessed_at"]
                vendor_row.reassessment_due = _reassessment_due(
                    vendor_row.criticality, record["assessed_at"]
                )
            log_action(session, action="record_vendor_assessment",
                       entity_type="vendor", entity_id=vendor_id,
                       user=assessed_by, after=record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return record


def get_assessment_history(vendor_id: str) -> list[dict]:
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import VendorAssessmentRow
    session = get_session()
    try:
        rows = (
            session.query(VendorAssessmentRow)
            .filter_by(vendor_id=vendor_id)
            .order_by(VendorAssessmentRow.assessed_at.desc())
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Overdue and summary
# ---------------------------------------------------------------------------

def get_overdue_vendors() -> list[dict]:
    today = date.today().isoformat()
    return [v for v in load_vendors() if v["reassessment_due"] < today]


def vendor_summary() -> dict:
    vendors = load_vendors()
    today = date.today().isoformat()
    by_tier: dict[str, int] = {}
    by_criticality: dict[str, int] = {}
    overdue = 0
    not_assessed = 0
    for v in vendors:
        by_tier[v["current_risk_tier"]] = by_tier.get(v["current_risk_tier"], 0) + 1
        by_criticality[v["criticality"]] = by_criticality.get(v["criticality"], 0) + 1
        if v["reassessment_due"] < today:
            overdue += 1
        if v["current_risk_tier"] == "Not Assessed":
            not_assessed += 1
    return {
        "total": len(vendors),
        "overdue_assessment": overdue,
        "not_assessed": not_assessed,
        "by_tier": by_tier,
        "by_criticality": by_criticality,
    }


TIER_COLORS = {
    "Low Risk":      "#4CAF50",
    "Medium Risk":   "#FFC107",
    "High Risk":     "#FF9800",
    "Critical Risk": "#F44336",
    "Not Assessed":  "#888888",
}

CRITICALITY_COLORS = {
    "Critical": "#F44336",
    "High":     "#FF9800",
    "Medium":   "#FFC107",
    "Low":      "#4CAF50",
}
