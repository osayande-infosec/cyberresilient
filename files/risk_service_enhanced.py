"""
Risk scoring, heat map generation, and architecture gap analysis.

Enhancements over v1:
  - Inherent vs residual risk split
  - Residual risk calculation after mitigation effectiveness
  - Risk appetite threshold enforcement (blocks closure without sign-off)
  - Evidence expiry tracking per risk item
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from cyberresilient.config import DATA_DIR
from cyberresilient.models.risk import (
    get_risk_level,
)

# ---------------------------------------------------------------------------
# Risk appetite configuration
# Any residual risk score above this threshold requires explicit sign-off
# before a risk can be marked Accepted or Closed.
# ---------------------------------------------------------------------------
RISK_APPETITE_THRESHOLD: int = 12  # on a 1-25 scale (e.g. 4x3 or 3x4)
RISK_APPETITE_LABEL: str = "High"  # human-readable name for UI

# Mitigation effectiveness multipliers applied to raw score
# to derive residual risk. Keys match the "mitigation_effectiveness"
# field stored on each risk row.
MITIGATION_EFFECTIVENESS_MULTIPLIERS: dict[str, float] = {
    "None": 1.00,  # no controls in place
    "Partial": 0.65,  # some controls, gaps remain
    "Largely": 0.35,  # controls mostly in place, minor gaps
    "Full": 0.10,  # fully mitigated; residual is near-zero
}

# Evidence expires after this many days if not refreshed
EVIDENCE_EXPIRY_DAYS: int = 365


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _db_available() -> bool:
    try:
        from sqlalchemy import inspect

        from cyberresilient.database import get_engine

        return inspect(get_engine()).has_table("risks")
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def calc_inherent_score(likelihood: int, impact: int) -> int:
    """Raw (inherent) risk score before any mitigation."""
    return likelihood * impact


def calc_residual_score(
    inherent_score: int,
    mitigation_effectiveness: str = "None",
) -> int:
    """
    Residual risk score after applying mitigation effectiveness multiplier.
    Always returns at least 1 to acknowledge residual risk can never be zero.
    """
    multiplier = MITIGATION_EFFECTIVENESS_MULTIPLIERS.get(mitigation_effectiveness, 1.0)
    return max(1, round(inherent_score * multiplier))


def exceeds_risk_appetite(residual_score: int) -> bool:
    """Return True when the residual score exceeds the organisation's appetite."""
    return residual_score > RISK_APPETITE_THRESHOLD


# ---------------------------------------------------------------------------
# Evidence expiry
# ---------------------------------------------------------------------------


def is_evidence_expired(evidence_date: str | None) -> bool:
    """
    Return True if the evidence collection date is older than EVIDENCE_EXPIRY_DAYS
    or has never been set.
    """
    if not evidence_date:
        return True
    try:
        collected = datetime.strptime(evidence_date, "%Y-%m-%d").date()
        return (date.today() - collected).days > EVIDENCE_EXPIRY_DAYS
    except ValueError:
        return True


def days_until_evidence_expires(evidence_date: str | None) -> int | None:
    """
    Return the number of days until evidence expires, or None if already expired
    or never set.
    """
    if not evidence_date:
        return None
    try:
        collected = datetime.strptime(evidence_date, "%Y-%m-%d").date()
        expires_on = collected + timedelta(days=EVIDENCE_EXPIRY_DAYS)
        remaining = (expires_on - date.today()).days
        return remaining if remaining > 0 else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Load / persist
# ---------------------------------------------------------------------------


def load_risks() -> list[dict]:
    """Load risks from database, falling back to JSON seed data."""
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
    """Build a 5×5 matrix counting risks at each likelihood × impact cell."""
    matrix = [[0] * 5 for _ in range(5)]
    for r in risks:
        li = r["likelihood"] - 1
        im = r["impact"] - 1
        matrix[li][im] += 1
    return matrix


