"""
Authentication and RBAC service.
Provides optional authentication with role-based access control.

Roles:
- admin: Full access, user management
- analyst: Full data access, run simulations, edit risks
- auditor: Read-only access, export data, view audit logs
- student: Read-only access with learning mode enabled by default
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import bcrypt
import streamlit as st
from sqlalchemy.orm import Session


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    STUDENT = "student"


# Permissions per role
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "view_dashboard", "view_dr", "view_ir", "view_risks", "view_compliance",
        "run_simulation", "edit_risks", "export_data", "import_data",
        "view_audit_log", "manage_users", "manage_settings",
    },
    "analyst": {
        "view_dashboard", "view_dr", "view_ir", "view_risks", "view_compliance",
        "run_simulation", "edit_risks", "export_data", "import_data",
    },
    "auditor": {
        "view_dashboard", "view_dr", "view_ir", "view_risks", "view_compliance",
        "export_data", "view_audit_log",
    },
    "student": {
        "view_dashboard", "view_dr", "view_ir", "view_risks", "view_compliance",
        "run_simulation",
    },
}


@dataclass
class CurrentUser:
    username: str
    name: str
    role: str
    is_authenticated: bool = True


def is_auth_enabled() -> bool:
    """Check if authentication is enabled via config or env."""
    import os
    return os.environ.get("CYBERRESILIENT_AUTH", "false").lower() == "true"


def get_current_user() -> CurrentUser | None:
    """Get the currently authenticated user from session state."""
    if not is_auth_enabled():
        return CurrentUser(
            username="anonymous",
            name="Anonymous User",
            role="admin",
        )
    return st.session_state.get("current_user")


def has_permission(permission: str) -> bool:
    """Check if the current user has a given permission."""
    user = get_current_user()
    if not user:
        return False
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def require_permission(permission: str) -> bool:
    """Check permission and show warning if denied. Returns True if allowed."""
    if has_permission(permission):
        return True
    st.warning("🔒 You do not have permission to access this feature.")
    return False


def authenticate(username: str, password: str) -> CurrentUser | None:
    """Authenticate user against the database. Returns CurrentUser or None."""
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import UserRow
    from cyberresilient.services.audit_service import log_action

    session = get_session()
    try:
        user = session.query(UserRow).filter_by(username=username, is_active=1).first()
        if not user:
            return None

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            log_action(
                session,
                action="LOGIN_FAILED",
                entity_type="user",
                entity_id=username,
                details="Invalid password",
            )
            session.commit()
            return None

        from datetime import datetime
        user.last_login = datetime.now()
        log_action(
            session,
            action="LOGIN",
            entity_type="user",
            entity_id=username,
            user=username,
        )
        session.commit()

        return CurrentUser(
            username=user.username,
            name=user.name,
            role=user.role,
        )
    finally:
        session.close()


def render_login_form() -> bool:
    """Render login form in sidebar. Returns True if authenticated."""
    if not is_auth_enabled():
        return True

    user = get_current_user()
    if user:
        return True

    st.sidebar.markdown("### 🔐 Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.error("Please enter username and password.")
                return False

            user = authenticate(username, password)
            if user:
                st.session_state["current_user"] = user
                st.rerun()
            else:
                st.error("Invalid username or password.")
                return False

    return False


def render_user_info() -> None:
    """Render current user info and logout button in sidebar."""
    user = get_current_user()
    if not user or not is_auth_enabled():
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{user.name}**")
    st.sidebar.caption(f"Role: {user.role.title()}")
    if st.sidebar.button("Logout"):
        st.session_state.pop("current_user", None)
        st.session_state.pop("learning_mode", None)
        st.rerun()


def render_learning_toggle() -> None:
    """Render learning mode toggle in sidebar."""
    user = get_current_user()
    if not user:
        return

    default_on = user.role == "student"
    current = st.session_state.get("learning_mode", default_on)
    new_val = st.sidebar.toggle("📚 Learning Mode", value=current)
    st.session_state["learning_mode"] = new_val


def is_learning_mode() -> bool:
    """Check if learning mode is currently active."""
    return st.session_state.get("learning_mode", False)


def learning_callout(title: str, content: str, icon: str = "💡") -> None:
    """Show an educational callout if learning mode is on."""
    if is_learning_mode():
        st.info(f"{icon} **{title}**\n\n{content}")
