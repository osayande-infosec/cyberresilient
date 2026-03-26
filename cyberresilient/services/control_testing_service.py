"""
cyberresilient/services/control_testing_service.py

Control Testing / Assessment Records Service.

ISO 27001 and NIST CSF require that controls are *tested*, not just stated
as implemented. This service manages a test log per control with:
  - Test method (Interview / Observation / Inspection / Re-performance)
  - Tester identity and date
  - Pass / Fail / Partial result with finding notes
  - Linked corrective action when result is not Pass

Test records are immutable — each assessment creates a new record.
The most recent record determines the control's current test status.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

TEST_METHODS = ["Interview", "Observation", "Inspection", "Re-performance"]
TEST_RESULTS = ["Pass", "Partial", "Fail"]

# How each result maps to an effective compliance contribution
RESULT_WEIGHTS = {
    "Pass":    1.0,
    "Partial": 0.5,
    "Fail":    0.0,
}

# Controls tested by each method need re-testing after N days
RETEST_INTERVALS: dict[str, int] = {
    "Interview":      365,
    "Observation":    365,
    "Inspection":     180,
    "Re-performance": 180,
}


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("control_tests")
    except Exception:
        return False


def record_test(
    control_id: str,
    framework: str,             # "nist_csf" | "iso27001"
    test_method: str,
    result: str,
    tester: str,
    finding: str = "",
    corrective_action_id: Optional[str] = None,
    notes: str = "",
) -> dict:
    """
    Record a control test result.

    Raises ValueError for invalid method or result values.
    A Fail result without a finding note raises ValueError —
    auditors need to know what failed.
    """
    if test_method not in TEST_METHODS:
        raise ValueError(
            f"Invalid test method '{test_method}'. "
            f"Choose from: {', '.join(TEST_METHODS)}"
        )
    if result not in TEST_RESULTS:
        raise ValueError(
            f"Invalid result '{result}'. Choose from: {', '.join(TEST_RESULTS)}"
        )
    if result == "Fail" and not finding.strip():
        raise ValueError(
            "A finding note is required when result is Fail. "
            "Describe what the test revealed."
        )

    record = {
        "id": str(uuid.uuid4()),
        "control_id": control_id,
        "framework": framework,
        "test_method": test_method,
        "result": result,
        "result_weight": RESULT_WEIGHTS[result],
        "tester": tester,
        "finding": finding,
        "corrective_action_id": corrective_action_id or "",
        "notes": notes,
        "tested_at": date.today().isoformat(),
        "retest_due": _retest_due(test_method),
    }

    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import ControlTestRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(ControlTestRow(**record))
            log_action(session, action="record_control_test",
                       entity_type="control", entity_id=control_id,
                       user=tester, after=record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return record


def _retest_due(method: str) -> str:
    from datetime import timedelta
    days = RETEST_INTERVALS.get(method, 365)
    return (date.today() + timedelta(days=days)).isoformat()


def get_latest_test(control_id: str) -> Optional[dict]:
    """Return the most recent test record for a control."""
    return next(iter(get_test_history(control_id)), None)


def get_test_history(control_id: str) -> list[dict]:
    """Return all test records for a control, newest first."""
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import ControlTestRow
    session = get_session()
    try:
        rows = (
            session.query(ControlTestRow)
            .filter_by(control_id=control_id)
            .order_by(ControlTestRow.tested_at.desc())
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        session.close()


def is_retest_overdue(control_id: str) -> bool:
    """Return True if the control's retest due date has passed."""
    latest = get_latest_test(control_id)
    if not latest:
        return True
    retest_due = latest.get("retest_due")
    if not retest_due:
        return True
    return date.today().isoformat() > retest_due


def get_overdue_controls(framework: str) -> list[dict]:
    """Return all controls for a framework whose retest is overdue."""
    if not _db_available():
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import ControlTestRow
    session = get_session()
    try:
        today = date.today().isoformat()
        rows = (
            session.query(ControlTestRow)
            .filter(
                ControlTestRow.framework == framework,
                ControlTestRow.retest_due < today,
            )
            .order_by(ControlTestRow.retest_due.asc())
            .all()
        )
        seen = set()
        overdue = []
        for r in rows:
            if r.control_id not in seen:
                seen.add(r.control_id)
                overdue.append(r.to_dict())
        return overdue
    finally:
        session.close()


def test_summary(framework: str) -> dict:
    """Return a summary of test coverage and results for a framework."""
    if not _db_available():
        return {"tested": 0, "passed": 0, "partial": 0, "failed": 0, "untested": 0}
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import ControlTestRow
    session = get_session()
    try:
        rows = session.query(ControlTestRow).filter_by(framework=framework).all()
        latest: dict[str, dict] = {}
        for r in rows:
            d = r.to_dict()
            if d["control_id"] not in latest or d["tested_at"] > latest[d["control_id"]]["tested_at"]:
                latest[d["control_id"]] = d
        results = [v["result"] for v in latest.values()]
        return {
            "tested": len(results),
            "passed": results.count("Pass"),
            "partial": results.count("Partial"),
            "failed": results.count("Fail"),
        }
    finally:
        session.close()


RESULT_ICONS = {"Pass": "✅", "Partial": "⚠️", "Fail": "❌"}
RESULT_COLORS = {"Pass": "#4CAF50", "Partial": "#FFC107", "Fail": "#F44336"}
METHOD_ICONS = {
    "Interview": "💬",
    "Observation": "👁️",
    "Inspection": "📄",
    "Re-performance": "🔁",
}
