"""
Import/Export service — JSON and CSV support.
"""

from __future__ import annotations

import csv
import io
import json

from sqlalchemy.orm import Session

from cyberresilient.models.db_models import (
    KPIMetricRow,
    MonthlyIncidentRow,
    PolicyRow,
    RiskRow,
    ScenarioRow,
    SystemRow,
)

_MODEL_MAP: dict[str, type] = {
    "risks": RiskRow,
    "systems": SystemRow,
    "scenarios": ScenarioRow,
    "policies": PolicyRow,
    "kpi_metrics": KPIMetricRow,
    "monthly_incidents": MonthlyIncidentRow,
}


def export_json(session: Session, entity_type: str) -> str:
    """Export all rows of a given entity type as a JSON string."""
    model = _MODEL_MAP.get(entity_type)
    if not model:
        msg = f"Unknown entity type: {entity_type}"
        raise ValueError(msg)
    rows = session.query(model).all()
    return json.dumps([r.to_dict() for r in rows], indent=2, default=str)


def export_csv(session: Session, entity_type: str) -> str:
    """Export all rows of a given entity type as a CSV string."""
    model = _MODEL_MAP.get(entity_type)
    if not model:
        msg = f"Unknown entity type: {entity_type}"
        raise ValueError(msg)
    rows = session.query(model).all()
    if not rows:
        return ""

    dicts = [r.to_dict() for r in rows]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=dicts[0].keys())
    writer.writeheader()
    for d in dicts:
        # Flatten lists/dicts for CSV
        flat = {}
        for k, v in d.items():
            flat[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
        writer.writerow(flat)
    return output.getvalue()


def import_json(session: Session, entity_type: str, json_str: str) -> int:
    """Import records from a JSON string. Returns count of imported records."""
    model = _MODEL_MAP.get(entity_type)
    if not model:
        msg = f"Unknown entity type: {entity_type}"
        raise ValueError(msg)

    data = json.loads(json_str)
    if not isinstance(data, list):
        data = [data]

    count = 0
    for record in data:
        # Check for existing record (by id if present)
        if hasattr(model, "id") and "id" in record:
            existing = session.get(model, record["id"])
            if existing:
                for key, val in record.items():
                    if hasattr(existing, key):
                        setattr(existing, key, val)
                count += 1
                continue
        session.add(model(**record))
        count += 1

    return count


def get_exportable_types() -> list[str]:
    return list(_MODEL_MAP.keys())
