"""
Compliance scoring service.

Enhancements:
  - Control dependency enforcement (prerequisite controls block dependents)
  - Compensating control recognition (alternative controls satisfy requirements)
  - Evidence expiry tracking per control (staleness detection)
  - Continuous control lifecycle states beyond binary implemented/not-implemented
  - Policy expiry proximity alerts
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Optional

from cyberresilient.config import DATA_DIR
from cyberresilient.models.compliance import STATUS_WEIGHTS

# ---------------------------------------------------------------------------
# Evidence configuration
# ---------------------------------------------------------------------------
EVIDENCE_EXPIRY_DAYS: int = 365

# ---------------------------------------------------------------------------
# Control lifecycle states and their compliance weight
# ---------------------------------------------------------------------------
LIFECYCLE_WEIGHTS: dict[str, float] = {
    "Implemented":       1.0,
    "Compensating":      0.85,
    "Largely":           0.65,
    "Partial":           0.40,
    "Planned":           0.15,
    "Not Implemented":   0.0,
}

# ---------------------------------------------------------------------------
# Control dependency map
# ---------------------------------------------------------------------------
CONTROL_DEPENDENCIES: dict[str, list[str]] = {
    "DE.CM-1": ["PR.AC-5"],
    "DE.CM-7": ["PR.AC-3"],
    "RS.CO-2": ["RS.RP-1"],
    "RC.CO-3": ["RC.RP-1"],
    "PR.DS-5": ["PR.AC-4"],
    "ID.RA-5": ["ID.RA-1", "ID.RA-2"],
}

# ---------------------------------------------------------------------------
# Compensating control map
# ---------------------------------------------------------------------------
COMPENSATING_CONTROLS: dict[str, list[str]] = {
    "PR.AC-1": ["PR.AC-3"],
    "DE.AE-1": ["DE.CM-1"],
    "RS.MI-1": ["RS.MI-2"],
}

# Default lookahead for policy-expiry alerts.
POLICY_ALERT_WINDOW_DAYS: int = 30


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _db_available(table: str) -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table(table)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Evidence expiry
# ---------------------------------------------------------------------------

def is_evidence_stale(evidence_date: Optional[str]) -> bool:
    """Return True if evidence is older than EVIDENCE_EXPIRY_DAYS or unset."""
    if not evidence_date:
        return True
    try:
        collected = datetime.strptime(evidence_date, "%Y-%m-%d").date()
        return (date.today() - collected).days > EVIDENCE_EXPIRY_DAYS
    except ValueError:
        return True


def evidence_expiry_status(evidence_date: Optional[str]) -> dict:
    """Return staleness flag and days remaining / overdue."""
    if not evidence_date:
        return {"stale": True, "days_remaining": None, "days_overdue": None}
    try:
        collected = datetime.strptime(evidence_date, "%Y-%m-%d").date()
        expires_on = collected + timedelta(days=EVIDENCE_EXPIRY_DAYS)
        delta = (expires_on - date.today()).days
        if delta > 0:
            return {"stale": False, "days_remaining": delta, "days_overdue": None}
        return {"stale": True, "days_remaining": None, "days_overdue": abs(delta)}
    except ValueError:
        return {"stale": True, "days_remaining": None, "days_overdue": None}


# ---------------------------------------------------------------------------
# Effective weight calculator
# ---------------------------------------------------------------------------

def _effective_weight(
    control_id: str,
    status: str,
    evidence_date: Optional[str],
    all_categories: dict,
) -> tuple[float, list[str]]:
    """Compute effective compliance weight with four layers."""
    notes: list[str] = []

    # 1. Base weight
    weight = LIFECYCLE_WEIGHTS.get(
        status,
        STATUS_WEIGHTS.get(status, 0.0),
    )

    # 2. Compensating control uplift
    if weight == 0.0:
        compensators = COMPENSATING_CONTROLS.get(control_id, [])
        for comp_id in compensators:
            comp = all_categories.get(comp_id, {})
            comp_status = comp.get("status", "Not Implemented")
            comp_weight = LIFECYCLE_WEIGHTS.get(comp_status, 0.0)
            if comp_weight >= 0.5:
                weight = LIFECYCLE_WEIGHTS["Compensating"]
                notes.append(
                    f"Compensated by {comp_id} ({comp_status}); "
                    f"effective weight {weight:.2f}"
                )
                break

    # 3. Evidence staleness penalty
    if is_evidence_stale(evidence_date) and weight > 0.5:
        exp = evidence_expiry_status(evidence_date)
        if exp["days_overdue"] is not None:
            notes.append(
                f"Evidence overdue by {exp['days_overdue']} days; "
                f"weight capped at 0.50"
            )
        else:
            notes.append("No evidence collected; weight capped at 0.50")
        weight = min(weight, 0.5)

    # 4. Dependency prerequisite cap
    prereqs = CONTROL_DEPENDENCIES.get(control_id, [])
    for prereq_id in prereqs:
        prereq = all_categories.get(prereq_id, {})
        prereq_status = prereq.get("status", "Not Implemented")
        prereq_weight = LIFECYCLE_WEIGHTS.get(prereq_status, 0.0)
        if prereq_weight < LIFECYCLE_WEIGHTS["Partial"]:
            if weight > 0.5:
                notes.append(
                    f"Prerequisite {prereq_id} is '{prereq_status}'; "
                    f"effective weight capped at 0.50"
                )
                weight = min(weight, 0.5)

    return weight, notes


# ---------------------------------------------------------------------------
# NIST CSF scoring
# ---------------------------------------------------------------------------

def calc_nist_csf_scores(data: dict) -> dict:
    """Calculate per-function and overall NIST CSF compliance with four-layer weighting."""
    functions = data["nist_csf"]["functions"]

    all_categories: dict[str, dict] = {}
    for func_data in functions.values():
        for cat_id, cat in func_data["categories"].items():
            all_categories[cat_id] = cat

    scores: dict = {}
    total_score = 0.0
    total_controls = 0
    stale_evidence_count = 0
    dependency_breach_count = 0
    compensating_count = 0

    for func_name, func_data in functions.items():
        categories = func_data["categories"]
        func_total = len(categories)
        func_score = 0.0
        func_control_details = []

        for cat_id, cat in categories.items():
            status = cat.get("status", "Not Implemented")
            evidence_date = cat.get("evidence_date")

            weight, notes = _effective_weight(
                cat_id, status, evidence_date, all_categories
            )

            func_score += weight

            exp = evidence_expiry_status(evidence_date)
            if exp["stale"]:
                stale_evidence_count += 1
            if any("Prerequisite" in n for n in notes):
                dependency_breach_count += 1
            if any("Compensated" in n for n in notes):
                compensating_count += 1

            func_control_details.append({
                "id": cat_id,
                "name": cat.get("name", cat_id),
                "status": status,
                "effective_weight": round(weight, 2),
                "evidence_date": evidence_date,
                "evidence_status": exp,
                "notes": notes,
            })

        pct = round((func_score / func_total) * 100) if func_total > 0 else 0
        scores[func_name] = {
            "description": func_data["description"],
            "total_categories": func_total,
            "score": round(func_score, 1),
            "percentage": pct,
            "categories": dict(categories.items()),
            "control_details": func_control_details,
        }
        total_score += func_score
        total_controls += func_total

    overall_pct = (
        round((total_score / total_controls) * 100) if total_controls > 0 else 0
    )

    return {
        "functions": scores,
        "overall_percentage": overall_pct,
        "total_controls": total_controls,
        "stale_evidence_count": stale_evidence_count,
        "dependency_breach_count": dependency_breach_count,
        "compensating_count": compensating_count,
    }


# ---------------------------------------------------------------------------
# ISO 27001 scoring
# ---------------------------------------------------------------------------

def calc_iso27001_scores(data: dict) -> dict:
    """Calculate ISO 27001 Annex A compliance with evidence staleness detection."""
    domains = data["iso27001"]["domains"]
    results = []
    total_controls = 0
    total_implemented = 0
    total_partial = 0
    stale_evidence_domains = 0

    for d in domains:
        t = d["total"]
        imp = d["implemented"]
        par = d["partial"]
        evidence_date = d.get("evidence_date")

        score = imp + (par * 0.5)
        pct = round((score / t) * 100) if t > 0 else 0

        exp = evidence_expiry_status(evidence_date)
        if exp["stale"] and pct > 0:
            pct = min(pct, round(pct * 0.80))
            stale_evidence_domains += 1

        if pct >= 80 and not exp["stale"]:
            health = "Compliant"
        elif pct >= 50:
            health = "At Risk"
        else:
            health = "Non-Compliant"

        results.append({
            **d,
            "score": round(score, 1),
            "percentage": pct,
            "evidence_status": exp,
            "health": health,
        })
        total_controls += t
        total_implemented += imp
        total_partial += par

    overall = total_implemented + (total_partial * 0.5)
    overall_pct = (
        round((overall / total_controls) * 100) if total_controls > 0 else 0
    )

    return {
        "domains": results,
        "overall_percentage": overall_pct,
        "total_controls": total_controls,
        "stale_evidence_domains": stale_evidence_domains,
    }


# ---------------------------------------------------------------------------
# Policy lifecycle
# ---------------------------------------------------------------------------

def get_policy_summary(policies: list[dict]) -> dict:
    """Summarise policy lifecycle status with expiry proximity alerts."""
    summary: dict[str, int] = {
        "Current": 0,
        "Under Review": 0,
        "Draft": 0,
        "Expired": 0,
    }
    expiring_soon: list[dict] = []

    for p in policies:
        status = p.get("status", "Unknown")
        summary[status] = summary.get(status, 0) + 1

        review_date_str = p.get("next_review")
        if review_date_str and status != "Expired":
            try:
                review_date = datetime.strptime(review_date_str, "%Y-%m-%d").date()
                days_remaining = (review_date - date.today()).days
                if 0 <= days_remaining <= POLICY_ALERT_WINDOW_DAYS:
                    expiring_soon.append({
                        "id": p.get("id"),
                        "name": p.get("name", "Untitled"),
                        "next_review": review_date_str,
                        "days_remaining": days_remaining,
                    })
            except ValueError:
                pass

    return {
        "total": len(policies),
        "by_status": summary,
        "current_pct": (
            round((summary.get("Current", 0) / len(policies)) * 100)
            if policies
            else 0
        ),
        "expiring_soon": sorted(expiring_soon, key=lambda x: x["days_remaining"]),
    }
