"""
Page 5 — Compliance & Policy Tracker
NIST CSF 2.0 mapping, ISO 27001 Annex A,
policy lifecycle management, and audit readiness score.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path

from cyberresilient.services.compliance_service import (
    load_controls, load_policies,
    calc_nist_csf_scores, calc_iso27001_scores, get_policy_summary,
)
from cyberresilient.config import get_config
from cyberresilient.services.auth_service import learning_callout, is_learning_mode
from cyberresilient.services.learning_service import (
    get_content, learning_section, grc_insight,
    compliance_comparison_table, evidence_types_panel,
    compliance_pipeline_panel, auditor_questions_panel,
    nist_function_detail,
)
from cyberresilient.theme import get_theme_colors

cfg = get_config()
colors = get_theme_colors()
GOLD = colors["accent"]
FUNC_COLORS = {
    "Govern": "#9C27B0",
    "Identify": "#2196F3",
    "Protect": "#4CAF50",
    "Detect": "#FF9800",
    "Respond": "#F44336",
    "Recover": GOLD,
}

# ── Header ──────────────────────────────────────────────────
st.markdown("# ✅ Compliance & Policy Tracker")
st.markdown("NIST CSF 2.0, ISO 27001:2022 compliance mapping and policy lifecycle management.")
st.markdown("---")

lc = get_content("compliance")

learning_callout(
    "Why Compliance Frameworks Matter",
    "Compliance frameworks like **NIST CSF** and **ISO 27001** provide structured "
    "approaches to managing cybersecurity risk. They are not checkbox exercises — "
    "they are engineering blueprints for building a defensible security program.",
)

# GRC Engineering manifesto (learning mode)
if lc.get("grc_engineering"):
    ge = lc["grc_engineering"]
    grc_insight(ge["title"].replace("The ", ""), ge["content"])
    compliance_comparison_table(ge.get("comparison", []))

# Evidence collection guide (learning mode)
if lc.get("evidence_collection"):
    ec = lc["evidence_collection"]
    learning_section(ec["title"], ec["content"], icon="🗂️")
    evidence_types_panel(ec.get("evidence_types", []))

# Compliance pipeline (learning mode)
if lc.get("compliance_tracking"):
    ct = lc["compliance_tracking"]
    learning_section(ct["title"], ct["content"], icon="🔄")
    compliance_pipeline_panel(ct.get("pipeline_stages", []))

# Auditor Q&A (learning mode)
if lc.get("audit_readiness"):
    ar = lc["audit_readiness"]
    learning_section(ar["title"], ar["content"], icon="🔍")
    auditor_questions_panel(ar.get("auditor_questions", []))

# ── Load Data ───────────────────────────────────────────────
controls_data = load_controls()
policies = load_policies()
nist_scores = calc_nist_csf_scores(controls_data)
iso_scores = calc_iso27001_scores(controls_data)
policy_summary = get_policy_summary(policies)

# ── Overall Metrics ─────────────────────────────────────────
st.markdown("### Compliance Overview")
ov1, ov2, ov3, ov4 = st.columns(4)
ov1.metric("NIST CSF 2.0", f"{nist_scores['overall_percentage']}%")
ov2.metric("ISO 27001:2022", f"{iso_scores['overall_percentage']}%")
ov3.metric("Policies Current", f"{policy_summary['current_pct']}%")
ov4.metric("Total Policies", policy_summary["total"])

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🏛️ NIST CSF 2.0", "📋 ISO 27001 & MFIPPA", "📄 Policy Lifecycle"])

# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — NIST CSF 2.0                                       ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown("### NIST Cybersecurity Framework v2.0 — Compliance Map")

    # Function-level bar chart
    func_names = list(nist_scores["functions"].keys())
    func_pcts = [nist_scores["functions"][f]["percentage"] for f in func_names]
    func_colors = [FUNC_COLORS.get(f, "#888") for f in func_names]

    fig_func = go.Figure()
    fig_func.add_trace(go.Bar(
        x=func_names, y=func_pcts,
        marker_color=func_colors,
        text=[f"{p}%" for p in func_pcts],
        textposition="outside",
    ))
    fig_func.add_hline(y=80, line_dash="dash", line_color=GOLD, annotation_text="Target: 80%")
    fig_func.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", yaxis_title="Compliance %",
        yaxis=dict(range=[0, 110], gridcolor="#222"),
        xaxis=dict(gridcolor="#222"),
        height=400, margin=dict(t=30),
    )
    st.plotly_chart(fig_func, use_container_width=True)

    # Detailed category breakdown
    st.markdown("### Category-Level Detail")

    # NIST CSF function deep dives (learning mode)
    nist_deep = lc.get("nist_csf_deep_dive", {})
    nist_functions = nist_deep.get("functions", {})

    for func_name, func_data in nist_scores["functions"].items():
        color = FUNC_COLORS.get(func_name, "#888")
        with st.expander(f"{func_name} — {func_data['description']} ({func_data['percentage']}%)"):
            for cat_name, cat_data in func_data["categories"].items():
                status = cat_data["status"]
                icon = {"Implemented": "✅", "Partial": "⚠️", "Gap": "❌"}.get(status, "❓")
                st.markdown(f"{icon} **{cat_name}** — {cat_data['name']}")
                st.markdown(f"   Status: **{status}** | Evidence: {cat_data.get('evidence', 'N/A')}")

            # Per-function learning deep dive
            if func_name in nist_functions:
                nist_function_detail(func_name, nist_functions[func_name])

    # Sunburst chart
    st.markdown("### NIST CSF Sunburst View")
    sunburst_data = {"ids": [], "labels": [], "parents": [], "values": [], "colors": []}
    sunburst_data["ids"].append("NIST CSF")
    sunburst_data["labels"].append("NIST CSF 2.0")
    sunburst_data["parents"].append("")
    sunburst_data["values"].append(nist_scores["total_controls"])
    sunburst_data["colors"].append("#333")

    for func_name, func_data in nist_scores["functions"].items():
        func_id = func_name
        sunburst_data["ids"].append(func_id)
        sunburst_data["labels"].append(f"{func_name}\n{func_data['percentage']}%")
        sunburst_data["parents"].append("NIST CSF")
        sunburst_data["values"].append(func_data["total_categories"])
        sunburst_data["colors"].append(FUNC_COLORS.get(func_name, "#888"))

        for cat_name, cat_data in func_data["categories"].items():
            cat_id = f"{func_name}/{cat_name}"
            status_color = {"Implemented": "#4CAF50", "Partial": "#FFC107", "Gap": "#F44336"}.get(cat_data["status"], "#888")
            sunburst_data["ids"].append(cat_id)
            sunburst_data["labels"].append(f"{cat_name}")
            sunburst_data["parents"].append(func_id)
            sunburst_data["values"].append(1)
            sunburst_data["colors"].append(status_color)

    fig_sun = go.Figure(go.Sunburst(
        ids=sunburst_data["ids"],
        labels=sunburst_data["labels"],
        parents=sunburst_data["parents"],
        values=sunburst_data["values"],
        marker=dict(colors=sunburst_data["colors"]),
        branchvalues="total",
    ))
    fig_sun.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA",
        height=600, margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig_sun, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — ISO 27001 & MFIPPA                                 ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### ISO 27001:2022 Annex A — Control Implementation")

    iso_df = pd.DataFrame(iso_scores["domains"])
    fig_iso = go.Figure()
    fig_iso.add_trace(go.Bar(
        name="Implemented",
        x=iso_df["name"], y=iso_df["implemented"],
        marker_color="#4CAF50",
    ))
    fig_iso.add_trace(go.Bar(
        name="Partial",
        x=iso_df["name"], y=iso_df["partial"],
        marker_color="#FFC107",
    ))
    fig_iso.add_trace(go.Bar(
        name="Gap",
        x=iso_df["name"], y=iso_df["total"] - iso_df["implemented"] - iso_df["partial"],
        marker_color="#F44336",
    ))
    fig_iso.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        yaxis_title="Controls", xaxis_title="",
        height=400,
        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_iso, use_container_width=True)

    # ISO domain table
    iso_df["percentage"] = ((iso_df["implemented"] + iso_df["partial"] * 0.5) / iso_df["total"] * 100).round(1)
    iso_display = iso_df[["name", "total", "implemented", "partial", "percentage"]].copy()
    iso_display.columns = ["Domain", "Total Controls", "Implemented", "Partial", "Score %"]
    st.dataframe(
        iso_display.style.background_gradient(subset=["Score %"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")

    # MFIPPA Section
    # Custom framework compliance (configurable per org)
    custom_fws = [fw for fw in cfg.compliance.custom_frameworks if fw.enabled]
    if custom_fws:
        for fw in custom_fws:
            st.markdown(f"### 🏛️ {fw.name} — {fw.full_name}")
    else:
        st.markdown("### 🏛️ Additional Regulatory Frameworks")
    st.markdown(f"""
    {cfg.organization.name} compliance requirements:
    """)

    mfippa_items = [
        {"requirement": "Privacy Impact Assessments (PIAs)", "status": "Implemented", "detail": "PIAs required for all new systems processing personal information"},
        {"requirement": "Access to Information Requests", "status": "Implemented", "detail": "30-day response window; tracked in FOIP management system"},
        {"requirement": "Privacy Breach Protocol", "status": "Implemented", "detail": "IPC notification at earliest opportunity; target < 72 hours"},
        {"requirement": "Data Minimization", "status": "Partial", "detail": "Policy in place; enforcement gaps in legacy systems"},
        {"requirement": "Retention & Disposal Schedules", "status": "Partial", "detail": "Schedules exist for most record types; OT data retention under review"},
        {"requirement": "Staff Privacy Training", "status": "Implemented", "detail": "Annual mandatory training with completion tracking"},
        {"requirement": "Third-Party Data Sharing Agreements", "status": "Partial", "detail": "Template agreements exist; not all vendors have current DSAs"},
    ]

    for item in mfippa_items:
        icon = {"Implemented": "✅", "Partial": "⚠️", "Gap": "❌"}.get(item["status"], "❓")
        st.markdown(f"{icon} **{item['requirement']}** — *{item['status']}*")
        st.caption(item["detail"])


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 3 — Policy Lifecycle                                   ║
# ╚══════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown("### 📄 Security Policy Lifecycle Management")

    # Policy status summary
    ps1, ps2, ps3, ps4 = st.columns(4)
    ps1.metric("Current", policy_summary["by_status"].get("Current", 0))
    ps2.metric("Under Review", policy_summary["by_status"].get("Under Review", 0))
    ps3.metric("Draft", policy_summary["by_status"].get("Draft", 0))
    ps4.metric("Expired", policy_summary["by_status"].get("Expired", 0))

    # Policy donut
    status_counts = {k: v for k, v in policy_summary["by_status"].items() if v > 0}
    fig_pol = px.pie(
        names=list(status_counts.keys()),
        values=list(status_counts.values()),
        color=list(status_counts.keys()),
        color_discrete_map={
            "Current": "#4CAF50", "Under Review": "#FFC107",
            "Draft": "#2196F3", "Expired": "#F44336",
        },
        hole=0.4,
    )
    fig_pol.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA",
        height=300,
    )
    st.plotly_chart(fig_pol, use_container_width=True)

    st.markdown("---")

    # Policy table
    st.markdown("### Policy Details")

    filter_status = st.multiselect(
        "Filter by Status",
        ["Current", "Under Review", "Draft", "Expired"],
        default=["Current", "Under Review", "Draft", "Expired"],
        key="policy_filter",
    )

    filtered_policies = [p for p in policies if p["status"] in filter_status]

    for p in filtered_policies:
        icon = {"Current": "✅", "Under Review": "🔄", "Draft": "📝", "Expired": "⛔"}.get(p["status"], "❓")
        with st.expander(f"{icon} {p['name']} — v{p['version']} ({p['status']})"):
            pc1, pc2 = st.columns(2)
            with pc1:
                st.markdown(f"**Owner:** {p['owner']}")
                st.markdown(f"**Approver:** {p['approved_by']}")
                st.markdown(f"**Version:** {p['version']}")
            with pc2:
                st.markdown(f"**Status:** {p['status']}")
                st.markdown(f"**Last Reviewed:** {p['last_reviewed']}")
                st.markdown(f"**Next Review:** {p['next_review']}")
            st.markdown(f"**Description:** {p['description']}")

    st.markdown("---")

    # Audit Readiness Score
    st.markdown("### 🎯 Audit Readiness Score")
    nist_pct = nist_scores["overall_percentage"]
    iso_pct = iso_scores["overall_percentage"]
    policy_pct = policy_summary["current_pct"]

    # Weighted composite
    audit_score = round(nist_pct * 0.4 + iso_pct * 0.35 + policy_pct * 0.25)

    fig_audit = go.Figure(go.Indicator(
        mode="gauge+number",
        value=audit_score,
        title={"text": "Audit Readiness", "font": {"color": "#EAEAEA", "size": 18}},
        number={"suffix": "%", "font": {"color": GOLD, "size": 48}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": GOLD},
            "bgcolor": "#1A1A1A",
            "steps": [
                {"range": [0, 40], "color": "#3a1010"},
                {"range": [40, 70], "color": "#3a3010"},
                {"range": [70, 100], "color": "#103a10"},
            ],
            "threshold": {"line": {"color": "#F44336", "width": 2}, "value": 70},
        },
    ))
    fig_audit.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", height=300, margin=dict(t=80, b=10),
    )
    st.plotly_chart(fig_audit, use_container_width=True)

    st.markdown(f"""
    | Component | Weight | Score |
    |---|---|---|
    | NIST CSF 2.0 | 40% | {nist_pct}% |
    | ISO 27001:2022 | 35% | {iso_pct}% |
    | Policy Currency | 25% | {policy_pct}% |
    | **Composite** | **100%** | **{audit_score}%** |
    """)

    if audit_score >= 80:
        st.success("✅ Strong audit readiness. Maintain current trajectory.")
    elif audit_score >= 60:
        st.warning("⚠️ Moderate readiness. Address gaps in NIST CSF and policy reviews before next audit cycle.")
    else:
        st.error("❌ Significant gaps. Prioritize compliance remediation immediately.")

# ── Export Section ──────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 Export Compliance Data")
ce1, ce2 = st.columns(2)
with ce1:
    import json as _json
    policy_json = _json.dumps([p.__dict__ if hasattr(p, '__dict__') else p for p in policies], indent=2, default=str)
    st.download_button("📋 Policies JSON", data=policy_json,
                      file_name="policies_export.json", mime="application/json",
                      use_container_width=True)
with ce2:
    nist_json = _json.dumps(controls_data, indent=2, default=str)
    st.download_button("📋 NIST CSF Controls JSON", data=nist_json,
                      file_name="nist_csf_controls.json", mime="application/json",
                      use_container_width=True)
