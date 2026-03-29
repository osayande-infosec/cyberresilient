"""
Page 5 — Compliance & Policy Tracker
NIST CSF 2.0 mapping, ISO 27001 Annex A,
policy lifecycle management, and audit readiness score.

v2: Surfaces evidence staleness, dependency breaches, compensating controls,
7-level lifecycle states, and policy expiry proximity alerts.
"""

import json as _json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from cyberresilient.config import get_config
from cyberresilient.services.auth_service import learning_callout
from cyberresilient.services.compliance_service import (
    LIFECYCLE_WEIGHTS,
    calc_iso27001_scores,
    calc_nist_csf_scores,
    get_policy_summary,
    load_controls,
    load_policies,
)
from cyberresilient.services.learning_service import (
    auditor_questions_panel,
    compliance_comparison_table,
    compliance_pipeline_panel,
    evidence_types_panel,
    get_content,
    grc_insight,
    learning_section,
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

# 7-level lifecycle → icon + colour
LIFECYCLE_META = {
    "Implemented": {"icon": "✅", "color": "#4CAF50"},
    "Compensating": {"icon": "🔄", "color": "#8BC34A"},
    "Largely": {"icon": "⚡", "color": "#CDDC39"},
    "Partial": {"icon": "⚠️", "color": "#FFC107"},
    "Planned": {"icon": "📅", "color": "#2196F3"},
    "Not Implemented": {"icon": "❌", "color": "#F44336"},
    "Gap": {"icon": "❌", "color": "#F44336"},  # legacy alias
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
    "they are engineering blueprints for building a defensible security program. "
    "Scores here reflect evidence quality and control dependencies, not just status.",
)

if lc.get("grc_engineering"):
    ge = lc["grc_engineering"]
    grc_insight(ge["title"].replace("The ", ""), ge["content"])
    compliance_comparison_table(ge.get("comparison", []))

if lc.get("evidence_collection"):
    ec = lc["evidence_collection"]
    learning_section(ec["title"], ec["content"], icon="🗂️")
    evidence_types_panel(ec.get("evidence_types", []))

if lc.get("compliance_tracking"):
    ct = lc["compliance_tracking"]
    learning_section(ct["title"], ct["content"], icon="🔄")
    compliance_pipeline_panel(ct.get("pipeline_stages", []))

if lc.get("audit_readiness"):
    ar = lc["audit_readiness"]
    learning_section(ar["title"], ar["content"], icon="🔍")
    auditor_questions_panel(ar.get("auditor_questions", []))

# ── Load & Score ─────────────────────────────────────────────
controls_data = load_controls()
policies = load_policies()
nist_scores = calc_nist_csf_scores(controls_data)
iso_scores = calc_iso27001_scores(controls_data)
policy_summary = get_policy_summary(policies)

# ── Platform-wide alert strip ───────────────────────────────
total_stale = nist_scores.get("stale_evidence_count", 0)
dep_breaches = nist_scores.get("dependency_breach_count", 0)
compensating = nist_scores.get("compensating_count", 0)
expiring_soon = policy_summary.get("expiring_soon", [])

if total_stale or dep_breaches or expiring_soon:
    with st.container():
        if total_stale:
            st.warning(
                f"🗂️ **{total_stale} NIST CSF control(s)** have stale or missing evidence "
                f"(>365 days). Effective scores are capped at 50% until evidence is refreshed."
            )
        if dep_breaches:
            st.warning(
                f"🔗 **{dep_breaches} control(s)** are capped by unmet prerequisite controls. "
                "Expand the Category Detail below to see which prerequisites are blocking."
            )
        if compensating:
            st.info(
                f"🔄 **{compensating} control(s)** are currently satisfied by compensating "
                "controls. These are credited at 85% — verify with your auditor."
            )
        if expiring_soon:
            names = ", ".join(p["name"] for p in expiring_soon[:3])
            more = f" (+{len(expiring_soon) - 3} more)" if len(expiring_soon) > 3 else ""
            st.error(
                f"📋 **{len(expiring_soon)} policy/policies expiring within 30 days:** "
                f"{names}{more}. Review the Policy Lifecycle tab."
            )

# ── Overall Metrics ─────────────────────────────────────────
st.markdown("### Compliance Overview")
ov1, ov2, ov3, ov4, ov5 = st.columns(5)
ov1.metric("NIST CSF 2.0", f"{nist_scores['overall_percentage']}%")
ov2.metric("ISO 27001:2022", f"{iso_scores['overall_percentage']}%")
ov3.metric("Policies Current", f"{policy_summary['current_pct']}%")
ov4.metric("Stale Evidence (NIST)", total_stale)
ov5.metric("ISO Stale Domains", iso_scores.get("stale_evidence_domains", 0))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    [
        "🏛️ NIST CSF 2.0",
        "📋 ISO 27001 & MFIPPA",
        "📄 Policy Lifecycle",
    ]
)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — NIST CSF 2.0                                       ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown("### NIST Cybersecurity Framework v2.0 — Compliance Map")

    func_names = list(nist_scores["functions"].keys())
    func_pcts = [nist_scores["functions"][f]["percentage"] for f in func_names]
    func_colors_list = [FUNC_COLORS.get(f, "#888") for f in func_names]

    fig_func = go.Figure()
    fig_func.add_trace(
        go.Bar(
            x=func_names,
            y=func_pcts,
            marker_color=func_colors_list,
            text=[f"{p}%" for p in func_pcts],
            textposition="outside",
        )
    )
    fig_func.add_hline(
        y=80,
        line_dash="dash",
        line_color=GOLD,
        annotation_text="Target: 80%",
    )
    fig_func.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        yaxis_title="Compliance %",
        yaxis={"range": [0, 115], "gridcolor": "#222"},
        xaxis={"gridcolor": "#222"},
        height=400,
        margin={"t": 30},
    )
    st.plotly_chart(fig_func, use_container_width=True)

    # ── 7-level lifecycle legend ─────────────────────────────
    st.markdown("#### Control Status Legend")
    leg_cols = st.columns(len(LIFECYCLE_WEIGHTS))
    for idx, (status, weight) in enumerate(LIFECYCLE_WEIGHTS.items()):
        meta = LIFECYCLE_META.get(status, {"icon": "❓", "color": "#888"})
        with leg_cols[idx]:
            st.markdown(
                f"<div style='text-align:center;background:{meta['color']}22;"
                f"border:1px solid {meta['color']};border-radius:6px;padding:6px 2px'>"
                f"<span style='font-size:18px'>{meta['icon']}</span><br>"
                f"<span style='font-size:11px;color:{meta['color']};font-weight:600'>"
                f"{status}</span><br>"
                f"<span style='font-size:10px;color:#aaa'>{int(weight * 100)}% weight</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### Category-Level Detail")

    nist_deep = lc.get("nist_csf_deep_dive", {})
    nist_functions = nist_deep.get("functions", {})

    for func_name, func_data in nist_scores["functions"].items():
        func_color = FUNC_COLORS.get(func_name, "#888")
        stale_in_func = sum(1 for cd in func_data.get("control_details", []) if cd["evidence_status"]["stale"])
        dep_in_func = sum(
            1 for cd in func_data.get("control_details", []) if any("Prerequisite" in n for n in cd.get("notes", []))
        )

        func_label = (
            f"{func_name} — {func_data['description']} "
            f"({func_data['percentage']}%)"
            + (f" 🗂️ {stale_in_func} stale" if stale_in_func else "")
            + (f" 🔗 {dep_in_func} capped" if dep_in_func else "")
        )

        with st.expander(func_label):
            control_details = func_data.get("control_details", [])

            if control_details:
                for cd in control_details:
                    status = cd["status"]
                    meta = LIFECYCLE_META.get(status, {"icon": "❓", "color": "#888"})
                    eff_weight = cd["effective_weight"]
                    ev_status = cd["evidence_status"]
                    notes = cd.get("notes", [])

                    # Control header row
                    c_col1, c_col2, c_col3 = st.columns([3, 1, 1])
                    with c_col1:
                        st.markdown(f"{meta['icon']} **{cd['id']}** — {cd['name']}")
                    with c_col2:
                        st.markdown(
                            f"<span style='color:{meta['color']};font-weight:600'>{status}</span>",
                            unsafe_allow_html=True,
                        )
                    with c_col3:
                        weight_color = "#4CAF50" if eff_weight >= 0.8 else "#FFC107" if eff_weight >= 0.4 else "#F44336"
                        st.markdown(
                            f"<span style='color:{weight_color};font-size:12px'>"
                            f"Effective: {int(eff_weight * 100)}%</span>",
                            unsafe_allow_html=True,
                        )

                    # Evidence status
                    if ev_status["stale"]:
                        if ev_status.get("days_overdue"):
                            st.caption(
                                f"   🗂️ Evidence overdue by {ev_status['days_overdue']} days"
                                f" — collected {cd.get('evidence_date', 'never')}"
                            )
                        else:
                            st.caption("   🗂️ No evidence date recorded")
                    elif ev_status.get("days_remaining") and ev_status["days_remaining"] <= 90:
                        st.caption(f"   🗂️ Evidence expires in {ev_status['days_remaining']} days")

                    # Advisory notes (dependency caps, compensating uplifts)
                    for note in notes:
                        if "Prerequisite" in note:
                            st.caption(f"   🔗 {note}")
                        elif "Compensated" in note:
                            st.caption(f"   🔄 {note}")
                        else:
                            st.caption(f"   ℹ️ {note}")

                    st.divider()
            else:
                # Fallback to legacy category dict rendering
                for cat_name, cat_data in func_data["categories"].items():
                    status = cat_data.get("status", "Not Implemented")
                    meta = LIFECYCLE_META.get(status, {"icon": "❓", "color": "#888"})
                    st.markdown(
                        f"{meta['icon']} **{cat_name}** — {cat_data.get('name', '')}  "
                        f"| Status: **{status}** | Evidence: {cat_data.get('evidence', 'N/A')}"
                    )

            if func_name in nist_functions:
                nist_function_detail(func_name, nist_functions[func_name])

    # ── Sunburst (coloured by effective weight tier) ─────────
    st.markdown("### NIST CSF Sunburst View")
    sunburst_data = {
        "ids": [],
        "labels": [],
        "parents": [],
        "values": [],
        "colors": [],
    }
    sunburst_data["ids"].append("NIST CSF")
    sunburst_data["labels"].append("NIST CSF 2.0")
    sunburst_data["parents"].append("")
    sunburst_data["values"].append(nist_scores["total_controls"])
    sunburst_data["colors"].append("#333")

    for func_name, func_data in nist_scores["functions"].items():
        sunburst_data["ids"].append(func_name)
        sunburst_data["labels"].append(f"{func_name}\n{func_data['percentage']}%")
        sunburst_data["parents"].append("NIST CSF")
        sunburst_data["values"].append(func_data["total_categories"])
        sunburst_data["colors"].append(FUNC_COLORS.get(func_name, "#888"))

        for cd in func_data.get("control_details", []):
            cat_id = f"{func_name}/{cd['id']}"
            # Colour by effective weight, not raw status
            w = cd["effective_weight"]
            if w >= 0.8:
                cell_color = "#4CAF50"
            elif w >= 0.6:
                cell_color = "#8BC34A"
            elif w >= 0.4:
                cell_color = "#FFC107"
            elif w >= 0.1:
                cell_color = "#FF9800"
            else:
                cell_color = "#F44336"
            sunburst_data["ids"].append(cat_id)
            sunburst_data["labels"].append(cd["id"])
            sunburst_data["parents"].append(func_name)
            sunburst_data["values"].append(1)
            sunburst_data["colors"].append(cell_color)

    fig_sun = go.Figure(
        go.Sunburst(
            ids=sunburst_data["ids"],
            labels=sunburst_data["labels"],
            parents=sunburst_data["parents"],
            values=sunburst_data["values"],
            marker={"colors": sunburst_data["colors"]},
            branchvalues="total",
        )
    )
    fig_sun.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        height=600,
        margin={"t": 20, "b": 20, "l": 20, "r": 20},
    )
    st.plotly_chart(fig_sun, use_container_width=True)
    st.caption(
        "Sunburst colour reflects **effective weight** after evidence staleness "
        "and dependency penalties — not raw status."
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — ISO 27001 & MFIPPA                                 ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### ISO 27001:2022 Annex A — Control Implementation")

    iso_df = pd.DataFrame(iso_scores["domains"])

    fig_iso = go.Figure()
    fig_iso.add_trace(
        go.Bar(
            name="Implemented",
            x=iso_df["name"],
            y=iso_df["implemented"],
            marker_color="#4CAF50",
        )
    )
    fig_iso.add_trace(
        go.Bar(
            name="Partial",
            x=iso_df["name"],
            y=iso_df["partial"],
            marker_color="#FFC107",
        )
    )
    fig_iso.add_trace(
        go.Bar(
            name="Gap",
            x=iso_df["name"],
            y=iso_df["total"] - iso_df["implemented"] - iso_df["partial"],
            marker_color="#F44336",
        )
    )
    fig_iso.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        yaxis_title="Controls",
        xaxis_title="",
        height=400,
        xaxis={"gridcolor": "#222"},
        yaxis={"gridcolor": "#222"},
        legend={"bgcolor": "rgba(0,0,0,0)"},
    )
    st.plotly_chart(fig_iso, use_container_width=True)

    # ── ISO domain table with health + staleness ─────────────
    st.markdown("#### Domain Detail")
    for domain in iso_scores["domains"]:
        ev = domain.get("evidence_status", {})
        health = domain.get("health", "Unknown")
        health_icon = {"Compliant": "✅", "At Risk": "⚠️", "Non-Compliant": "❌"}.get(health, "❓")
        stale_flag = " 🗂️ stale evidence" if ev.get("stale") else ""

        with st.expander(f"{health_icon} **{domain['name']}** — {domain['percentage']}% ({health}){stale_flag}"):
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Total Controls", domain["total"])
            dc2.metric("Implemented", domain["implemented"])
            dc3.metric("Partial", domain["partial"])

            if ev.get("stale"):
                if ev.get("days_overdue"):
                    st.error(
                        f"🗂️ Domain evidence overdue by {ev['days_overdue']} days. "
                        "Score penalised to 80% of calculated until refreshed."
                    )
                else:
                    st.error("🗂️ No evidence date recorded for this domain. Score penalised to 80% of calculated.")
            elif ev.get("days_remaining") and ev["days_remaining"] <= 90:
                st.warning(f"🗂️ Evidence expires in {ev['days_remaining']} days — schedule refresh before it lapses.")

    st.markdown("---")

    # MFIPPA / custom frameworks (unchanged)
    custom_fws = [fw for fw in cfg.compliance.custom_frameworks if fw.enabled]
    if custom_fws:
        for fw in custom_fws:
            st.markdown(f"### 🏛️ {fw.name} — {fw.full_name}")
    else:
        st.markdown("### 🏛️ Additional Regulatory Frameworks")

    mfippa_items = [
        {
            "requirement": "Privacy Impact Assessments (PIAs)",
            "status": "Implemented",
            "detail": "PIAs required for all new systems processing personal information",
        },
        {
            "requirement": "Access to Information Requests",
            "status": "Implemented",
            "detail": "30-day response window; tracked in FOIP management system",
        },
        {
            "requirement": "Privacy Breach Protocol",
            "status": "Implemented",
            "detail": "IPC notification at earliest opportunity; target < 72 hours",
        },
        {
            "requirement": "Data Minimization",
            "status": "Partial",
            "detail": "Policy in place; enforcement gaps in legacy systems",
        },
        {
            "requirement": "Retention & Disposal Schedules",
            "status": "Partial",
            "detail": "Schedules exist for most record types; OT data retention under review",
        },
        {
            "requirement": "Staff Privacy Training",
            "status": "Implemented",
            "detail": "Annual mandatory training with completion tracking",
        },
        {
            "requirement": "Third-Party Data Sharing Agreements",
            "status": "Partial",
            "detail": "Template agreements exist; not all vendors have current DSAs",
        },
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

    # ── Expiry proximity alert ───────────────────────────────
    if expiring_soon:
        st.error(f"🚨 **{len(expiring_soon)} policy/policies expiring within 30 days**")
        for p in expiring_soon:
            days = p["days_remaining"]
            urgency = "🔴" if days <= 7 else "🟠" if days <= 14 else "🟡"
            st.markdown(
                f"{urgency} **{p['name']}** — "
                f"review due **{p['next_review']}** ({days} day{'s' if days != 1 else ''} remaining)"
            )
        st.markdown("---")

    # Summary metrics
    ps1, ps2, ps3, ps4 = st.columns(4)
    ps1.metric("Current", policy_summary["by_status"].get("Current", 0))
    ps2.metric("Under Review", policy_summary["by_status"].get("Under Review", 0))
    ps3.metric("Draft", policy_summary["by_status"].get("Draft", 0))
    ps4.metric("Expired", policy_summary["by_status"].get("Expired", 0))

    # Donut
    status_counts = {k: v for k, v in policy_summary["by_status"].items() if v > 0}
    fig_pol = px.pie(
        names=list(status_counts.keys()),
        values=list(status_counts.values()),
        color=list(status_counts.keys()),
        color_discrete_map={
            "Current": "#4CAF50",
            "Under Review": "#FFC107",
            "Draft": "#2196F3",
            "Expired": "#F44336",
        },
        hole=0.4,
    )
    fig_pol.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        height=300,
    )
    st.plotly_chart(fig_pol, use_container_width=True)

    st.markdown("---")
    st.markdown("### Policy Details")

    filter_status = st.multiselect(
        "Filter by Status",
        ["Current", "Under Review", "Draft", "Expired"],
        default=["Current", "Under Review", "Draft", "Expired"],
        key="policy_filter",
    )
    filtered_policies = [p for p in policies if p["status"] in filter_status]

    # Sort: expiring soonest first, then alphabetical
    expiring_names = {p["name"] for p in expiring_soon}

    def _policy_sort_key(p):
        if p.get("name") in expiring_names:
            days = next((ep["days_remaining"] for ep in expiring_soon if ep["name"] == p.get("name")), 999)
            return (0, days)
        status_order = {"Expired": 1, "Under Review": 2, "Draft": 3, "Current": 4}
        return (status_order.get(p["status"], 5), 999)

    filtered_policies.sort(key=_policy_sort_key)

    for p in filtered_policies:
        icon = {
            "Current": "✅",
            "Under Review": "🔄",
            "Draft": "📝",
            "Expired": "⛔",
        }.get(p["status"], "❓")

        is_expiring = p.get("name") in expiring_names
        expiry_flag = " 🔴 EXPIRING SOON" if is_expiring else ""

        with st.expander(f"{icon} {p['name']} — v{p['version']} ({p['status']}){expiry_flag}"):
            pc1, pc2 = st.columns(2)
            with pc1:
                st.markdown(f"**Owner:** {p['owner']}")
                st.markdown(f"**Approver:** {p['approved_by']}")
                st.markdown(f"**Version:** {p['version']}")
            with pc2:
                st.markdown(f"**Status:** {p['status']}")
                st.markdown(f"**Last Reviewed:** {p['last_reviewed']}")
                st.markdown(f"**Next Review:** {p['next_review']}")

            if is_expiring:
                days_rem = next((ep["days_remaining"] for ep in expiring_soon if ep["name"] == p.get("name")), None)
                if days_rem is not None:
                    st.error(
                        f"⏰ Review due in **{days_rem} day{'s' if days_rem != 1 else ''}**. "
                        "Assign a reviewer immediately."
                    )

            st.markdown(f"**Description:** {p['description']}")

    st.markdown("---")

    # ── Audit Readiness Score ────────────────────────────────
    st.markdown("### 🎯 Audit Readiness Score")

    nist_pct = nist_scores["overall_percentage"]
    iso_pct = iso_scores["overall_percentage"]
    policy_pct = policy_summary["current_pct"]

    # Evidence quality penalty: deduct proportionally for stale evidence
    stale_ratio = total_stale / max(nist_scores["total_controls"], 1)
    evidence_penalty = round(stale_ratio * 10)  # up to -10 pts for fully stale

    audit_score = max(
        0,
        round(nist_pct * 0.4 + iso_pct * 0.35 + policy_pct * 0.25) - evidence_penalty,
    )

    fig_audit = go.Figure(
        go.Indicator(
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
        )
    )
    fig_audit.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"t": 80, "b": 10},
    )
    st.plotly_chart(fig_audit, use_container_width=True)

    st.markdown(f"""
| Component | Weight | Score |
|---|---|---|
| NIST CSF 2.0 | 40% | {nist_pct}% |
| ISO 27001:2022 | 35% | {iso_pct}% |
| Policy Currency | 25% | {policy_pct}% |
| Evidence penalty | — | -{evidence_penalty}% |
| **Composite** | **100%** | **{audit_score}%** |
""")

    if audit_score >= 80:
        st.success("✅ Strong audit readiness. Maintain current trajectory.")
    elif audit_score >= 60:
        st.warning("⚠️ Moderate readiness. Address stale evidence and NIST CSF gaps before the next audit cycle.")
    else:
        st.error(
            "❌ Significant gaps. Prioritize compliance remediation, "
            "evidence refresh, and expired policy reviews immediately."
        )

# ── Export ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 Export Compliance Data")
ce1, ce2 = st.columns(2)
with ce1:
    policy_json = _json.dumps(
        [p.__dict__ if hasattr(p, "__dict__") else p for p in policies],
        indent=2,
        default=str,
    )
    st.download_button(
        "📋 Policies JSON",
        data=policy_json,
        file_name="policies_export.json",
        mime="application/json",
        use_container_width=True,
    )
with ce2:
    nist_json = _json.dumps(controls_data, indent=2, default=str)
    st.download_button(
        "📋 NIST CSF Controls JSON",
        data=nist_json,
        file_name="nist_csf_controls.json",
        mime="application/json",
        use_container_width=True,
    )
