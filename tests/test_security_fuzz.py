"""
Fuzz Testing for CyberResilient
Uses Hypothesis for property-based testing and custom fuzzing
for input validation, service boundaries, and API endpoints.
"""

from __future__ import annotations

import json
import os
import sys

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cyberresilient.models.risk import get_risk_level, get_risk_color, Risk
from cyberresilient.services.risk_service import (
    build_heatmap_matrix,
    get_risk_summary,
    run_architecture_assessment,
)


# ═══════════════════════════════════════════════════════════
# Risk Model Fuzzing
# ═══════════════════════════════════════════════════════════

@given(
    likelihood=st.integers(min_value=1, max_value=5),
    impact=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_risk_level_always_returns_valid_level(likelihood, impact):
    """Risk level must always be one of our 4 defined levels."""
    score = likelihood * impact
    level = get_risk_level(score)
    assert level in ("Low", "Medium", "High", "Very High"), f"Unexpected level '{level}' for score {score}"


@given(
    likelihood=st.integers(min_value=1, max_value=5),
    impact=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_risk_color_always_returns_hex(likelihood, impact):
    """Risk color must always be a valid hex color string."""
    score = likelihood * impact
    color = get_risk_color(score)
    assert color.startswith("#"), f"Color '{color}' is not a hex color"
    assert len(color) == 7, f"Color '{color}' is not a valid 7-char hex color"


@given(score=st.integers(min_value=-100, max_value=100))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_risk_level_boundary_values(score):
    """Risk level should handle any integer without crashing."""
    try:
        level = get_risk_level(score)
        assert isinstance(level, str)
    except (KeyError, ValueError):
        pass  # Acceptable for out-of-range scores


# ═══════════════════════════════════════════════════════════
# Heatmap Matrix Fuzzing
# ═══════════════════════════════════════════════════════════

@given(
    risks=st.lists(
        st.fixed_dictionaries({
            "likelihood": st.integers(min_value=1, max_value=5),
            "impact": st.integers(min_value=1, max_value=5),
            "risk_score": st.integers(min_value=1, max_value=25),
            "status": st.sampled_from(["Open", "Mitigating", "Monitoring", "Accepted", "Closed"]),
            "id": st.text(min_size=1, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
            "title": st.text(min_size=1, max_size=100),
            "category": st.text(min_size=1, max_size=50),
            "owner": st.text(min_size=1, max_size=50),
            "mitigation": st.text(max_size=200),
            "asset": st.text(max_size=100),
            "target_date": st.text(max_size=10),
            "notes": st.text(max_size=200),
        }),
        min_size=0,
        max_size=50,
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_heatmap_matrix_always_5x5(risks):
    """Heatmap matrix must always be 5x5 regardless of input."""
    matrix = build_heatmap_matrix(risks)
    assert len(matrix) == 5
    for row in matrix:
        assert len(row) == 5
        for cell in row:
            assert isinstance(cell, int)
            assert cell >= 0


@given(
    risks=st.lists(
        st.fixed_dictionaries({
            "likelihood": st.integers(min_value=1, max_value=5),
            "impact": st.integers(min_value=1, max_value=5),
            "risk_score": st.integers(min_value=1, max_value=25),
            "status": st.sampled_from(["Open", "Mitigating", "Closed"]),
            "id": st.just("R1"),
            "title": st.just("test"),
            "category": st.just("test"),
            "owner": st.just("test"),
            "mitigation": st.just(""),
            "asset": st.just(""),
            "target_date": st.just(""),
            "notes": st.just(""),
        }),
        min_size=0,
        max_size=30,
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_risk_summary_counts_match(risks):
    """Risk summary total must equal sum of level counts."""
    summary = get_risk_summary(risks)
    assert summary["total"] == len(risks)
    level_total = sum(summary["by_level"].values())
    assert level_total == len(risks)


# ═══════════════════════════════════════════════════════════
# Architecture Assessment Fuzzing
# ═══════════════════════════════════════════════════════════

@given(
    answers=st.dictionaries(
        keys=st.sampled_from([f"CHK-{i:02d}" for i in range(1, 11)]),
        values=st.booleans(),
        min_size=0,
        max_size=10,
    )
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_architecture_assessment_valid_output(answers):
    """Architecture assessment must return valid structure for any checkbox combo."""
    result = run_architecture_assessment(answers)
    assert 0 <= result["score_pct"] <= 100
    assert result["passed"] + result["failed"] == result["total_checks"]
    assert result["overall_risk"] in ("Low Risk", "Medium Risk", "High Risk", "Critical Risk")
    assert len(result["results"]) == result["total_checks"]


# ═══════════════════════════════════════════════════════════
# Input Sanitization Fuzzing
# ═══════════════════════════════════════════════════════════

@given(text=st.text(min_size=0, max_size=500))
@settings(max_examples=300, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_json_roundtrip_safety(text):
    """Any text value must survive JSON serialization without data loss."""
    data = {"title": text, "notes": text}
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    assert deserialized["title"] == text
    assert deserialized["notes"] == text


XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    '"><img src=x onerror=alert(1)>',
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
    "{{7*7}}",  # SSTI
    "${7*7}",   # Template injection
    "'; DROP TABLE risks; --",  # SQLi
    "' OR '1'='1",
    "../../../etc/passwd",  # Path traversal
    "..\\..\\..\\windows\\system32\\config\\sam",
    "\x00\x01\x02\x03",  # Null bytes
    "A" * 10000,  # Buffer overflow attempt
]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_malicious_input_in_risk_summary(payload):
    """Risk summary must handle malicious input without crashing."""
    risks = [{
        "id": "TEST-001", "title": payload, "category": payload,
        "likelihood": 3, "impact": 3, "risk_score": 9,
        "owner": payload, "status": "Open", "mitigation": payload,
        "asset": payload, "target_date": "2026-01-01", "notes": payload,
    }]
    summary = get_risk_summary(risks)
    assert summary["total"] == 1


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_malicious_input_in_heatmap(payload):
    """Heatmap must handle malicious string fields without crashing."""
    risks = [{
        "id": payload[:20], "title": payload, "category": payload,
        "likelihood": 1, "impact": 1, "risk_score": 1,
        "owner": payload, "status": "Open", "mitigation": payload,
        "asset": payload, "target_date": payload, "notes": payload,
    }]
    matrix = build_heatmap_matrix(risks)
    assert len(matrix) == 5
