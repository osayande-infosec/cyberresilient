"""
Page 4 — Risk Register & Architecture Security Advisor
Interactive risk heat map, sortable risk register table,
and vendor/solution architecture security assessment form.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.risk_calculator import (
    load_risks, get_risk_level, get_risk_color,
    build_heatmap_matrix, get_risk_summary,
    ARCHITECTURE_CHECKS, run_architecture_assessment,
    LIKELIHOOD_LABELS, IMPACT_LABELS,
)
from utils.pdf_generator import generate_risk_report

st.set_page_config(page_title="Risk Register | DurhamResilient", page_icon="⚠️", layout="wide")

GOLD = "#C9A84C"

# ── Header ──────────────────────────────────────────────────
st.markdown("# ⚠️ Risk Register & Architecture Advisor")
st.markdown("Manage cybersecurity risks and assess vendor/solution security posture.")
st.markdown("---")

tab1, tab2 = st.tabs(["📊 Risk Register & Heat Map", "🏗️ Architecture Security Advisor"])

# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — Risk Register & Heat Map                           ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    risks = load_risks()
    summary = get_risk_summary(risks)

    # Summary metrics
    st.markdown("### Risk Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Risks", summary["total"])
    m2.metric("Very High", summary["by_level"]["Very High"], delta=None)
    m3.metric("High", summary["by_level"]["High"], delta=None)
    m4.metric("Medium + Low", summary["by_level"]["Medium"] + summary["by_level"]["Low"])

    st.markdown("---")

    # Heat Map
    hmap_col, detail_col = st.columns([1, 1])

    with hmap_col:
        st.markdown("### 5×5 Risk Heat Map")
        matrix = build_heatmap_matrix(risks)

        # Build annotation text
        annotations = []
        z_values = []
        for li in range(5):
            row = []
            for im in range(5):
                score = (li + 1) * (im + 1)
                count = matrix[li][im]
                row.append(score)
                annotations.append(
                    dict(
                        x=im, y=li,
                        text=f"{score}" + (f"\n({count} risks)" if count > 0 else ""),
                        showarrow=False,
                        font=dict(color="white" if score >= 10 else "#CCC", size=11),
                    )
                )
            z_values.append(row)

        fig_hmap = go.Figure(data=go.Heatmap(
            z=z_values,
            x=[IMPACT_LABELS[i] for i in range(1, 6)],
            y=[LIKELIHOOD_LABELS[i] for i in range(1, 6)],
            colorscale=[
                [0.0, "#1a3a1a"], [0.25, "#4CAF50"],
                [0.4, "#FFC107"], [0.6, "#FF9800"],
                [0.8, "#F44336"], [1.0, "#B71C1C"],
            ],
            showscale=False,
            hovertemplate="Likelihood: %{y}<br>Impact: %{x}<br>Score: %{z}<extra></extra>",
        ))
        fig_hmap.update_layout(
            annotations=annotations,
            xaxis_title="Impact →",
            yaxis_title="Likelihood →",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA",
            height=450,
            margin=dict(t=30, b=60, l=80, r=20),
        )
        st.plotly_chart(fig_hmap, use_container_width=True)

    with detail_col:
        st.markdown("### Risk Distribution")
        level_df = pd.DataFrame([
            {"Level": k, "Count": v, "Color": {"Very High": "#F44336", "High": "#FF9800", "Medium": "#FFC107", "Low": "#4CAF50"}[k]}
            for k, v in summary["by_level"].items() if v > 0
        ])
        if not level_df.empty:
            fig_dist = px.pie(
                level_df, names="Level", values="Count",
                color="Level",
                color_discrete_map={"Very High": "#F44336", "High": "#FF9800", "Medium": "#FFC107", "Low": "#4CAF50"},
                hole=0.4,
            )
            fig_dist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA", height=300,
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        # Status breakdown
        st.markdown("### By Status")
        for status, count in summary["by_status"].items():
            st.markdown(f"- **{status}:** {count}")

    st.markdown("---")

    # Risk Register Table
    st.markdown("### Detailed Risk Register")

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_level = st.multiselect("Filter by Level", ["Very High", "High", "Medium", "Low"], default=["Very High", "High", "Medium", "Low"])
    with fc2:
        filter_status = st.multiselect("Filter by Status", list(summary["by_status"].keys()), default=list(summary["by_status"].keys()))
    with fc3:
        sort_by = st.selectbox("Sort by", ["Risk Score (High→Low)", "Risk Score (Low→High)", "Target Date"])

    filtered = [
        r for r in risks
        if get_risk_level(r["risk_score"]) in filter_level and r["status"] in filter_status
    ]

    if sort_by == "Risk Score (High→Low)":
        filtered.sort(key=lambda x: x["risk_score"], reverse=True)
    elif sort_by == "Risk Score (Low→High)":
        filtered.sort(key=lambda x: x["risk_score"])
    else:
        filtered.sort(key=lambda x: x.get("target_date", "9999"))

    for r in filtered:
        level = get_risk_level(r["risk_score"])
        color = get_risk_color(r["risk_score"])
        icon = {"Very High": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(level, "⚪")

        with st.expander(f"{icon} {r['id']} — {r['title']} (Score: {r['risk_score']}, {level})"):
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown(f"**Category:** {r['category']}")
                st.markdown(f"**Likelihood:** {r['likelihood']}/5 ({LIKELIHOOD_LABELS[r['likelihood']]})")
                st.markdown(f"**Impact:** {r['impact']}/5 ({IMPACT_LABELS[r['impact']]})")
                st.markdown(f"**Status:** {r['status']}")
            with rc2:
                st.markdown(f"**Owner:** {r['owner']}")
                st.markdown(f"**Target Date:** {r['target_date']}")
                st.markdown(f"**Risk Score:** {r['risk_score']}")
            st.markdown(f"**Asset:** {r['asset']}")
            st.markdown(f"**Mitigation:** {r['mitigation']}")
            if r.get("notes"):
                st.markdown(f"**Notes:** {r['notes']}")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — Architecture Security Advisor                      ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### 🏗️ Architecture Security Assessment")
    st.markdown(
        "Evaluate a new vendor, solution, or architecture change against "
        "municipal security requirements. Complete the checklist below."
    )

    with st.form("arch_assessment"):
        vendor_name = st.text_input("Vendor / Solution Name", placeholder="e.g., Acme Cloud ERP v3.0")
        st.markdown("---")
        st.markdown("#### Security Control Checklist")

        answers = {}
        for check in ARCHITECTURE_CHECKS:
            answers[check["id"]] = st.checkbox(
                f"**{check['control']}** — {check['question']}",
                key=f"check_{check['id']}",
            )
            st.caption(f"Framework: {check['framework']}")

        submitted = st.form_submit_button("🔍 Run Assessment", type="primary")

    if submitted and vendor_name:
        assessment = run_architecture_assessment(answers)
        st.session_state["arch_assessment"] = assessment
        st.session_state["arch_vendor"] = vendor_name

    if "arch_assessment" in st.session_state:
        assessment = st.session_state["arch_assessment"]
        vendor = st.session_state["arch_vendor"]

        st.markdown("---")
        st.markdown(f"## Assessment Results: {vendor}")

        # Score gauge
        score = assessment["score_pct"]
        gauge_color = "#4CAF50" if score >= 70 else ("#FF9800" if score >= 50 else "#F44336")

        gc1, gc2 = st.columns([1, 2])
        with gc1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": "Security Score", "font": {"color": "#EAEAEA"}},
                number={"suffix": "%", "font": {"color": gauge_color}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": gauge_color},
                    "bgcolor": "#1A1A1A",
                    "steps": [
                        {"range": [0, 50], "color": "#3a1010"},
                        {"range": [50, 70], "color": "#3a3010"},
                        {"range": [70, 100], "color": "#103a10"},
                    ],
                },
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(t=60, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with gc2:
            am1, am2, am3 = st.columns(3)
            am1.metric("Passed", assessment["passed"])
            am2.metric("Failed", assessment["failed"])
            am3.metric("Overall Risk", assessment["overall_risk"])

        # Detailed results
        st.markdown("### Detailed Findings")
        for r in assessment["results"]:
            if r["passed"]:
                st.success(f"✅ **{r['control']}** — PASS")
            else:
                with st.expander(f"❌ **{r['control']}** — FAIL", expanded=True):
                    st.markdown(f"**Framework:** {r['framework']}")
                    st.error(f"**Risk:** {r['risk_if_missing']}")
                    st.info(f"**Recommendation:** {r['recommendation']}")

        # PDF Export
        st.markdown("---")
        if st.button("📥 Download Assessment Report (PDF)", type="primary"):
            filepath = generate_risk_report(assessment, vendor)
            with open(filepath, "rb") as f:
                st.download_button(
                    label="💾 Save PDF",
                    data=f.read(),
                    file_name=filepath.split("\\")[-1].split("/")[-1],
                    mime="application/pdf",
                )
            st.success("Report generated successfully!")
    elif submitted and not vendor_name:
        st.warning("Please enter a vendor/solution name.")
