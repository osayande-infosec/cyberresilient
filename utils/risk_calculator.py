"""
Risk Calculator
Scoring, heat map data generation, and architecture gap analysis.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

LIKELIHOOD_LABELS = {1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost Certain"}
IMPACT_LABELS = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Catastrophic"}
RISK_LEVELS = {
    (1, 4): "Low",
    (5, 9): "Medium",
    (10, 14): "High",
    (15, 19): "Critical",
    (20, 25): "Extreme",
}


def load_risks():
    with open(DATA_DIR / "risks.json", "r") as f:
        return json.load(f)


def get_risk_level(score: int) -> str:
    for (lo, hi), level in RISK_LEVELS.items():
        if lo <= score <= hi:
            return level
    return "Unknown"


def get_risk_color(score: int) -> str:
    level = get_risk_level(score)
    return {
        "Low": "#4CAF50",
        "Medium": "#FFC107",
        "High": "#FF9800",
        "Critical": "#F44336",
        "Extreme": "#B71C1C",
    }.get(level, "#9E9E9E")


def build_heatmap_matrix(risks: list) -> list[list[int]]:
    """Build a 5x5 matrix counting risks at each likelihood x impact cell."""
    matrix = [[0] * 5 for _ in range(5)]
    for r in risks:
        li = r["likelihood"] - 1  # 0-indexed
        im = r["impact"] - 1
        matrix[li][im] += 1
    return matrix


def get_risk_summary(risks: list) -> dict:
    total = len(risks)
    by_level = {"Extreme": 0, "Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    by_status = {}
    for r in risks:
        level = get_risk_level(r["risk_score"])
        by_level[level] = by_level.get(level, 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    return {"total": total, "by_level": by_level, "by_status": by_status}


# ── Architecture Risk Advisor ──────────────────────────────

ARCHITECTURE_CHECKS = [
    {
        "id": "CHK-01",
        "control": "Single Sign-On (SSO) Integration",
        "framework": "NIST 800-53 IA-2",
        "question": "Does the solution support SSO (SAML/OIDC) with Azure AD?",
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
        "control": "Data Residency (Canada)",
        "framework": "MFIPPA / PIPEDA",
        "question": "Is all data stored and processed within Canada?",
        "risk_if_missing": "MFIPPA compliance violation — municipal data must remain in Canada",
        "recommendation": "Contractually require Canadian data residency; verify Azure/AWS region",
    },
    {
        "id": "CHK-07",
        "control": "Backup & Disaster Recovery",
        "framework": "NIST 800-53 CP-9",
        "question": "Does the vendor provide automated backups with tested DR?",
        "risk_if_missing": "Data loss in vendor outage; no recovery capability",
        "recommendation": "Require documented DR plan with RTO/RPO commitments in SLA",
    },
    {
        "id": "CHK-08",
        "control": "Incident Notification SLA",
        "framework": "NIST 800-53 IR-6",
        "question": "Does the vendor commit to notify within 24 hours of a breach?",
        "risk_if_missing": "Delayed breach discovery; inability to meet IPC notification requirements",
        "recommendation": "Require 24-hour breach notification SLA in contract",
    },
    {
        "id": "CHK-09",
        "control": "API Security",
        "framework": "OWASP API Top 10",
        "question": "Are APIs authenticated, rate-limited, and logged?",
        "risk_if_missing": "Unauthorized data access, API abuse, data scraping",
        "recommendation": "Require OAuth 2.0 API auth, rate limiting, and API activity logging",
    },
    {
        "id": "CHK-10",
        "control": "Vulnerability Management",
        "framework": "CIS Control 7",
        "question": "Does the vendor have a vulnerability management and patching program?",
        "risk_if_missing": "Unpatched vulnerabilities exploited by attackers",
        "recommendation": "Require evidence of regular scanning and critical patch SLAs (< 72 hours)",
    },
]


def run_architecture_assessment(answers: dict[str, bool]) -> dict:
    """
    answers: dict mapping check ID -> True (yes/pass) or False (no/fail).
    Returns assessment results.
    """
    results = []
    pass_count = 0
    fail_count = 0

    for check in ARCHITECTURE_CHECKS:
        passed = answers.get(check["id"], False)
        if passed:
            pass_count += 1
        else:
            fail_count += 1
        results.append({
            **check,
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
        })

    total = len(ARCHITECTURE_CHECKS)
    score = round((pass_count / total) * 100) if total > 0 else 0

    if score >= 90:
        overall = "Low Risk"
    elif score >= 70:
        overall = "Medium Risk"
    elif score >= 50:
        overall = "High Risk"
    else:
        overall = "Critical Risk"

    return {
        "total_checks": total,
        "passed": pass_count,
        "failed": fail_count,
        "score_pct": score,
        "overall_risk": overall,
        "results": results,
    }
