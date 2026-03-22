"""Tests for risk scoring logic."""

from cyberresilient.models.risk import get_risk_level, get_risk_color
from cyberresilient.services.risk_service import (
    build_heatmap_matrix,
    get_risk_summary,
    run_architecture_assessment,
)


def test_risk_level_classification():
    assert get_risk_level(1) == "Low"
    assert get_risk_level(4) == "Low"
    assert get_risk_level(5) == "Medium"
    assert get_risk_level(9) == "Medium"
    assert get_risk_level(10) == "High"
    assert get_risk_level(15) == "High"
    assert get_risk_level(16) == "Very High"
    assert get_risk_level(25) == "Very High"


def test_risk_color_mapping():
    assert get_risk_color(3) == "#4CAF50"    # Low = green
    assert get_risk_color(7) == "#FFC107"    # Medium = yellow
    assert get_risk_color(12) == "#FF9800"   # High = orange
    assert get_risk_color(20) == "#F44336"   # Very High = red


def test_heatmap_matrix():
    risks = [
        {"likelihood": 3, "impact": 4, "risk_score": 12, "status": "Open"},
        {"likelihood": 5, "impact": 5, "risk_score": 25, "status": "Open"},
        {"likelihood": 1, "impact": 1, "risk_score": 1, "status": "Monitoring"},
    ]
    matrix = build_heatmap_matrix(risks)
    assert matrix[2][3] == 1  # likelihood=3, impact=4 (0-indexed)
    assert matrix[4][4] == 1  # likelihood=5, impact=5
    assert matrix[0][0] == 1  # likelihood=1, impact=1


def test_risk_summary():
    risks = [
        {"risk_score": 20, "status": "Open"},
        {"risk_score": 12, "status": "Mitigating"},
        {"risk_score": 6, "status": "Open"},
        {"risk_score": 2, "status": "Monitoring"},
    ]
    summary = get_risk_summary(risks)
    assert summary["total"] == 4
    assert summary["by_level"]["Very High"] == 1
    assert summary["by_level"]["High"] == 1
    assert summary["by_level"]["Medium"] == 1
    assert summary["by_level"]["Low"] == 1
    assert summary["by_status"]["Open"] == 2


def test_architecture_assessment_all_pass():
    answers = {f"CHK-{i:02d}": True for i in range(1, 11)}
    result = run_architecture_assessment(answers)
    assert result["passed"] == 10
    assert result["failed"] == 0
    assert result["score_pct"] == 100
    assert result["overall_risk"] == "Low Risk"


def test_architecture_assessment_all_fail():
    answers = {f"CHK-{i:02d}": False for i in range(1, 11)}
    result = run_architecture_assessment(answers)
    assert result["passed"] == 0
    assert result["failed"] == 10
    assert result["score_pct"] == 0
    assert result["overall_risk"] == "Critical Risk"
