"""
cyberresilient/services/review_service.py

Risk Review Cadence Enforcement Service.

Every risk has a mandatory review frequency based on its residual level:
  Very High / High  → quarterly  (90 days)
  Medium            → semi-annual (180 days)
  Low               → annual     (365 days)

A review record is created each time a risk is formally reviewed.
Overdue reviews are surfaced on the dashboard and risk register.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Optional

from cyberresilient.models.risk import get_risk_level

REVIEW_INTERVALS: dict[str, int] = {
    "Very High": 90,
    "High":      90,
    "Medium":    180,
    "Low":       365,
}


def review_due_date(risk: dict) -> str:
    """Calculate when a risk's next review is due based on residual level."""
    residual = risk.get("residual_score", risk.get("risk_score", 1))
    level = get_risk_level(residual)
    days = REVIEW_INTERVALS[level]
    last = risk.get("last_reviewed_at") or risk.get("created_at") or date.today().isoformat()
    try:
        base = date.fromisoformat(last[:10])
    except ValueError:
        base = date.today()
    return (base + timedelta(days=days)).isoformat()


def is_review_overdue(risk: dict) -> bool:
    return date.today().isoformat() > review_due_date(risk)


def days_until_review(risk: dict) -> int:
    """Positive = days remaining. Negative = days overdue."""
    due = date.fromisoformat(review_due_date(risk))
    return (due - date.today()).days


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("risk_reviews")
    except Exception:
        return False


def record_review(
    risk_id: str,
    reviewer: str,
    outcome: str,           # "No Change" | "Score Updated" | "Closed" | "Escalated"
    notes: str = "",
    residual_score_at_review: int = 0,
) -> dict:
    """
    Record a formal risk review event.
    Updates last_reviewed_at on the risk row so next due date recalculates.
    """
    if outcome not in ("No Change", "Score Updated", "Closed", "Escalated"):
        raise ValueError(
            f"Invalid outcome '{outcome}'. "
            "Choose: No Change, Score Updated, Closed, Escalated"
        )
    record = {
        "id": str(uuid.uuid4()),
        "risk_id": risk_id,
        "reviewer": reviewer,
        "outcome": outcome,
        "notes": notes,
        "residual_score_at_review": residual_score_at_review,
        "reviewed_at": date.today().isoformat(),
    }
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import RiskReviewRow, RiskRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(RiskReviewRow(**record))
            # Stamp last_reviewed_at on the parent risk
            risk_row = session.query(RiskRow).filter_by(id=risk_id).first()
            if risk_row:
                risk_row.last_reviewed_at = record["reviewed_at"]
            log_action(session, action="record_review",
                       entity_type="risk", entity_id=risk_id,
                       user=reviewer, after=record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return record


def get_review_history(risk_id: str) -> list[dict]:
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskReviewRow
    session = get_session()
    try:
        rows = (
            session.query(RiskReviewRow)
            .filter_by(risk_id=risk_id)
            .order_by(RiskReviewRow.reviewed_at.desc())
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()


def get_overdue_risks(risks: list[dict]) -> list[dict]:
    """Filter a list of risk dicts to those with overdue reviews."""
    overdue = [r for r in risks if is_review_overdue(r)]
    overdue.sort(key=lambda r: days_until_review(r))  # most overdue first
    return overdue


OUTCOME_ICONS = {
    "No Change":     "📋",
    "Score Updated": "📊",
    "Closed":        "✅",
    "Escalated":     "🚨",
}
