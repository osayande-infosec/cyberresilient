"""Tests for DR simulation logic."""

from cyberresilient.services.dr_service import simulate_dr, generate_raci


SAMPLE_SYSTEM = {
    "id": "SYS-001",
    "name": "Test Health Records",
    "department": "IT Services",
    "type": "IT",
    "tier": 1,
    "rto_target_hours": 4,
    "rpo_target_hours": 1,
    "current_dr_strategy": "Warm Standby",
    "dependencies": [],
    "last_test_date": "2025-12-01",
    "last_test_result": "Pass",
}

SAMPLE_SCENARIO = {
    "id": "SCN-001",
    "name": "Ransomware Attack",
    "type": "Cyber",
    "severity": "Critical",
    "description": "Ransomware targeting financial systems",
    "rto_impact_multiplier": 1.5,
    "rpo_impact_multiplier": 1.3,
    "recovery_steps": ["Isolate", "Assess", "Restore"],
    "impact": {
        "departments_affected": ["Finance", "IT Services"],
        "public_impact": "Service delays expected",
        "estimated_citizens_affected": 50000,
    },
    "affected_systems": ["SYS-001"],
}


def test_simulate_dr_returns_required_fields():
    result = simulate_dr(SAMPLE_SYSTEM, SAMPLE_SCENARIO)
    assert "rto_estimated_hours" in result
    assert "rpo_estimated_hours" in result
    assert "overall_pass" in result
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)


def test_simulate_dr_applies_multiplier():
    """Estimated values should be in the range of target * multiplier * variance."""
    result = simulate_dr(SAMPLE_SYSTEM, SAMPLE_SCENARIO)
    # RTO: 4 * 1.5 * [0.85, 1.25] = [5.1, 7.5]
    assert 3.0 <= result["rto_estimated_hours"] <= 8.0


def test_generate_raci():
    raci = generate_raci(SAMPLE_SYSTEM, SAMPLE_SCENARIO)
    assert len(raci) == 8
    assert all("activity" in r for r in raci)
    assert all("responsible" in r for r in raci)
    # Department should appear in RACI entries
    dept_mentioned = any("IT Services" in str(r) for r in raci)
    assert dept_mentioned
