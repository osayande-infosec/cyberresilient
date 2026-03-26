"""
pages/8_CAP_Tracker.py

Corrective Action Plan Tracker
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date

from cyberresilient.services.cap_service import (
    create_cap, update_cap_status, load_caps, cap_summary,
    CAP_STATUSES, CAP_PRIORITIES, PRIORITY_COLORS, STATUS_ICONS,
)
from cyberresilient.services.auth_service import get_current_user, has_permission
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()
GOLD = colors["accent"]

st.markdown("# 📋 Corrective Action Plan Tracker")
st.markdown(
    "Track remediation actions raised from control test failures and compliance gaps."
)
st.markdown("---")

summary = cap_summary()
today = date.today().isoformat()

# ── Summary metrics ──────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total CAPs", summary["total"])
m2.metric("Open", summary["by_status"].get("Open", 0))
m3.metric("In Progress", summary["by_status"].get("In Progress", 0))
m4.metric("Overdue", summary["overdue"],
          delta=f"-{summary['overdue']}" if summary["overdue"] else None,
          delta_color="inverse")

if summary["overdue"]:
    st.error(f"🚨 {summary['overdue']} CAP(s) are past their target date and not closed.")

st.markdown("---")

tab1, tab2 = st.tabs(["📋 CAP Register", "➕ Raise New CAP"])

with tab1:
    filter_status = st.multiselect(
        "Filter by Status", CAP_STATUSES, default=CAP_STATUSES,
    )
    filter_priority = st.multiselect(
        "Filter by Priority", CAP_PRIORITIES, default=CAP_PRIORITIES,
    )

    caps = load_caps(status_filter=filter_status)
    caps = [c for c in caps if c["priority"] in filter_priority]

    if not caps:
        st.info("No CAPs found for the selected filters.")
    else:
        for cap in caps:
            is_overdue = cap["status"] != "Closed" and cap["target_date"] < today
            icon = STATUS_ICONS.get(cap["status"], "❓")
            overdue_flag = " ⏰ OVERDUE" if is_overdue else ""
            p_color = PRIORITY_COLORS.get(cap["priority"], "#888")

            with st.expander(
                f"{icon} [{cap['priority']}] {cap['title']} — {cap['status']}{overdue_flag}"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Owner:** {cap['owner']}")
                    st.markdown(f"**Priority:** "
                                f"<span style='color:{p_color}'>{cap['priority']}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"**Target Date:** {cap['target_date']}")
                    if cap.get("linked_control_id"):
                        st.markdown(f"**Linked Control:** `{cap['linked_control_id']}`")
                    if cap.get("linked_risk_id"):
                        st.markdown(f"**Linked Risk:** `{cap['linked_risk_id']}`")
                with c2:
                    st.markdown(f"**Status:** {cap['status']}")
                    st.markdown(f"**Created:** {cap['created_at']} by {cap['created_by']}")
                    if cap.get("closed_at"):
                        st.markdown(f"**Closed:** {cap['closed_at']}")

                st.markdown(f"**Description:** {cap['description']}")
                if cap.get("resolution_notes"):
                    st.markdown(f"**Resolution:** {cap['resolution_notes']}")

                if cap["status"] != "Closed" and has_permission("edit_risks"):
                    st.markdown("**Update Status**")
                    new_status = st.selectbox(
                        "New Status", CAP_STATUSES,
                        index=CAP_STATUSES.index(cap["status"]),
                        key=f"status_{cap['id']}",
                    )
                    res_notes = st.text_area(
                        "Resolution Notes (required to close)",
                        key=f"notes_{cap['id']}",
                    )
                    if st.button("Update", key=f"upd_{cap['id']}"):
                        try:
                            update_cap_status(
                                cap["id"], new_status, res_notes,
                                updated_by=get_current_user().username,
                            )
                            st.success("CAP updated.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

with tab2:
    if not has_permission("edit_risks"):
        st.warning("You do not have permission to raise CAPs.")
    else:
        with st.form("new_cap"):
            title = st.text_input("Title *")
            description = st.text_area("Description *")
            c1, c2 = st.columns(2)
            with c1:
                owner = st.text_input("Owner *")
                priority = st.selectbox("Priority", CAP_PRIORITIES)
                target_date = st.date_input("Target Date")
            with c2:
                linked_control = st.text_input(
                    "Linked Control ID",
                    help="e.g. DE.CM-1 — the control that failed",
                )
                linked_risk = st.text_input(
                    "Linked Risk ID",
                    help="e.g. RISK-042 — the risk this remediates",
                )

            submitted = st.form_submit_button("➕ Raise CAP", type="primary")

        if submitted:
            if not title or not description or not owner:
                st.error("Title, Description and Owner are required.")
            else:
                try:
                    cap = create_cap(
                        title=title,
                        description=description,
                        owner=owner,
                        target_date=str(target_date),
                        priority=priority,
                        linked_control_id=linked_control,
                        linked_risk_id=linked_risk,
                        created_by=get_current_user().username,
                    )
                    st.success(f"CAP raised: {cap['id']}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