def get_risk_summary(risks: list[dict]) -> dict:
    """
    Summarise risks by inherent level, residual level, status,
    and flag counts for appetite breaches and expired evidence.
    """
    total = len(risks)
    by_inherent_level: dict[str, int] = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0}
    by_residual_level: dict[str, int] = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0}
    by_status: dict[str, int] = {}
    appetite_breaches = 0
    expired_evidence = 0

    for r in risks:
        inherent = r.get("risk_score", calc_inherent_score(r["likelihood"], r["impact"]))
        residual = r.get("residual_score", inherent)

        by_inherent_level[get_risk_level(inherent)] = by_inherent_level.get(get_risk_level(inherent), 0) + 1
        by_residual_level[get_risk_level(residual)] = by_residual_level.get(get_risk_level(residual), 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

        if exceeds_risk_appetite(residual):
            appetite_breaches += 1
        if is_evidence_expired(r.get("evidence_date")):
            expired_evidence += 1

    return {
        "total": total,
        "by_inherent_level": by_inherent_level,
        "by_residual_level": by_residual_level,
        "by_status": by_status,
        "appetite_breaches": appetite_breaches,
        "expired_evidence_count": expired_evidence,
    }


# ---------------------------------------------------------------------------
# Closure guard
# ---------------------------------------------------------------------------


def can_close_risk(risk: dict) -> tuple[bool, str]:
    """
    Determine whether a risk is eligible for Accepted / Closed status.

    Returns (allowed: bool, reason: str).
    A risk that exceeds appetite requires an explicit approver sign-off
    stored in the `sign_off_by` field before closure is permitted.
    """
    residual = risk.get(
        "residual_score",
        calc_residual_score(
            calc_inherent_score(risk["likelihood"], risk["impact"]),
            risk.get("mitigation_effectiveness", "None"),
        ),
    )

    if not exceeds_risk_appetite(residual):
        return True, "Residual score within appetite — closure permitted."

    sign_off = (risk.get("sign_off_by") or "").strip()
    if sign_off:
        return True, f"Closure approved by: {sign_off}"

    return (
        False,
        f"Residual score {residual} exceeds appetite threshold "
        f"({RISK_APPETITE_THRESHOLD}). Sign-off required before closure.",
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def _next_risk_id() -> str:
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
    return "RISK-100"


def create_risk(data: dict, user: str = "system") -> dict:
    """
    Create a new risk entry.

    Computes both inherent_score and residual_score from the submitted data.
    Enforces closure guard if status is Accepted/Closed at creation time.
    """
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.audit_service import log_action

    risk_id = _next_risk_id()
    data["id"] = risk_id

    inherent = calc_inherent_score(data["likelihood"], data["impact"])
    residual = calc_residual_score(inherent, data.get("mitigation_effectiveness", "None"))
    data["risk_score"] = inherent
    data["residual_score"] = residual

    # Enforce closure guard
    if data.get("status") in ("Accepted", "Closed"):
        allowed, reason = can_close_risk(data)
        if not allowed:
            raise PermissionError(reason)

    session = get_session()
    try:
        row = RiskRow(
            id=risk_id,
            title=data["title"],
            category=data["category"],
            likelihood=data["likelihood"],
            impact=data["impact"],
            risk_score=inherent,
            residual_score=residual,
            mitigation_effectiveness=data.get("mitigation_effectiveness", "None"),
            owner=data["owner"],
            status=data["status"],
            mitigation=data.get("mitigation", ""),
            asset=data.get("asset", ""),
            target_date=data.get("target_date", ""),
            notes=data.get("notes", ""),
            evidence_date=data.get("evidence_date"),
            sign_off_by=data.get("sign_off_by", ""),
        )
        session.add(row)
        log_action(
            session,
            action="create",
            entity_type="risk",
            entity_id=risk_id,
            user=user,
            after=data,
        )
        session.commit()
        return row.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_risk(risk_id: str, data: dict, user: str = "system") -> dict:
    """
    Update an existing risk entry.

    Re-derives inherent and residual scores from current field values.
    Blocks transition to Accepted/Closed if appetite guard fails.
    """
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.audit_service import log_action

    session = get_session()
    try:
        row = session.query(RiskRow).filter_by(id=risk_id).first()
        if not row:
            raise ValueError(f"Risk {risk_id} not found")

        before = row.to_dict()

        # Recalculate scores
        likelihood = data.get("likelihood", row.likelihood)
        impact = data.get("impact", row.impact)
        mitigation_effectiveness = data.get(
            "mitigation_effectiveness",
            getattr(row, "mitigation_effectiveness", "None"),
        )
        inherent = calc_inherent_score(likelihood, impact)
        residual = calc_residual_score(inherent, mitigation_effectiveness)
        data["risk_score"] = inherent
        data["residual_score"] = residual

        # Enforce closure guard
        if data.get("status") in ("Accepted", "Closed"):
            merged = {**before, **data}
            allowed, reason = can_close_risk(merged)
            if not allowed:
                raise PermissionError(reason)

        mutable_fields = (
            "title",
            "category",
            "likelihood",
            "impact",
            "risk_score",
            "residual_score",
            "mitigation_effectiveness",
            "owner",
            "status",
            "mitigation",
            "asset",
            "target_date",
            "notes",
            "evidence_date",
            "sign_off_by",
        )
        for field in mutable_fields:
            if field in data:
                setattr(row, field, data[field])

        log_action(
            session,
            action="update",
            entity_type="risk",
            entity_id=risk_id,
            user=user,
            before=before,
            after=row.to_dict(),
        )
        session.commit()
        return row.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_risk(risk_id: str, user: str = "system") -> None:
    """Delete a risk entry with full audit log."""
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
        log_action(
            session,
            action="delete",
            entity_type="risk",
            entity_id=risk_id,
            user=user,
            before=before,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Architecture assessment (unchanged from v1, kept for completeness)
# ---------------------------------------------------------------------------

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
        "risk_if_missing": "Regulatory compliance violation",
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
