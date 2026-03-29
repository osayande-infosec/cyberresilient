"""
cyberresilient/services/treatment_service.py

Risk Treatment Workflow Service.

Enterprise GRC requires a formal treatment decision for every risk:
  - Accept   : Risk is within appetite or sign-off obtained. Justification memo required.
  - Mitigate : Controls are being implemented. Linked to mitigation plan + target date.
  - Transfer : Risk shifted to third party (insurance, contract). Policy reference required.
  - Avoid    : Activity generating the risk is discontinued. Decision memo required.

Each treatment decision is an immutable record linked to a risk ID.
The most recent decision is the active treatment.
"""

from __future__ import annotations

import uuid
from datetime import date

TREATMENT_OPTIONS = ["Mitigate", "Accept", "Transfer", "Avoid"]

TREATMENT_DESCRIPTIONS = {
    "Mitigate": (
        "Implement or improve controls to reduce likelihood or impact. Requires a mitigation plan and target date."
    ),
    "Accept": (
        "Acknowledge the risk and accept it without further action. "
        "Requires a justification memo and sign-off by an authorised approver. "
        "Only valid when residual score is within appetite OR explicit exception granted."
    ),
    "Transfer": (
        "Shift financial or operational impact to a third party via insurance, "
        "contract, or outsourcing. Requires a policy or contract reference."
    ),
    "Avoid": (
        "Discontinue the activity or system that generates the risk entirely. "
        "Requires a decision memo and executive approval."
    ),
}

# Fields required per treatment type
TREATMENT_REQUIRED_FIELDS: dict[str, list[str]] = {
    "Mitigate": ["mitigation_plan", "target_date"],
    "Accept": ["justification", "sign_off_by"],
    "Transfer": ["policy_reference", "third_party"],
    "Avoid": ["justification", "sign_off_by"],
}


def _db_available() -> bool:
    try:
        from sqlalchemy import inspect

        from cyberresilient.database import get_engine

        return inspect(get_engine()).has_table("risk_treatments")
    except Exception:
        return False


def validate_treatment(treatment_type: str, fields: dict) -> list[str]:
    """
    Validate that all required fields are present for the given treatment type.
    Returns a list of missing field names (empty = valid).
    """
    required = TREATMENT_REQUIRED_FIELDS.get(treatment_type, [])
    return [f for f in required if not (fields.get(f) or "").strip()]


def record_treatment(
    risk_id: str,
    treatment_type: str,
    fields: dict,
    recorded_by: str = "system",
) -> dict:
    """
    Record a formal treatment decision for a risk.

    fields keys (all optional except those required per type):
      mitigation_plan   : str   — Mitigate
      target_date       : str   — Mitigate (YYYY-MM-DD)
      justification     : str   — Accept / Avoid
      sign_off_by       : str   — Accept / Avoid
      policy_reference  : str   — Transfer
      third_party       : str   — Transfer (insurer / vendor name)
      notes             : str   — any

    Raises ValueError if required fields are missing.
    """
    if treatment_type not in TREATMENT_OPTIONS:
        raise ValueError(f"Invalid treatment type '{treatment_type}'. Choose from: {', '.join(TREATMENT_OPTIONS)}")

    missing = validate_treatment(treatment_type, fields)
    if missing:
        raise ValueError(f"Treatment '{treatment_type}' requires: {', '.join(missing)}")

    record = {
        "id": str(uuid.uuid4()),
        "risk_id": risk_id,
        "treatment_type": treatment_type,
        "mitigation_plan": fields.get("mitigation_plan", ""),
        "target_date": fields.get("target_date", ""),
        "justification": fields.get("justification", ""),
        "sign_off_by": fields.get("sign_off_by", ""),
        "policy_reference": fields.get("policy_reference", ""),
        "third_party": fields.get("third_party", ""),
        "notes": fields.get("notes", ""),
        "recorded_by": recorded_by,
        "recorded_at": date.today().isoformat(),
        "active": True,
    }

    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import RiskTreatmentRow
        from cyberresilient.services.audit_service import log_action

        session = get_session()
        try:
            # Deactivate previous treatments for this risk
            session.query(RiskTreatmentRow).filter_by(risk_id=risk_id, active=True).update({"active": False})
            session.add(RiskTreatmentRow(**record))
            log_action(
                session,
                action="record_treatment",
                entity_type="risk",
                entity_id=risk_id,
                user=recorded_by,
                after=record,
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return record


def get_active_treatment(risk_id: str) -> dict | None:
    """Return the current active treatment for a risk, or None."""
    if not _db_available():
        return None
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskTreatmentRow

    session = get_session()
    try:
        row = (
            session.query(RiskTreatmentRow)
            .filter_by(risk_id=risk_id, active=True)
            .order_by(RiskTreatmentRow.recorded_at.desc())
            .first()
        )
        return row.to_dict() if row else None
    finally:
        session.close()


def get_treatment_history(risk_id: str) -> list[dict]:
    """Return full treatment history for a risk, newest first."""
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskTreatmentRow

    session = get_session()
    try:
        rows = (
            session.query(RiskTreatmentRow)
            .filter_by(risk_id=risk_id)
            .order_by(RiskTreatmentRow.recorded_at.desc())
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()


TREATMENT_ICONS = {
    "Mitigate": "🔧",
    "Accept": "✅",
    "Transfer": "🤝",
    "Avoid": "🚫",
}

TREATMENT_COLORS = {
    "Mitigate": "#2196F3",
    "Accept": "#4CAF50",
    "Transfer": "#9C27B0",
    "Avoid": "#FF9800",
}
