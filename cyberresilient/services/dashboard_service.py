"""
Dashboard data service.
Loads KPI/dashboard data from database with JSON fallback.
"""

from __future__ import annotations

import json

from cyberresilient.config import DATA_DIR


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("kpi_metrics")
    except Exception:
        return False


def _load_json() -> dict:
    with open(DATA_DIR / "kpi_data.json", encoding="utf-8") as f:
        return json.load(f)


def load_dashboard_data() -> dict:
    """Load dashboard data, merging DB KPI/incident data with JSON for remaining fields."""
    json_data = _load_json()

    if not _db_available():
        return json_data

    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import KPIMetricRow, MonthlyIncidentRow

    session = get_session()
    try:
        kpi_rows = session.query(KPIMetricRow).all()
        incident_rows = session.query(MonthlyIncidentRow).all()

        if kpi_rows:
            json_data["kpi_metrics"] = [r.to_dict() for r in kpi_rows]
        if incident_rows:
            json_data["monthly_incidents"] = [r.to_dict() for r in incident_rows]
    finally:
        session.close()

    return json_data
