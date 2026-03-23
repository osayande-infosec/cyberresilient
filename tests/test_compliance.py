"""Tests for compliance scoring logic."""

from cyberresilient.services.compliance_service import (
    calc_nist_csf_scores,
    calc_iso27001_scores,
    get_policy_summary,
)


def test_nist_csf_scores():
    data = {
        "nist_csf": {
            "functions": {
                "Identify": {
                    "description": "Asset management and risk assessment",
                    "categories": {
                        "ID.AM": {"name": "Asset Management", "status": "Implemented", "evidence": "CMDB", "evidence_date": "2026-01-01"},
                        "ID.RA": {"name": "Risk Assessment", "status": "Partial", "evidence": "Annual RA", "evidence_date": "2026-01-01"},
                    },
                },
            },
        },
    }
    scores = calc_nist_csf_scores(data)
    assert scores["overall_percentage"] == 70  # (1.0 + 0.40) / 2 * 100
    assert scores["functions"]["Identify"]["percentage"] == 70


def test_iso27001_scores():
    data = {
        "iso27001": {
            "domains": [
                {"id": "A.5", "name": "Organizational", "total": 10, "implemented": 8, "partial": 2, "evidence_date": "2026-01-01"},
                {"id": "A.6", "name": "People", "total": 5, "implemented": 5, "partial": 0, "evidence_date": "2026-01-01"},
            ],
        },
    }
    scores = calc_iso27001_scores(data)
    # Domain A.5: (8 + 2*0.5) / 10 = 90%
    # Domain A.6: 5/5 = 100%
    # Overall: (8+5 + (2+0)*0.5) / 15 = (13+1)/15 = 93%
    assert scores["overall_percentage"] == 93
    assert scores["domains"][0]["percentage"] == 90
    assert scores["domains"][1]["percentage"] == 100


def test_policy_summary():
    policies = [
        {"status": "Current"},
        {"status": "Current"},
        {"status": "Under Review"},
        {"status": "Draft"},
        {"status": "Expired"},
    ]
    summary = get_policy_summary(policies)
    assert summary["total"] == 5
    assert summary["by_status"]["Current"] == 2
    assert summary["current_pct"] == 40
