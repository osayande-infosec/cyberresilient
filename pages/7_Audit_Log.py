"""
Page 7 — Audit Log Viewer
Browse and filter the audit trail of all data mutations.
"""

import pandas as pd
import streamlit as st

from cyberresilient.services.auth_service import has_permission, learning_callout
from cyberresilient.services.learning_service import (
    audit_logging_principles,
    get_content,
    grc_insight,
    how_to_use_panel,
    learning_section,
    try_this_panel,
)
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()

st.markdown("# 📋 Audit Log")
st.markdown("Review the complete audit trail of system activity and data changes.")
st.markdown("---")

learning_callout(
    "Why Audit Logs Matter",
    "Audit logs provide a tamper-evident record of who did what, when. They are "
    "essential for compliance (NIST 800-53 AU family, ISO 27001 A.12.4), incident "
    "investigation, and insider threat detection. Enterprise audit logs should be "
    "centralized, immutable, and retained per your organization's policy (typically 1–7 years).",
)

lc = get_content("audit_log")

if lc.get("how_to_use"):
    hu = lc["how_to_use"]
    how_to_use_panel(hu["title"], hu["steps"])

# Audit logging best practices deep dive
if lc.get("deep_dive"):
    dd = lc["deep_dive"]
    learning_section(dd["title"], dd["content"], icon="📝")
    audit_logging_principles(dd.get("principles", []))

# GRC Engineering: Audit Trail as Foundation
if lc.get("grc_connection"):
    gc = lc["grc_connection"]
    grc_insight(gc["title"].replace("GRC Engineering: ", ""), gc["content"])

if lc.get("try_this"):
    try_this_panel(lc["try_this"]["exercises"])


def _load_audit():
    """Load audit log from DB if available."""
    try:
        from cyberresilient.database import get_session
        from cyberresilient.services.audit_service import get_audit_log

        session = get_session()
        try:
            return get_audit_log(session, limit=500)
        finally:
            session.close()
    except Exception:
        return []


if not has_permission("view_audit_log"):
    st.warning("You do not have permission to view the audit log.")
    st.stop()

# ── Filters ─────────────────────────────────────────────────
f1, f2, f3 = st.columns(3)
with f1:
    filter_action = st.multiselect(
        "Action",
        ["create", "update", "delete", "login", "seed"],
        default=["create", "update", "delete"],
    )
with f2:
    filter_entity = st.text_input("Entity Type (e.g., risk, system)", value="")
with f3:
    max_rows = st.number_input("Max Rows", min_value=10, max_value=500, value=100, step=10)

# ── Load & Filter ───────────────────────────────────────────
audit_data = _load_audit()

if not audit_data:
    st.info(
        "No audit log entries found. Initialise the database with `CyberResilient init --seed` to enable audit logging."
    )
    st.stop()

# Apply filters
filtered = audit_data
if filter_action:
    filter_action_lower = {a.lower() for a in filter_action}
    filtered = [e for e in filtered if e["action"].lower() in filter_action_lower]
if filter_entity:
    filtered = [e for e in filtered if filter_entity.lower() in e["entity_type"].lower()]
filtered = filtered[:max_rows]

# ── Summary Metrics ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Entries", len(audit_data))
m2.metric("Filtered", len(filtered))
m3.metric("Creates", sum(1 for e in audit_data if e["action"].lower() == "create"))
m4.metric("Deletes", sum(1 for e in audit_data if e["action"].lower() == "delete"))

st.markdown("---")

# ── Table ───────────────────────────────────────────────────
if filtered:
    df = pd.DataFrame(
        [
            {
                "Timestamp": e["timestamp"],
                "User": e["user"],
                "Action": e["action"].upper(),
                "Entity Type": e["entity_type"],
                "Entity ID": e["entity_id"],
                "Details": e.get("details", ""),
            }
            for e in filtered
        ]
    )

    def _color_action(val):
        colors_map = {
            "CREATE": "color: #4CAF50",
            "UPDATE": "color: #FFC107",
            "DELETE": "color: #F44336",
            "LOGIN": "color: #2196F3",
            "SEED": "color: #9C27B0",
        }
        return colors_map.get(val, "")

    st.dataframe(
        df.style.map(_color_action, subset=["Action"]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No entries match the current filters.")
