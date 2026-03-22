"""
Risk scoring, heat map generation, and architecture gap analysis.
"""

from __future__ import annotations

import json
from pathlib import Path

from cyberresilient.config import DATA_DIR
from cyberresilient.models.risk import (
    IMPACT_LABELS,
    LIKELIHOOD_LABELS,
    ArchitectureCheck,
    Risk,
    get_risk_level,
)


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("risks")
    except Exception:
        return False


def load_risks() -> list[dict]:
    """Load risks from database, falling back to JSON."""
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import RiskRow
        session = get_session()
        try:
            rows = session.query(RiskRow).all()
            if rows:
                return [r.to_dict() for r in rows]
        finally:
            session.close()

    with open(DATA_DIR / "risks.json", encoding="utf-8") as f:
        return json.load(f)


def build_heatmap_matrix(risks: list[dict]) -> list[list[int]]:
    """Build a 5x5 matrix counting risks at each likelihood x impact cell."""
    matrix = [[0] * 5 for _ in range(5)]
    for r in risks:
        li = r["likelihood"] - 1
        im = r["impact"] - 1
        matrix[li][im] += 1
    return matrix


def get_risk_summary(risks: list[dict]) -> dict:
    """Summarise risks by level and status."""
    total = len(risks)
    by_level = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0}
    by_status: dict[str, int] = {}
    for r in risks:
        level = get_risk_level(r["risk_score"])
        by_level[level] = by_level.get(level, 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    return {"total": total, "by_level": by_level, "by_status": by_status}


ARCHITECTURE_CHECKS: list[dict] = [
    {
        "id": "CHK-01",
        "control": "Single Sign-On (SSO) Integration",
        "framework": "NIST 800-53 IA-2",
        "question": "Does the solution support SSO (SAML/OIDC)?",
        "risk_if_missing": "Credential sprawl, inability to enforce MFA, audit gaps",
        "recommendation": "Require SAML 2.0 or OIDC integration before procurement approval",
    },
    {
        "id": "CHK-02",
        "control": "Data Encryption at Rest",
        "framework": "NIST 800-53 SC-28",
        "question": "Is all data encrypted at rest using AES-256 or equivalent?",
        "risk_if_missing": "Data exposure in event of physical theft or cloud misconfiguration",
        "recommendation": "Require AES-256 encryption at rest; verify key management practices",
    },
    {
        "id": "CHK-03",
        "control": "Data Encryption in Transit",
        "framework": "NIST 800-53 SC-8",
        "question": "Is all data encrypted in transit using TLS 1.2+?",
        "risk_if_missing": "Man-in-the-middle attacks, data interception",
        "recommendation": "Mandate TLS 1.2+ minimum; disable legacy protocols",
    },
    {
        "id": "CHK-04",
        "control": "Multi-Factor Authentication",
        "framework": "NIST 800-53 IA-2(1)",
        "question": "Does the solution enforce MFA for all administrative access?",
        "risk_if_missing": "Credential compromise leads to full administrative takeover",
        "recommendation": "Require MFA for all privileged and standard user access",
    },
    {
        "id": "CHK-05",
        "control": "SOC 2 Type II Certification",
        "framework": "AICPA TSC",
        "question": "Does the vendor hold a current SOC 2 Type II report?",
        "risk_if_missing": "No independent verification of security controls",
        "recommendation": "Require annual SOC 2 Type II; review for exceptions",
    },
    {
        "id": "CHK-06",
        "control": "Data Residency Compliance",
        "framework": "Regulatory / Privacy",
        "question": "Is all data stored and processed within the required jurisdiction?",
        "risk_if_missing": "Regulatory compliance violation — data may need to remain in-jurisdiction",
        "recommendation": "Contractually require data residency; verify cloud region",
    },
    {
        "id": "CHK-07",
        "control": "Backup & Disaster Recovery",
        "framework": "NIST 800-53 CP-9",
        "question": "Does the vendor provide automated backups with tested DR?",
        "risk_if_missing": "Data loss in vendor outage; no recovery capability",
        "recommendation": "Require documented RTO/RPO SLAs with evidence of testing",
    },
    {
        "id": "CHK-08",
        "control": "Breach Notification SLA",
        "framework": "NIST 800-53 IR-6",
        "question": "Does the vendor commit to breach notification within 24 hours?",
        "risk_if_missing": "Delayed awareness of compromise affecting your data",
        "recommendation": "Require ≤24-hour notification SLA in contract",
    },
    {
        "id": "CHK-09",
        "control": "API Security & Rate Limiting",
        "framework": "OWASP API Top 10",
        "question": "Are APIs secured with authentication, authorization, and rate limiting?",
        "risk_if_missing": "API abuse, data exfiltration, denial of service",
        "recommendation": "Require API key/OAuth, rate limiting, and input validation",
    },
    {
        "id": "CHK-10",
        "control": "Vulnerability Management",
        "framework": "CIS Control 7",
        "question": "Does the vendor patch critical vulnerabilities within 72 hours?",
        "risk_if_missing": "Prolonged exposure to known exploits",
        "recommendation": "Require documented patching SLA: Critical <72h, High <7d",
    },
]


def _next_risk_id() -> str:
    """Generate the next RISK-NNN id."""
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import RiskRow
        session = get_session()
        try:
            max_id = session.query(RiskRow.id).order_by(RiskRow.id.desc()).first()
            if max_id:
                num = int(max_id[0].split("-")[1]) + 1
                return f"RISK-{num:03d}"
        finally:
            session.close()
    return f"RISK-{100:03d}"


def create_risk(data: dict, user: str = "system") -> dict:
    """Create a new risk entry in the database."""
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.audit_service import log_action

    risk_id = _next_risk_id()
    data["id"] = risk_id
    data["risk_score"] = data["likelihood"] * data["impact"]

    session = get_session()
    try:
        row = RiskRow(
            id=risk_id, title=data["title"], category=data["category"],
            likelihood=data["likelihood"], impact=data["impact"],
            risk_score=data["risk_score"], owner=data["owner"],
            status=data["status"], mitigation=data.get("mitigation", ""),
            asset=data.get("asset", ""), target_date=data.get("target_date", ""),
            notes=data.get("notes", ""),
        )
        session.add(row)
        log_action(session, action="create", entity_type="risk",
                   entity_id=risk_id, user=user, after=data)
        session.commit()
        return row.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_risk(risk_id: str, data: dict, user: str = "system") -> dict:
    """Update an existing risk entry."""
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.audit_service import log_action

    session = get_session()
    try:
        row = session.query(RiskRow).filter_by(id=risk_id).first()
        if not row:
            raise ValueError(f"Risk {risk_id} not found")
        before = row.to_dict()
        data["risk_score"] = data["likelihood"] * data["impact"]
        for field in ("title", "category", "likelihood", "impact", "risk_score",
                      "owner", "status", "mitigation", "asset", "target_date", "notes"):
            if field in data:
                setattr(row, field, data[field])
        log_action(session, action="update", entity_type="risk",
                   entity_id=risk_id, user=user, before=before, after=row.to_dict())
        session.commit()
        return row.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_risk(risk_id: str, user: str = "system") -> None:
    """Delete a risk entry."""
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.audit_service import log_action

    session = get_session()
    try:
        row = session.query(RiskRow).filter_by(id=risk_id).first()
        if not row:
            raise ValueError(f"Risk {risk_id} not found")
        before = row.to_dict()
        session.delete(row)
        log_action(session, action="delete", entity_type="risk",
                   entity_id=risk_id, user=user, before=before)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_architecture_assessment(answers: dict[str, bool]) -> dict:
    """Score a vendor architecture assessment from checkbox answers."""
    results = []
    passed = 0
    for check in ARCHITECTURE_CHECKS:
        is_pass = answers.get(check["id"], False)
        if is_pass:
            passed += 1
        results.append({**check, "passed": is_pass})

    total = len(ARCHITECTURE_CHECKS)
    failed = total - passed
    score_pct = round((passed / total) * 100) if total > 0 else 0

    if score_pct >= 90:
        overall_risk = "Low Risk"
    elif score_pct >= 70:
        overall_risk = "Medium Risk"
    elif score_pct >= 50:
        overall_risk = "High Risk"
    else:
        overall_risk = "Critical Risk"

    return {
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "score_pct": score_pct,
        "overall_risk": overall_risk,
        "results": results,
    }
