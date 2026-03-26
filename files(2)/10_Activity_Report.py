"""
pages/10_Activity_Report.py

User Activity Report — 90-day audit log summary.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from cyberresilient.services.activity_service import (
    generate_activity_report, get_recent_actions,
)
from cyberresilient.services.notification_service import build_digest, notify_all
from cyberresilient.services.auth_service import has_permission
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()
GOLD = colors["accent"]

st.markdown("# 📊 Activity Report & Notifications")
st.markdown("90-day user activity summary and GRC alert digest.")
st.markdown("---")

tab1, tab2 = st.tabs(["📋 Activity Report", "🔔 Alert Digest"])

with tab1:
    window = st.slider("Report Window (days)", 7, 90, 90)
    report = generate_activity_report(days=window)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Actions", report["total_actions"])
    m2.metric("Unique Users", report["unique_users"])
    m3.metric(
        "Period",
        f"{report['from_date']} → {report['to_date']}",
    )

    st.markdown("---")

    # Daily activity chart
    st.markdown("### Daily Activity")
    daily_df = pd.DataFrame(report["daily_activity"])
    if not daily_df.empty:
        fig = px.bar(
            daily_df, x="date", y="count",
            color="count",
            color_continuous_scale=["#1a3a1a", GOLD, "#F44336"],
            labels={"date": "Date", "count": "Actions"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", showlegend=False,
            xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Action type breakdown
    ac1, ac2 = st.columns(2)
    with ac1:
        st.markdown("### Actions by Type")
        if report["by_action_type"]:
            fig_at = px.pie(
                names=list(report["by_action_type"].keys()),
                values=list(report["by_action_type"].values()),
                hole=0.4,
            )
            fig_at.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA", height=280,
            )
            st.plotly_chart(fig_at, use_container_width=True)

    with ac2:
        st.markdown("### Actions by Entity Type")
        if report["by_entity_type"]:
            fig_et = px.bar(
                x=list(report["by_entity_type"].values()),
                y=list(report["by_entity_type"].keys()),
                orientation="h",
                color=list(report["by_entity_type"].values()),
                color_continuous_scale=["#1a3a1a", GOLD],
            )
            fig_et.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA", showlegend=False, height=280,
                xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
            )
            st.plotly_chart(fig_et, use_container_width=True)

    # Per-user breakdown
    st.markdown("### Per-User Activity")
    if report["by_user"]:
        user_df = pd.DataFrame(report["by_user"])[["user", "actions", "last_seen"]]
        user_df.columns = ["User", "Total Actions", "Last Seen"]
        st.dataframe(
            user_df.style.background_gradient(subset=["Total Actions"], cmap="YlOrRd"),
            use_container_width=True, hide_index=True,
        )

    # Most changed entities
    st.markdown("### Most Changed Records")
    if report["most_changed_entities"]:
        mce_df = pd.DataFrame(report["most_changed_entities"])
        mce_df.columns = ["Entity Type", "Entity ID", "Changes"]
        st.dataframe(mce_df, use_container_width=True, hide_index=True)

    # Recent raw actions
    with st.expander("🔍 Recent Audit Log Entries (last 50)"):
        recent = get_recent_actions(50)
        if recent:
            st.dataframe(
                pd.DataFrame(recent), use_container_width=True, hide_index=True,
            )
        else:
            st.info("No audit log entries found.")

    st.markdown("---")
    st.markdown("### 📥 Export")
    import json
    st.download_button(
        "📋 Download Activity Report (JSON)",
        data=json.dumps(report, indent=2, default=str),
        file_name=f"activity_report_{report['to_date']}.json",
        mime="application/json",
        use_container_width=True,
    )


with tab2:
    st.markdown("### 🔔 Current Alert Digest")
    st.markdown(
        "This is the same digest that gets sent via email/Slack by the "
        "scheduled GitHub Actions workflow."
    )

    digest = build_digest()

    dm1, dm2, dm3 = st.columns(3)
    dm1.metric("Total Alerts", digest["total_alerts"])
    dm2.metric("High Severity", digest["high_severity"])
    dm3.metric("Medium Severity", digest["medium_severity"])

    if not digest["total_alerts"]:
        st.success("✅ No alerts — all controls, risks, policies, CAPs, and vendors are current.")
    else:
        for alert in digest["alerts"]:
            sev_color = "#F44336" if alert["severity"] == "high" else "#FF9800"
            icon = "🔴" if alert["severity"] == "high" else "🟡"
            st.markdown(
                f"{icon} **{alert['type'].replace('_', ' ').title()}** — "
                f"{alert['message']} *(due: {alert['due']})*"
            )

    st.markdown("---")
    st.markdown("### 📤 Manual Send")
    if has_permission("admin"):
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("📧 Send Email Digest", use_container_width=True):
                from cyberresilient.services.notification_service import send_email_digest
                ok = send_email_digest(digest)
                st.success("Email sent!") if ok else st.error(
                    "Email failed — check SMTP_HOST, SMTP_USER, SMTP_PASS, NOTIFY_TO env vars."
                )
        with sc2:
            if st.button("💬 Send Slack Digest", use_container_width=True):
                from cyberresilient.services.notification_service import send_slack_digest
                ok = send_slack_digest(digest)
                st.success("Slack message sent!") if ok else st.error(
                    "Slack failed — check SLACK_WEBHOOK_URL env var."
                )
    else:
        st.info("Admin permission required to send notifications manually.")
