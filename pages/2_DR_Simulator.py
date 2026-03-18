"""
Page 2 — DR/BC Simulator & Tester
Interactive disaster recovery simulation with RTO/RPO analysis,
recovery step walkthrough, RACI matrix, and PDF report export.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dr_simulator import load_systems, load_scenarios, simulate_dr, generate_raci
from utils.pdf_generator import generate_dr_report

st.set_page_config(page_title="DR Simulator | DurhamResilient", page_icon="🔄", layout="wide")

GOLD = "#C9A84C"

# ── Header ──────────────────────────────────────────────────
st.markdown("# 🔄 Disaster Recovery / Business Continuity Simulator")
st.markdown("Test your recovery readiness against realistic threat scenarios.")
st.markdown("---")

# ── Load Data ───────────────────────────────────────────────
systems = load_systems()
scenarios = load_scenarios()

# ── Sidebar Controls ────────────────────────────────────────
with st.sidebar:
    st.markdown("### Simulation Parameters")
    system_names = {s["name"]: s for s in systems}
    selected_system_name = st.selectbox("Select System", list(system_names.keys()))
    selected_system = system_names[selected_system_name]

    scenario_names = {s["name"]: s for s in scenarios}
    selected_scenario_name = st.selectbox("Select Scenario", list(scenario_names.keys()))
    selected_scenario = scenario_names[selected_scenario_name]

    run_sim = st.button("🚀 Run Simulation", use_container_width=True, type="primary")

# ── System & Scenario Info ──────────────────────────────────
info1, info2 = st.columns(2)

with info1:
    st.markdown("### 🖥️ System Profile")
    st.markdown(f"**{selected_system['name']}** (`{selected_system['id']}`)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tier", selected_system["tier"])
    c2.metric("RTO Target", f"{selected_system['rto_target_hours']}h")
    c3.metric("RPO Target", f"{selected_system['rpo_target_hours']}h")
    st.markdown(f"**Type:** {selected_system['type']} | **DR Strategy:** {selected_system['current_dr_strategy']}")
    st.markdown(f"**Department:** {selected_system['department']}")
    st.markdown(f"**Dependencies:** {', '.join(selected_system.get('dependencies', ['None']))}")
    st.markdown(f"**Last DR Test:** {selected_system.get('last_test_date', 'N/A')} — *{selected_system.get('last_test_result', 'N/A')}*")

with info2:
    st.markdown("### ⚡ Scenario Profile")
    st.markdown(f"**{selected_scenario['name']}**")
    severity_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(selected_scenario["severity"], "⚪")
    st.markdown(f"**Severity:** {severity_color} {selected_scenario['severity']}")
    st.markdown(f"**Type:** {selected_scenario['type']}")
    st.markdown(f"**Description:** {selected_scenario['description']}")
    st.markdown(f"**Departments Affected:** {', '.join(selected_scenario['impact']['departments_affected'])}")
    st.markdown(f"**RTO Multiplier:** {selected_scenario['rto_impact_multiplier']}x | **RPO Multiplier:** {selected_scenario['rpo_impact_multiplier']}x")

st.markdown("---")

# ── Simulation Results ──────────────────────────────────────
if run_sim:
    with st.spinner("Running DR simulation..."):
        result = simulate_dr(selected_system, selected_scenario)
        raci = generate_raci(selected_system, selected_scenario)

    # Store in session state
    st.session_state["dr_result"] = result
    st.session_state["dr_raci"] = raci

if "dr_result" in st.session_state:
    result = st.session_state["dr_result"]
    raci = st.session_state["dr_raci"]

    st.markdown("## 📋 Simulation Results")

    # Overall status
    if result["overall_pass"]:
        st.success("✅ SIMULATION PASSED — All RTO/RPO targets met.")
    else:
        st.error("❌ SIMULATION FAILED — One or more targets exceeded.")

    # RTO/RPO gauges
    g1, g2 = st.columns(2)

    with g1:
        rto_color = "#4CAF50" if result["rto_met"] else "#F44336"
        fig_rto = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=result["rto_estimated_hours"],
            title={"text": "RTO (Recovery Time)", "font": {"color": "#EAEAEA"}},
            number={"suffix": "h", "font": {"color": rto_color}},
            delta={"reference": result["rto_target_hours"], "relative": False, "increasing": {"color": "#F44336"}, "decreasing": {"color": "#4CAF50"}},
            gauge={
                "axis": {"range": [0, max(result["rto_estimated_hours"], result["rto_target_hours"]) * 1.5]},
                "bar": {"color": rto_color},
                "bgcolor": "#1A1A1A",
                "threshold": {"line": {"color": GOLD, "width": 3}, "value": result["rto_target_hours"]},
            },
        ))
        fig_rto.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(t=80, b=10))
        st.plotly_chart(fig_rto, use_container_width=True)
        st.markdown(f"**Target:** {result['rto_target_hours']}h | **Estimated:** {result['rto_estimated_hours']}h | **Gap:** {result['rto_gap_hours']}h")

    with g2:
        rpo_color = "#4CAF50" if result["rpo_met"] else "#F44336"
        fig_rpo = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=result["rpo_estimated_hours"],
            title={"text": "RPO (Recovery Point)", "font": {"color": "#EAEAEA"}},
            number={"suffix": "h", "font": {"color": rpo_color}},
            delta={"reference": result["rpo_target_hours"], "relative": False, "increasing": {"color": "#F44336"}, "decreasing": {"color": "#4CAF50"}},
            gauge={
                "axis": {"range": [0, max(result["rpo_estimated_hours"], result["rpo_target_hours"]) * 1.5]},
                "bar": {"color": rpo_color},
                "bgcolor": "#1A1A1A",
                "threshold": {"line": {"color": GOLD, "width": 3}, "value": result["rpo_target_hours"]},
            },
        ))
        fig_rpo.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(t=80, b=10))
        st.plotly_chart(fig_rpo, use_container_width=True)
        st.markdown(f"**Target:** {result['rpo_target_hours']}h | **Estimated:** {result['rpo_estimated_hours']}h | **Gap:** {result['rpo_gap_hours']}h")

    st.markdown("---")

    # Recovery Steps
    st.markdown("### 🔧 Recovery Steps")
    for i, step in enumerate(result["recovery_steps"], 1):
        st.checkbox(step, key=f"step_{i}", value=False)

    st.markdown("---")

    # Recommendations
    st.markdown("### 💡 Recommendations")
    for rec in result["recommendations"]:
        st.markdown(f"- {rec}")

    st.markdown("---")

    # RACI Matrix
    st.markdown("### 📊 RACI Matrix — DR Activation")
    raci_df = pd.DataFrame(raci)
    raci_df.columns = ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]
    st.dataframe(raci_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # PDF Export
    st.markdown("### 📄 Export Report")
    if st.button("📥 Download DR Simulation Report (PDF)", type="primary"):
        filepath = generate_dr_report(result, raci)
        with open(filepath, "rb") as f:
            st.download_button(
                label="💾 Save PDF",
                data=f.read(),
                file_name=filepath.split("\\")[-1].split("/")[-1],
                mime="application/pdf",
            )
        st.success(f"Report generated successfully!")
else:
    st.info("👈 Select a system and scenario, then click **Run Simulation** to begin.")
