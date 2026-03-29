"""Tests for auth service."""

from cyberresilient.services.auth_service import (
    ROLE_PERMISSIONS,
    Role,
    is_auth_enabled,
)


def test_roles_defined():
    assert "admin" in ROLE_PERMISSIONS
    assert "analyst" in ROLE_PERMISSIONS
    assert "auditor" in ROLE_PERMISSIONS
    assert "student" in ROLE_PERMISSIONS


def test_admin_has_all_permissions():
    admin_perms = ROLE_PERMISSIONS["admin"]
    assert "manage_users" in admin_perms
    assert "view_dashboard" in admin_perms
    assert "export_data" in admin_perms
    assert "import_data" in admin_perms


def test_student_cannot_manage_users():
    student_perms = ROLE_PERMISSIONS["student"]
    assert "manage_users" not in student_perms
    assert "edit_risks" not in student_perms
    assert "view_dashboard" in student_perms


def test_auditor_has_read_and_export():
    auditor_perms = ROLE_PERMISSIONS["auditor"]
    assert "view_dashboard" in auditor_perms
    assert "export_data" in auditor_perms
    assert "view_audit_log" in auditor_perms
    assert "edit_risks" not in auditor_perms
    assert "import_data" not in auditor_perms


def test_auth_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CYBERRESILIENT_AUTH", raising=False)
    assert not is_auth_enabled()


def test_auth_enabled_via_env(monkeypatch):
    monkeypatch.setenv("CYBERRESILIENT_AUTH", "true")
    assert is_auth_enabled()


def test_role_enum_values():
    assert Role.ADMIN == "admin"
    assert Role.STUDENT == "student"
