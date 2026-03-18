"""
Page 1 — Executive Security Posture Dashboard
Real-time KPI cards, trend charts, department breakdown, and PDF export.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

st.set_page_config(page_title="Dashboard | DurhamShield", page_icon="📊", layout="wide")


@st.cache_data
def load_kpis():
    with open(DATA_DIR / "kpi_data.json") as f:
        return json.load(f)


data = load_kpis()
GOLD = "#C9A84C"
BG_CARD = "#1A1A1A"

# ── Header ──────────────────────────────────────────────────
st.markdown("# 📊 Executive Security Posture Dashboard")
st.markdown("Real-time cybersecurity metrics for the Region of Durham.")
st.markdown("---")

# ── Overall Score Gauge ─────────────────────────────────────
score = data["overall_security_score"]
gauge_col, summary_col = st.columns([1, 3])

with gauge_col:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Security Score", "font": {"color": "#EAEAEA", "size": 16}},
        number={"font": {"color": GOLD, "size": 40}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#555"},
            "bar": {"color": GOLD},
            "bgcolor": "#1A1A1A",
            "steps": [
                {"range": [0, 40], "color": "#3a1010"},
                {"range": [40, 70], "color": "#3a3010"},
                {"range": [70, 100], "color": "#103a10"},
            ],
            "threshold": {"line": {"color": "#F44336", "width": 2}, "value": 60},
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=250, margin=dict(t=60, b=10, l=30, r=30),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with summary_col:
    # KPI metric cards
    cols = st.columns(4)
    kpi_list = data["kpi_metrics"]
    for i, kpi in enumerate(kpi_list[:4]):
        with cols[i]:
            delta_val = kpi.get("trend", None)
            delta_str = f"{delta_val}" if delta_val else None
            st.metric(
                label=kpi["label"],
                value=f"{kpi['value']}{kpi.get('unit', '')}",
                delta=delta_str,
                delta_color="inverse" if kpi.get("lower_is_better", False) else "normal",
            )
    cols2 = st.columns(4)
    for i, kpi in enumerate(kpi_list[4:8]):
        with cols2[i]:
            delta_val = kpi.get("trend", None)
            delta_str = f"{delta_val}" if delta_val else None
            st.metric(
                label=kpi["label"],
                value=f"{kpi['value']}{kpi.get('unit', '')}",
                delta=delta_str,
                delta_color="inverse" if kpi.get("lower_is_better", False) else "normal",
            )

st.markdown("---")

# ── Charts Row 1 ───────────────────────────────────────────
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("Monthly Security Incidents (12-Month Trend)")
    incidents_df = pd.DataFrame(data["monthly_incidents"])
    fig_inc = px.bar(
        incidents_df, x="month", y="count",
        color="count",
        color_continuous_scale=["#103a10", GOLD, "#F44336"],
        labels={"month": "Month", "count": "Incidents"},
    )
    fig_inc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", showlegend=False,
        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
        height=350,
    )
    st.plotly_chart(fig_inc, use_container_width=True)

with chart2:
    st.subheader("Vulnerability Aging Distribution")
    vuln_df = pd.DataFrame(data["vulnerability_aging"])
    fig_vuln = px.pie(
        vuln_df, names="age_bucket", values="count",
        color_discrete_sequence=["#4CAF50", GOLD, "#FF9800", "#F44336"],
        hole=0.4,
    )
    fig_vuln.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=350,
    )
    st.plotly_chart(fig_vuln, use_container_width=True)

# ── Charts Row 2 ───────────────────────────────────────────
chart3, chart4 = st.columns(2)

with chart3:
    st.subheader("Compliance Trend (NIST CSF & ISO 27001)")
    comp_df = pd.DataFrame(data["compliance_trend"])
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=comp_df["quarter"], y=comp_df["nist_csf_pct"],
        name="NIST CSF", line=dict(color=GOLD, width=3),
        mode="lines+markers",
    ))
    fig_comp.add_trace(go.Scatter(
        x=comp_df["quarter"], y=comp_df["iso27001_pct"],
        name="ISO 27001", line=dict(color="#4CAF50", width=3),
        mode="lines+markers",
    ))
    fig_comp.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", yaxis_title="Compliance %",
        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222", range=[0, 100]),
        height=350, legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with chart4:
    st.subheader("Threat Categories")
    threat_df = pd.DataFrame(data["threat_categories"])
    fig_threat = px.bar(
        threat_df, x="count", y="category", orientation="h",
        color="severity",
        color_discrete_map={"Critical": "#F44336", "High": "#FF9800", "Medium": GOLD, "Low": "#4CAF50"},
        labels={"count": "Incidents", "category": ""},
    )
    fig_threat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=350,
        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_threat, use_container_width=True)

# ── Department Breakdown ────────────────────────────────────
st.markdown("---")
st.subheader("Department Security Metrics")

dept_data = data["department_metrics"]
dept_names = [d["department"] for d in dept_data]
selected_dept = st.selectbox("Filter by Department", ["All Departments"] + dept_names)

if selected_dept != "All Departments":
    dept_data = [d for d in dept_data if d["department"] == selected_dept]

dept_df = pd.DataFrame(dept_data)
dept_display = dept_df[["department", "risk_score", "compliance_pct", "open_incidents", "patch_compliance_pct"]].copy()
dept_display.columns = ["Department", "Risk Score", "Compliance %", "Open Incidents", "Patch Compliance %"]

st.dataframe(
    dept_display.style.background_gradient(subset=["Risk Score"], cmap="RdYlGn_r")
    .background_gradient(subset=["Compliance %"], cmap="RdYlGn")
    .background_gradient(subset=["Patch Compliance %"], cmap="RdYlGn"),
    use_container_width=True,
    hide_index=True,
)

# ── Department radar chart ──────────────────────────────────
if selected_dept == "All Departments":
    st.subheader("Department Risk Comparison")
    fig_radar = go.Figure()
    for d in data["department_metrics"]:
        fig_radar.add_trace(go.Scatterpolar(
            r=[d["risk_score"], d["compliance_pct"], d["patch_compliance_pct"],
               100 - d["open_incidents"] * 10, d.get("training_completion_pct", 80)],
            theta=["Risk Score", "Compliance", "Patch Compliance", "Incident Score", "Training"],
            fill="toself",
            name=d["department"],
            opacity=0.6,
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#333"),
            angularaxis=dict(gridcolor="#333"),
        ),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA",
        height=500, showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_radar, use_container_width=True)
