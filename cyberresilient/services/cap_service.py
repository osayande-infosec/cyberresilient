"""
cyberresilient/services/cap_service.py

Corrective Action Plan (CAP) Service.

When a control fails a test or a compliance gap is identified, a CAP is
raised. CAPs are distinct from risk mitigations — they are tied to a
specific control failure event, not a risk entry.

CAP lifecycle:
  Open → In Progress → Pending Verification → Closed | Overdue (auto-flag)
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

CAP_STATUSES = ["Open", "In Progress", "Pending Verification", "Closed"]
CAP_PRIORITIES = ["Critical", "High", "Medium", "Low"]

# Maps control test result to default CAP priority
RESULT_TO_PRIORITY = {
    "Fail":    "High",
    "Partial": "Medium",
}


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("corrective_action_plans")
    except Exception:
        return False


def create_cap(
    title: str,
    description: str,
    owner: str,
    target_date: str,           # YYYY-MM-DD
    priority: str = "High",
    linked_control_id: str = "",
    linked_risk_id: str = "",
    linked_test_id: str = "",   # control_test.id that triggered this CAP
    created_by: str = "system",
) -> dict:
    """
    Create a new Corrective Action Plan.

    At least one of linked_control_id or linked_risk_id must be provided
    so the CAP is traceable to a specific finding.
    """
    if not linked_control_id and not linked_risk_id:
        raise ValueError(
            "A CAP must be linked to a control ID or a risk ID."
        )
    if priority not in CAP_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Choose from: {', '.join(CAP_PRIORITIES)}"
        )

    record = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "owner": owner,
        "priority": priority,
        "status": "Open",
        "target_date": target_date,
        "linked_control_id": linked_control_id,
        "linked_risk_id": linked_risk_id,
        "linked_test_id": linked_test_id,
        "resolution_notes": "",
        "created_by": created_by,
        "created_at": date.today().isoformat(),
        "closed_at": "",
    }

    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import CAPRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(CAPRow(**record))
            log_action(session, action="create_cap",
                       entity_type="cap", entity_id=record["id"],
                       user=created_by, after=record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return record


def update_cap_status(
    cap_id: str,
    new_status: str,
    resolution_notes: str = "",
    updated_by: str = "system",
) -> dict:
    if new_status not in CAP_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'.")
    if new_status == "Closed" and not resolution_notes.strip():
        raise ValueError("Resolution notes are required when closing a CAP.")

    if not _db_available():
        raise RuntimeError("Database not available.")

    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import CAPRow
    from cyberresilient.services.audit_service import log_action
    session = get_session()
    try:
        row = session.query(CAPRow).filter_by(id=cap_id).first()
        if not row:
            raise ValueError(f"CAP {cap_id} not found.")
        before = row.to_dict()
        row.status = new_status
        if resolution_notes:
            row.resolution_notes = resolution_notes
        if new_status == "Closed":
            row.closed_at = date.today().isoformat()
        log_action(session, action="update_cap",
                   entity_type="cap", entity_id=cap_id,
                   user=updated_by, before=before, after=row.to_dict())
        session.commit()
        return row.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def load_caps(
    status_filter: Optional[list[str]] = None,
    linked_control_id: str = "",
    linked_risk_id: str = "",
) -> list[dict]:
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import CAPRow
    session = get_session()
    try:
        q = session.query(CAPRow)
        if status_filter:
            q = q.filter(CAPRow.status.in_(status_filter))
        if linked_control_id:
            q = q.filter_by(linked_control_id=linked_control_id)
        if linked_risk_id:
            q = q.filter_by(linked_risk_id=linked_risk_id)
        return [r.to_dict() for r in q.order_by(CAPRow.target_date.asc()).all()]
    finally:
        session.close()


def cap_summary() -> dict:
    caps = load_caps()
    today = date.today().isoformat()
    overdue = [
        c for c in caps
        if c["status"] not in ("Closed",) and c["target_date"] < today
    ]
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for c in caps:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
        by_priority[c["priority"]] = by_priority.get(c["priority"], 0) + 1
    return {
        "total": len(caps),
        "overdue": len(overdue),
        "by_status": by_status,
        "by_priority": by_priority,
    }


PRIORITY_COLORS = {
    "Critical": "#B71C1C",
    "High":     "#F44336",
    "Medium":   "#FF9800",
    "Low":      "#4CAF50",
}
STATUS_ICONS = {
    "Open":                 "🔴",
    "In Progress":          "🟡",
    "Pending Verification": "🔵",
    "Closed":               "✅",
}
