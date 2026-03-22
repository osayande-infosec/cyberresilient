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
from pathlib import Path

from cyberresilient.services.risk_service import (
    load_risks, build_heatmap_matrix, get_risk_summary,
    ARCHITECTURE_CHECKS, run_architecture_assessment,
    create_risk, update_risk, delete_risk, _db_available,
)
from cyberresilient.models.risk import (
    get_risk_level, get_risk_color,
    LIKELIHOOD_LABELS, IMPACT_LABELS,
)
from cyberresilient.services.report_service import generate_risk_report
from cyberresilient.services.auth_service import learning_callout, get_current_user, has_permission
from cyberresilient.services.learning_service import (
    get_content, learning_section, case_study_panel, try_this_panel, grc_insight,
)
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()
GOLD = colors["accent"]

lc = get_content("risk_register")

# ── Header ──────────────────────────────────────────────────
st.markdown("# ⚠️ Risk Register & Architecture Advisor")
st.markdown("Manage cybersecurity risks and assess vendor/solution security posture.")

learning_callout(
    "What is a Risk Register?",
    "A risk register is the central tool for tracking identified cybersecurity risks. "
    "Each risk is scored using a **Likelihood × Impact** matrix (typically 5×5), producing "
    "a risk score from 1–25. Risks are categorized as Low (1–4), Medium (5–9), High (10–15), "
    "or Very High (16–25). Risk owners are assigned to drive mitigation actions. "
    "This process aligns with ISO 31000 and NIST RMF (SP 800-37).",
)

# Heat map concepts (learning mode)
if lc.get("heat_map_guide"):
    hmg = lc["heat_map_guide"]
    learning_section(hmg["title"], hmg["content"], icon="🟩")
    from cyberresilient.services.auth_service import is_learning_mode
    if is_learning_mode() and "key_concepts" in hmg:
        with st.expander("📚 Key Risk Concepts", expanded=False):
            for concept in hmg["key_concepts"]:
                st.markdown(f"- {concept}")

# Case studies (learning mode)
if lc.get("case_studies"):
    case_study_panel(lc["case_studies"]["cases"])

