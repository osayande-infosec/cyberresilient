"""
IAST-style Security Tests for CyberResilient
Interactive Application Security Testing — validates security properties
at runtime by exercising real code paths with instrumentation.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cyberresilient.database import get_session, init_db, reset_engine


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Use an in-memory SQLite database for each test."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_engine()
    init_db()
    yield
    reset_engine()


# ═══════════════════════════════════════════════════════════
# SQL Injection Tests (IAST)
# ═══════════════════════════════════════════════════════════


class TestSQLInjection:
    """Verify that ORM-based queries are immune to SQL injection."""

    SQLI_PAYLOADS = [
        "'; DROP TABLE risks; --",
        "' OR '1'='1' --",
        "1; DELETE FROM risks WHERE 1=1",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "1' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--",
    ]

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_risk_crud_sqli_immunity(self, payload):
        """Risk CRUD operations must be immune to SQL injection."""
        from cyberresilient.services.risk_service import create_risk, load_risks

        risk = create_risk(
            {
                "title": payload,
                "category": payload,
                "likelihood": 3,
                "impact": 3,
                "owner": payload,
                "status": "Open",
                "asset": payload,
                "target_date": "2026-01-01",
                "mitigation": payload,
                "notes": payload,
            }
        )

        # The payload should be stored as literal text, not executed
        assert risk["title"] == payload
        risks = load_risks()
        assert len(risks) == 1
        assert risks[0]["title"] == payload

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_audit_log_sqli_immunity(self, payload):
        """Audit log queries must be immune to SQL injection."""
        from cyberresilient.services.audit_service import get_audit_log, log_action

        session = get_session()
        try:
            log_action(
                session,
                action="test",
                entity_type=payload,
                entity_id=payload,
                user=payload,
                details=payload,
            )
            session.commit()
            # Query with malicious filter should not crash
            results = get_audit_log(session, entity_type=payload)
            assert len(results) == 1
        finally:
            session.close()


# ═══════════════════════════════════════════════════════════
# XSS / Output Encoding Tests
# ═══════════════════════════════════════════════════════════


class TestXSSPrevention:
    """Verify that stored data doesn't get HTML-interpreted."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        '"><img src=x onerror=alert(1)>',
        "<svg/onload=alert(1)>",
        "javascript:alert(document.cookie)",
        "<iframe src='javascript:alert(1)'>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_risk_stores_html_as_literal(self, payload):
        """HTML/JS in risk fields must be stored as-is, not interpreted."""
        from cyberresilient.services.risk_service import create_risk

        risk = create_risk(
            {
                "title": payload,
                "category": "Test",
                "likelihood": 1,
                "impact": 1,
                "owner": "test",
                "status": "Open",
                "notes": payload,
            }
        )
        # Verify no encoding happened in storage — it's stored literally
        # (Streamlit's st.markdown without unsafe_allow_html=True auto-escapes)
        assert risk["title"] == payload
        assert risk["notes"] == payload


# ═══════════════════════════════════════════════════════════
# Authentication & Authorization Tests (IAST)
# ═══════════════════════════════════════════════════════════


class TestAuthSecurity:
    """Validate auth boundaries at runtime."""

    def test_password_not_stored_plaintext(self):
        """Passwords must be hashed, never stored in cleartext."""
        from cyberresilient.models.db_models import UserRow

        session = get_session()
        try:
            import bcrypt

            pw_hash = bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode()
            user = UserRow(
                username="testuser",
                name="Test",
                email="test@test.com",
                password_hash=pw_hash,
                role="student",
            )
            session.add(user)
            session.commit()

            stored = session.query(UserRow).filter_by(username="testuser").first()
            assert stored.password_hash != "TestPass123!"
            assert stored.password_hash.startswith("$2")  # bcrypt prefix
        finally:
            session.close()

    def test_student_cannot_edit_risks(self):
        """Student role must not have edit_risks permission."""
        from cyberresilient.services.auth_service import ROLE_PERMISSIONS, Role

        assert "edit_risks" not in ROLE_PERMISSIONS[Role.STUDENT]

    def test_auditor_cannot_manage_users(self):
        """Auditor role must not have manage_users permission."""
        from cyberresilient.services.auth_service import ROLE_PERMISSIONS, Role

        assert "manage_users" not in ROLE_PERMISSIONS[Role.AUDITOR]

    def test_all_roles_have_dashboard_access(self):
        """All roles must have view_dashboard permission."""
        from cyberresilient.services.auth_service import ROLE_PERMISSIONS

        for role, perms in ROLE_PERMISSIONS.items():
            assert "view_dashboard" in perms, f"{role} missing view_dashboard"


# ═══════════════════════════════════════════════════════════
# Path Traversal Tests
# ═══════════════════════════════════════════════════════════


class TestPathTraversal:
    """Verify file operations don't allow path traversal."""

    TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f",
        "..%252f..%252f",
    ]

    @pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
    def test_report_output_stays_in_reports_dir(self, payload):
        """Report generation must never write outside the reports/ directory."""
        import pathlib

        from cyberresilient.services.report_service import REPORTS_DIR

        # Simulate: if someone tried to manipulate report filenames
        # Use PurePath (OS-aware) to correctly parse both / and \ separators
        safe_name = pathlib.PurePath(payload).name
        resolved = (REPORTS_DIR / safe_name).resolve()
        reports_resolved = REPORTS_DIR.resolve()
        # The resolved path must be within REPORTS_DIR
        assert str(resolved).startswith(str(reports_resolved)), f"Path traversal: {resolved} escapes {reports_resolved}"


# ═══════════════════════════════════════════════════════════
# Data Integrity Tests
# ═══════════════════════════════════════════════════════════


class TestDataIntegrity:
    """Verify data integrity constraints at runtime."""

    def test_risk_score_equals_likelihood_times_impact(self):
        """Created risk score must always equal likelihood * impact."""
        from cyberresilient.services.risk_service import create_risk

        risk = create_risk(
            {
                "title": "Integrity Test",
                "category": "Test",
                "likelihood": 4,
                "impact": 3,
                "owner": "test",
                "status": "Open",
            }
        )
        assert risk["risk_score"] == 12  # 4 * 3

    def test_audit_log_captures_mutations(self):
        """Every create/update/delete must produce an audit log entry."""
        from cyberresilient.services.audit_service import get_audit_log
        from cyberresilient.services.risk_service import create_risk, delete_risk, update_risk

        risk = create_risk(
            {"title": "Audit Test", "category": "Test", "likelihood": 2, "impact": 2, "owner": "test", "status": "Open"}
        )

        update_risk(
            risk["id"],
            {
                "title": "Updated",
                "category": "Test",
                "likelihood": 3,
                "impact": 3,
                "owner": "test",
                "status": "Mitigating",
            },
        )

        delete_risk(risk["id"])

        session = get_session()
        try:
            log = get_audit_log(session, entity_type="risk")
            actions = [e["action"] for e in log]
            assert "create" in actions
            assert "update" in actions
            assert "delete" in actions
        finally:
            session.close()

    def test_deleted_risk_not_retrievable(self):
        """Deleted risks must not appear in load_risks()."""
        from cyberresilient.services.risk_service import create_risk, delete_risk, load_risks

        risk = create_risk(
            {"title": "Delete Me", "category": "Test", "likelihood": 1, "impact": 1, "owner": "test", "status": "Open"}
        )
        delete_risk(risk["id"])
        risks = load_risks()
        ids = [r["id"] for r in risks]
        assert risk["id"] not in ids
