"""Tests for database layer, CLI seeding, and audit logging."""

import json
import os
import tempfile

import pytest

from cyberresilient.database import Base, get_engine, get_session, init_db, reset_engine


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for each test."""
    reset_engine()
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    reset_engine()
    init_db()
    yield
    reset_engine()


def test_init_db_creates_tables():
    from sqlalchemy import inspect
    inspector = inspect(get_engine())
    tables = inspector.get_table_names()
    assert "risks" in tables
    assert "systems" in tables
    assert "scenarios" in tables
    assert "policies" in tables
    assert "kpi_metrics" in tables
    assert "monthly_incidents" in tables
    assert "audit_log" in tables
    assert "users" in tables


def test_risk_crud():
    from cyberresilient.models.db_models import RiskRow
    session = get_session()
    try:
        risk = RiskRow(
            id="TEST-001",
            title="Test Risk",
            category="Technical",
            likelihood=3,
            impact=4,
            risk_score=12,
            owner="Tester",
            status="Open",
            mitigation="Test mitigation",
            asset="Test Asset",
            target_date="2026-06-01",
        )
        session.add(risk)
        session.commit()

        loaded = session.query(RiskRow).filter_by(id="TEST-001").first()
        assert loaded is not None
        assert loaded.title == "Test Risk"
        assert loaded.risk_score == 12

        d = loaded.to_dict()
        assert d["id"] == "TEST-001"
        assert d["likelihood"] == 3
    finally:
        session.close()


def test_audit_logging():
    from cyberresilient.services.audit_service import get_audit_log, log_action
    session = get_session()
    try:
        log_action(
            session,
            action="TEST",
            entity_type="risk",
            entity_id="TEST-001",
            details="Unit test",
        )
        session.commit()

        logs = get_audit_log(session)
        assert len(logs) == 1
        assert logs[0]["action"] == "TEST"
        assert logs[0]["entity_type"] == "risk"
    finally:
        session.close()


def test_import_export_json():
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.import_export_service import export_json, import_json
    session = get_session()
    try:
        session.add(RiskRow(
            id="EXP-001", title="Export Test", category="Technical",
            likelihood=2, impact=3, risk_score=6, owner="Tester",
            status="Open", mitigation="None", asset="Test", target_date="2026-01-01",
        ))
        session.commit()

        json_str = export_json(session, "risks")
        data = json.loads(json_str)
        assert len(data) == 1
        assert data[0]["id"] == "EXP-001"

        # Import into a fresh session
        session.query(RiskRow).delete()
        session.commit()

        count = import_json(session, "risks", json_str)
        session.commit()
        assert count == 1
        assert session.query(RiskRow).count() == 1
    finally:
        session.close()


def test_export_csv():
    from cyberresilient.models.db_models import RiskRow
    from cyberresilient.services.import_export_service import export_csv
    session = get_session()
    try:
        session.add(RiskRow(
            id="CSV-001", title="CSV Test", category="Operational",
            likelihood=1, impact=2, risk_score=2, owner="Tester",
            status="Open", mitigation="None", asset="Test", target_date="2026-01-01",
        ))
        session.commit()

        csv_str = export_csv(session, "risks")
        assert "CSV-001" in csv_str
        assert "CSV Test" in csv_str
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
    finally:
        session.close()