# Guided exercises (learning mode)
if lc.get("try_this"):
    try_this_panel(lc["try_this"]["exercises"])

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Risk Register & Heat Map", "🏗️ Architecture Security Advisor", "✏️ Risk Management"])

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

    # Export buttons
    st.markdown("---")
    st.markdown("### 📥 Export Risk Register")
    ex1, ex2 = st.columns(2)
    with ex1:
        risk_json = json.dumps(risks, indent=2, default=str)
        st.download_button("📋 Download JSON", data=risk_json,
                          file_name="risk_register.json", mime="application/json",
                          use_container_width=True)
    with ex2:
        import csv, io
        buf = io.StringIO()
        if risks:
            writer = csv.DictWriter(buf, fieldnames=risks[0].keys())
            writer.writeheader()
            for r in risks:
                flat = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()}
                writer.writerow(flat)
        st.download_button("📊 Download CSV", data=buf.getvalue(),
                          file_name="risk_register.csv", mime="text/csv",
                          use_container_width=True)


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
        st.session_state["arch_assessment_result"] = assessment
        st.session_state["arch_vendor"] = vendor_name

    if "arch_assessment_result" in st.session_state:
        assessment = st.session_state["arch_assessment_result"]
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


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 3 — Risk Management (CRUD)                             ║
# ╚══════════════════════════════════════════════════════════════╝
with tab3:
    db_ok = _db_available()
    if not db_ok:
        st.warning("Database not initialised. Run `CyberResilient init --seed` to enable CRUD operations.")
    else:
        current_user = get_current_user()
        can_edit = has_permission("edit_risks")

        learning_callout(
            "Risk Management Workflow",
            "In practice, risks are identified during assessments, penetration tests, "
            "or incident reviews. Each risk is assigned a likelihood and impact score, "
            "an owner, and a mitigation plan. Risks are reviewed periodically (quarterly "
            "is common) and updated as controls are implemented or the threat landscape changes.",
        )

        # GRC insight (learning mode)
        if lc.get("grc_connection"):
            grc = lc["grc_connection"]
            grc_insight(grc["title"].replace("GRC Engineering: ", ""), grc["content"])

        st.markdown("### ➕ Add New Risk")
        with st.form("add_risk", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_title = st.text_input("Title *")
                new_category = st.selectbox("Category", [
                    "Malware / Ransomware", "Vulnerability Management",
                    "Third-Party / Supply Chain", "Insider Threat",
                    "Cloud Security", "Compliance / Regulatory",
                    "Physical Security", "Data Loss", "Other",
                ])
                new_likelihood = st.slider("Likelihood", 1, 5, 3)
                new_impact = st.slider("Impact", 1, 5, 3)
                st.info(f"Calculated Risk Score: **{new_likelihood * new_impact}** ({get_risk_level(new_likelihood * new_impact)})")
            with c2:
                new_owner = st.text_input("Owner *")
                new_status = st.selectbox("Status", ["Open", "Mitigating", "Monitoring", "Accepted", "Closed"])
                new_asset = st.text_input("Asset")
                new_target = st.date_input("Target Date")
                new_mitigation = st.text_area("Mitigation Plan")
                new_notes = st.text_area("Notes")

            add_submitted = st.form_submit_button("➕ Create Risk", type="primary", disabled=not can_edit)

        if add_submitted:
            if not new_title or not new_owner:
                st.error("Title and Owner are required.")
            else:
                risk_data = {
                    "title": new_title, "category": new_category,
                    "likelihood": new_likelihood, "impact": new_impact,
                    "owner": new_owner, "status": new_status,
                    "asset": new_asset, "target_date": str(new_target),
                    "mitigation": new_mitigation, "notes": new_notes,
                }
                result = create_risk(risk_data, user=current_user.username)
                st.success(f"Risk **{result['id']}** created successfully!")
                st.rerun()

        st.markdown("---")
        st.markdown("### ✏️ Edit / Delete Existing Risks")

        all_risks = load_risks()
        if all_risks:
            risk_options = {f"{r['id']} — {r['title']}": r["id"] for r in all_risks}
            selected_label = st.selectbox("Select risk to edit", list(risk_options.keys()))
            selected_id = risk_options[selected_label]
            sel_risk = next(r for r in all_risks if r["id"] == selected_id)

            with st.form("edit_risk"):
                e1, e2 = st.columns(2)
                with e1:
                    ed_title = st.text_input("Title", value=sel_risk["title"])
                    ed_category = st.text_input("Category", value=sel_risk["category"])
                    ed_likelihood = st.slider("Likelihood", 1, 5, sel_risk["likelihood"], key="ed_l")
                    ed_impact = st.slider("Impact", 1, 5, sel_risk["impact"], key="ed_i")
                    st.info(f"Calculated Risk Score: **{ed_likelihood * ed_impact}** ({get_risk_level(ed_likelihood * ed_impact)})")
                with e2:
                    ed_owner = st.text_input("Owner", value=sel_risk["owner"])
                    ed_status = st.selectbox("Status", ["Open", "Mitigating", "Monitoring", "Accepted", "Closed"],
                                             index=["Open", "Mitigating", "Monitoring", "Accepted", "Closed"].index(sel_risk["status"])
                                             if sel_risk["status"] in ["Open", "Mitigating", "Monitoring", "Accepted", "Closed"] else 0)
                    ed_asset = st.text_input("Asset", value=sel_risk.get("asset", ""))
                    ed_target = st.text_input("Target Date", value=sel_risk.get("target_date", ""))
                    ed_mitigation = st.text_area("Mitigation", value=sel_risk.get("mitigation", ""))
                    ed_notes = st.text_area("Notes", value=sel_risk.get("notes", ""))

                ec1, ec2 = st.columns(2)
                with ec1:
                    update_submitted = st.form_submit_button("💾 Update Risk", type="primary", disabled=not can_edit)
                with ec2:
                    delete_submitted = st.form_submit_button("🗑️ Delete Risk", disabled=not can_edit)

            if update_submitted:
                upd_data = {
                    "title": ed_title, "category": ed_category,
                    "likelihood": ed_likelihood, "impact": ed_impact,
                    "owner": ed_owner, "status": ed_status,
                    "asset": ed_asset, "target_date": ed_target,
                    "mitigation": ed_mitigation, "notes": ed_notes,
                }
                update_risk(selected_id, upd_data, user=current_user.username)
                st.success(f"Risk **{selected_id}** updated!")
                st.rerun()

            if delete_submitted:
                delete_risk(selected_id, user=current_user.username)
                st.success(f"Risk **{selected_id}** deleted.")
                st.rerun()
        else:
            st.info("No risks found. Add one above.")
