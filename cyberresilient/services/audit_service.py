"""
Audit logging service.
Records every data mutation with timestamp, user, action, and before/after state.
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from cyberresilient.models.db_models import AuditLog


def log_action(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str = "",
    user: str = "system",
    before: dict | None = None,
    after: dict | None = None,
    details: str = "",
) -> None:
    """Write an audit log entry."""
    entry = AuditLog(
        timestamp=datetime.now(),
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=json.dumps(before) if before else "",
        after_json=json.dumps(after) if after else "",
        details=details,
    )
    session.add(entry)


def get_audit_log(session: Session, *, limit: int = 100, entity_type: str | None = None) -> list[dict]:
    """Retrieve recent audit log entries."""
    query = session.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    return [row.to_dict() for row in query.limit(limit).all()]
