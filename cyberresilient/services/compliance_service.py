"""
Compliance scoring service.
Calculates compliance percentages from NIST CSF and ISO 27001 data.
"""

from __future__ import annotations

import json

from cyberresilient.config import DATA_DIR
from cyberresilient.models.compliance import STATUS_WEIGHTS


def _db_available(table: str) -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table(table)
    except Exception:
        return False


def load_controls() -> dict:
    with open(DATA_DIR / "controls_nist_csf.json", encoding="utf-8") as f:
        return json.load(f)


def load_policies() -> list[dict]:
    if _db_available("policies"):
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import PolicyRow
        session = get_session()
        try:
            rows = session.query(PolicyRow).all()
            if rows:
                return [r.to_dict() for r in rows]
        finally:
            session.close()
    with open(DATA_DIR / "policies.json", encoding="utf-8") as f:
        return json.load(f)


def calc_nist_csf_scores(data: dict) -> dict:
    """Calculate per-function and overall NIST CSF compliance."""
    functions = data["nist_csf"]["functions"]
    scores = {}
    total_score = 0.0
    total_controls = 0

    for func_name, func_data in functions.items():
        categories = func_data["categories"]
        func_total = len(categories)
        func_score = sum(STATUS_WEIGHTS.get(cat["status"], 0) for cat in categories.values())
        pct = round((func_score / func_total) * 100) if func_total > 0 else 0
        scores[func_name] = {
            "description": func_data["description"],
            "total_categories": func_total,
            "score": round(func_score, 1),
            "percentage": pct,
            "categories": dict(categories.items()),
        }
        total_score += func_score
        total_controls += func_total

    overall_pct = round((total_score / total_controls) * 100) if total_controls > 0 else 0
    return {"functions": scores, "overall_percentage": overall_pct, "total_controls": total_controls}


def calc_iso27001_scores(data: dict) -> dict:
    """Calculate ISO 27001 Annex A compliance percentages."""
    domains = data["iso27001"]["domains"]
    results = []
    total_controls = 0
    total_implemented = 0
    total_partial = 0

    for d in domains:
        t = d["total"]
        imp = d["implemented"]
        par = d["partial"]
        score = imp + (par * 0.5)
        pct = round((score / t) * 100) if t > 0 else 0
        results.append({**d, "score": round(score, 1), "percentage": pct})
        total_controls += t
        total_implemented += imp
        total_partial += par

    overall = total_implemented + (total_partial * 0.5)
    overall_pct = round((overall / total_controls) * 100) if total_controls > 0 else 0
    return {"domains": results, "overall_percentage": overall_pct, "total_controls": total_controls}


def get_policy_summary(policies: list[dict]) -> dict:
    """Summarise policy lifecycle status."""
    summary: dict[str, int] = {"Current": 0, "Under Review": 0, "Draft": 0, "Expired": 0}
    for p in policies:
        status = p.get("status", "Unknown")
        summary[status] = summary.get(status, 0) + 1
    return {
        "total": len(policies),
        "by_status": summary,
        "current_pct": round((summary.get("Current", 0) / len(policies)) * 100) if policies else 0,
    }
