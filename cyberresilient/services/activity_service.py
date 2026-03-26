"""
cyberresilient/services/activity_service.py

User Activity Reporting Service.

Generates 90-day activity summaries from the audit log.
Auditors want: who did what, when, and how often — not raw log entries.

Produces:
  - Per-user action counts and last-seen timestamps
  - Action type breakdown (create/update/delete/login)
  - Entity-level change frequency (which risks/controls changed most)
  - Exportable report dict for PDF/PPTX generation
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional


REPORT_WINDOW_DAYS = 90


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("audit_log")
    except Exception:
        return False


def _load_raw_logs(days: int = REPORT_WINDOW_DAYS) -> list[dict]:
    """Pull audit log entries from the last N days."""
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import AuditLog
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    session = get_session()
    try:
        rows = (
            session.query(AuditLog)
            .filter(AuditLog.timestamp >= cutoff)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()


def generate_activity_report(days: int = REPORT_WINDOW_DAYS) -> dict:
    """
    Generate a structured activity summary for the given window.

    Returns:
      {
        "window_days": 90,
        "from_date": "YYYY-MM-DD",
        "to_date": "YYYY-MM-DD",
        "total_actions": int,
        "by_user": [ {user, actions, last_seen, action_breakdown} ],
        "by_action_type": {create: N, update: N, delete: N, ...},
        "by_entity_type": {risk: N, control: N, cap: N, ...},
        "most_changed_entities": [ {entity_type, entity_id, change_count} ],
        "daily_activity": [ {date, count} ],
      }
    """
    logs = _load_raw_logs(days)
    today = date.today()
    from_date = (today - timedelta(days=days)).isoformat()

    by_user: dict[str, dict] = defaultdict(lambda: {
        "actions": 0, "last_seen": "", "action_breakdown": defaultdict(int)
    })
    by_action: dict[str, int] = defaultdict(int)
    by_entity: dict[str, int] = defaultdict(int)
    entity_changes: dict[tuple, int] = defaultdict(int)
    daily: dict[str, int] = defaultdict(int)

    for log in logs:
        user = log.get("user", "unknown")
        action = log.get("action", "unknown")
        entity_type = log.get("entity_type", "unknown")
        entity_id = log.get("entity_id", "")
        ts = log.get("timestamp", "")[:10]

        by_user[user]["actions"] += 1
        by_user[user]["action_breakdown"][action] += 1
        if ts > by_user[user]["last_seen"]:
            by_user[user]["last_seen"] = ts

        by_action[action] += 1
        by_entity[entity_type] += 1
        entity_changes[(entity_type, entity_id)] += 1
        daily[ts] += 1

    # Most changed entities — top 10
    most_changed = sorted(
        [
            {"entity_type": k[0], "entity_id": k[1], "change_count": v}
            for k, v in entity_changes.items()
        ],
        key=lambda x: x["change_count"],
        reverse=True,
    )[:10]

    # Daily activity — fill zeros for days with no activity
    daily_series = []
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()
        daily_series.append({"date": d, "count": daily.get(d, 0)})

    # Flatten by_user
    user_list = sorted(
        [
            {
                "user": u,
                "actions": v["actions"],
                "last_seen": v["last_seen"],
                "action_breakdown": dict(v["action_breakdown"]),
            }
            for u, v in by_user.items()
        ],
        key=lambda x: x["actions"],
        reverse=True,
    )

    return {
        "window_days": days,
        "from_date": from_date,
        "to_date": today.isoformat(),
        "total_actions": len(logs),
        "unique_users": len(by_user),
        "by_user": user_list,
        "by_action_type": dict(by_action),
        "by_entity_type": dict(by_entity),
        "most_changed_entities": most_changed,
        "daily_activity": daily_series,
    }


def get_recent_actions(limit: int = 50) -> list[dict]:
    """Return the N most recent audit log entries for live display."""
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import AuditLog
    session = get_session()
    try:
        rows = (
            session.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()
