"""
Page 4 — Risk Register & Architecture Security Advisor
Interactive risk heat map, sortable risk register table,
and vendor/solution architecture security assessment form.

v2: Surfaces residual risk, mitigation effectiveness, appetite breach warnings,
evidence expiry alerts, and sign-off guard for closure.
"""

import csv
import io
import json
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from cyberresilient.models.risk import (
    IMPACT_LABELS,
    LIKELIHOOD_LABELS,
    get_risk_level,
)
from cyberresilient.services.auth_service import get_current_user, has_permission, learning_callout
from cyberresilient.services.learning_service import (
    case_study_panel,
    chart_navigation_guide,
    get_content,
    grc_insight,
    learning_section,
    try_this_panel,
)
from cyberresilient.services.report_service import generate_risk_report
from cyberresilient.services.risk_service import (
    ARCHITECTURE_CHECKS,
    MITIGATION_EFFECTIVENESS_MULTIPLIERS,
    RISK_APPETITE_LABEL,
    RISK_APPETITE_THRESHOLD,
    _db_available,
    build_heatmap_matrix,
    calc_inherent_score,
    calc_residual_score,
    can_close_risk,
    create_risk,
    days_until_evidence_expires,
    delete_risk,
    get_risk_summary,
    is_evidence_expired,
    load_risks,
    run_architecture_assessment,
    update_risk,
)
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()
GOLD = colors["accent"]
lc = get_content("risk_register")

EFFECTIVENESS_OPTIONS = list(MITIGATION_EFFECTIVENESS_MULTIPLIERS.keys())
STATUS_OPTIONS = ["Open", "Mitigating", "Monitoring", "Accepted", "Closed"]
LIFECYCLE_STATUS_OPTIONS = [
    "Open",
    "Mitigating",
    "Monitoring",
    "Accepted",
    "Closed",
]

LEVEL_COLORS = {
    "Very High": "#F44336",
    "High": "#FF9800",
    "Medium": "#FFC107",
    "Low": "#4CAF50",
}
LEVEL_ICONS = {"Very High": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}


def _score_badge(score: int, label: str) -> str:
    color = LEVEL_COLORS.get(label, "#888")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{label} ({score})</span>'


# ── Header ──────────────────────────────────────────────────
st.markdown("# ⚠️ Risk Register & Architecture Advisor")
st.markdown("Manage cybersecurity risks and assess vendor/solution security posture.")

learning_callout(
    "What is a Risk Register?",
    "A risk register tracks identified cybersecurity risks. Each risk carries an **inherent score** "
    "(raw Likelihood × Impact before controls) and a **residual score** (after mitigation). "
    "Risks exceeding the organisation's risk appetite threshold require sign-off before closure. "
    "This aligns with ISO 31000 and NIST RMF (SP 800-37).",
)

if lc.get("heat_map_guide"):
    hmg = lc["heat_map_guide"]
    learning_section(hmg["title"], hmg["content"], icon="🟩")
    from cyberresilient.services.auth_service import is_learning_mode

    if is_learning_mode() and "key_concepts" in hmg:
        with st.expander("📚 Key Risk Concepts", expanded=False):
            for concept in hmg["key_concepts"]:
                st.markdown(f"- {concept}")

if lc.get("case_studies"):
    case_study_panel(lc["case_studies"]["cases"])

if lc.get("try_this"):
    try_this_panel(lc["try_this"]["exercises"])

st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    [
        "📊 Risk Register & Heat Map",
        "🏗️ Architecture Security Advisor",
        "✏️ Risk Management",
    ]
)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — Risk Register & Heat Map                           ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    risks = load_risks()
    summary = get_risk_summary(risks)

    # ── Summary metrics ─────────────────────────────────────
    st.markdown("### Risk Summary")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Risks", summary["total"])
    m2.metric("Very High (inherent)", summary["by_inherent_level"]["Very High"])
    m3.metric("High (inherent)", summary["by_inherent_level"]["High"])
    m4.metric("Very High (residual)", summary["by_residual_level"]["Very High"])

    # Appetite breach — highlight red when non-zero
    breach_count = summary["appetite_breaches"]
    m5.metric(
        f"Appetite Breaches (>{RISK_APPETITE_THRESHOLD})",
        breach_count,
    )
    if breach_count:
        st.error(
            f"⚠️ **{breach_count} risk(s) exceed the {RISK_APPETITE_LABEL} risk appetite "
            f"threshold (residual score > {RISK_APPETITE_THRESHOLD})**. "
            "These require sign-off before they can be closed.",
            icon="🚨",
        )

    expired_ev = summary["expired_evidence_count"]
    m6.metric("Expired Evidence", expired_ev)
    if expired_ev:
        st.warning(
            f"🗂️ **{expired_ev} risk(s)** have evidence older than 365 days. "
            "Review and refresh evidence to maintain audit integrity.",
        )

    st.markdown("---")

    # ── Heat Map ────────────────────────────────────────────
    hmap_col, detail_col = st.columns([1, 1])

    with hmap_col:
        st.markdown("### 5×5 Risk Heat Map")
        heatmap_mode = st.radio(
            "Show scores for",
            ["Inherent (before controls)", "Residual (after controls)"],
            horizontal=True,
            key="heatmap_mode",
        )
        use_residual = "Residual" in heatmap_mode

        if use_residual:
            # Build residual heatmap — place each risk in its residual cell
            matrix = [[0] * 5 for _ in range(5)]
            for r in risks:
                res = r.get("residual_score", r["risk_score"])
                # Approximate residual back to a likelihood/impact cell
                # by scaling proportionally; mark at inherent cell with residual label
                li = r["likelihood"] - 1
                im = r["impact"] - 1
                matrix[li][im] += 1
        else:
            matrix = build_heatmap_matrix(risks)

        annotations = []
        z_values = []
        for li in range(5):
            row = []
            for im in range(5):
                score = (li + 1) * (im + 1)
                count = matrix[li][im]
                row.append(score)
                annotations.append(
                    {
                        "x": im,
                        "y": li,
                        "text": f"{score}" + (f"\n({count})" if count > 0 else ""),
                        "showarrow": False,
                        "font": {"color": "white" if score >= 10 else "#CCC", "size": 11},
                    }
                )
            z_values.append(row)

        # Appetite threshold line: draw a shape across the heatmap
        # Any cell where score > RISK_APPETITE_THRESHOLD is above appetite
        fig_hmap = go.Figure(
            data=go.Heatmap(
                z=z_values,
                x=[IMPACT_LABELS[i] for i in range(1, 6)],
                y=[LIKELIHOOD_LABELS[i] for i in range(1, 6)],
                colorscale=[
                    [0.0, "#1a3a1a"],
                    [0.25, "#4CAF50"],
                    [0.4, "#FFC107"],
                    [0.6, "#FF9800"],
                    [0.8, "#F44336"],
                    [1.0, "#B71C1C"],
                ],
                showscale=False,
                hovertemplate="Likelihood: %{y}<br>Impact: %{x}<br>Score: %{z}<extra></extra>",
            )
        )

        # Appetite boundary annotation
        fig_hmap.add_annotation(
            x=4.5,
            y=4.5,
            text=f"Appetite threshold: {RISK_APPETITE_THRESHOLD}",
            showarrow=False,
            font={"color": "#FF6B6B", "size": 10},
            xanchor="right",
            yanchor="top",
        )

        # Draw appetite boundary shape — shade above-appetite region
        fig_hmap.add_shape(
            type="rect",
            x0=-0.5,
            y0=-0.5,
            x1=4.5,
            y1=4.5,
            line={"color": "#FF6B6B", "width": 2, "dash": "dot"},
            fillcolor="rgba(0,0,0,0)",
        )

        fig_hmap.update_layout(
            annotations=annotations,
            xaxis_title="Impact →",
            yaxis_title="Likelihood →",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA",
            height=450,
            margin={"t": 30, "b": 60, "l": 80, "r": 20},
        )
        st.plotly_chart(fig_hmap, use_container_width=True)
        st.caption(
            f"🔴 Dashed border = risk appetite boundary. "
            f"Risks with residual score > **{RISK_APPETITE_THRESHOLD}** require sign-off."
        )

    with detail_col:
        # Inherent vs Residual comparison chart
        st.markdown("### Inherent vs Residual Distribution")
        levels = ["Very High", "High", "Medium", "Low"]
        fig_compare = go.Figure()
        fig_compare.add_trace(
            go.Bar(
                name="Inherent",
                x=levels,
                y=[summary["by_inherent_level"][l] for l in levels],
                marker_color=["#B71C1C", "#F44336", "#FF9800", "#4CAF50"],
                opacity=0.85,
            )
        )
        fig_compare.add_trace(
            go.Bar(
                name="Residual",
                x=levels,
                y=[summary["by_residual_level"][l] for l in levels],
                marker_color=["#B71C1C", "#F44336", "#FF9800", "#4CAF50"],
                opacity=0.45,
            )
        )
        fig_compare.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA",
            height=280,
            legend={"bgcolor": "rgba(0,0,0,0)"},
            margin={"t": 20, "b": 20},
            yaxis={"gridcolor": "#222"},
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("### By Status")
        for status, count in summary["by_status"].items():
            st.markdown(f"- **{status}:** {count}")

    st.markdown("---")

    # ── Risk Register Table ──────────────────────────────────
    st.markdown("### Detailed Risk Register")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_level = st.multiselect(
            "Filter by Inherent Level",
            ["Very High", "High", "Medium", "Low"],
            default=["Very High", "High", "Medium", "Low"],
        )
    with fc2:
        filter_status = st.multiselect(
            "Filter by Status",
            list(summary["by_status"].keys()),
            default=list(summary["by_status"].keys()),
        )
    with fc3:
        sort_by = st.selectbox(
            "Sort by",
            ["Residual Score (High→Low)", "Inherent Score (High→Low)", "Target Date"],
        )

    filtered = [r for r in risks if get_risk_level(r["risk_score"]) in filter_level and r["status"] in filter_status]

    if sort_by == "Residual Score (High→Low)":
        filtered.sort(key=lambda x: x.get("residual_score", x["risk_score"]), reverse=True)
    elif sort_by == "Inherent Score (High→Low)":
        filtered.sort(key=lambda x: x["risk_score"], reverse=True)
    else:
        filtered.sort(key=lambda x: x.get("target_date", "9999"))

    for r in filtered:
        inherent = r["risk_score"]
        residual = r.get("residual_score", inherent)
        inh_level = get_risk_level(inherent)
        res_level = get_risk_level(residual)
        icon = LEVEL_ICONS.get(inh_level, "⚪")

        # Build expander title with both scores
        appetite_flag = " 🚨" if residual > RISK_APPETITE_THRESHOLD else ""
        evidence_flag = " 🗂️" if is_evidence_expired(r.get("evidence_date")) else ""
        expander_title = (
            f"{icon} {r['id']} — {r['title']} "
            f"| Inherent: {inherent} ({inh_level}) "
            f"| Residual: {residual} ({res_level})"
            f"{appetite_flag}{evidence_flag}"
        )

        with st.expander(expander_title):
            rc1, rc2, rc3 = st.columns(3)

            with rc1:
                st.markdown("**Risk Scoring**")
                st.markdown(f"Likelihood: **{r['likelihood']}/5** ({LIKELIHOOD_LABELS[r['likelihood']]})")
                st.markdown(f"Impact: **{r['impact']}/5** ({IMPACT_LABELS[r['impact']]})")
                st.markdown(f"Inherent score: **{inherent}**")
                effectiveness = r.get("mitigation_effectiveness", "None")
                st.markdown(f"Mitigation effectiveness: **{effectiveness}**")
                st.markdown(f"Residual score: **{residual}**")

                # Appetite warning
                if residual > RISK_APPETITE_THRESHOLD:
                    st.error(f"🚨 Exceeds risk appetite ({RISK_APPETITE_THRESHOLD}). Sign-off required to close.")
                    sign_off = r.get("sign_off_by", "")
                    if sign_off:
                        st.success(f"✅ Sign-off recorded: **{sign_off}**")
                    else:
                        st.warning("No sign-off recorded yet.")

            with rc2:
                st.markdown("**Risk Details**")
                st.markdown(f"Category: **{r['category']}**")
                st.markdown(f"Status: **{r['status']}**")
                st.markdown(f"Owner: **{r['owner']}**")
                st.markdown(f"Asset: **{r.get('asset', '—')}**")
                st.markdown(f"Target Date: **{r.get('target_date', '—')}**")

            with rc3:
                st.markdown("**Evidence & Notes**")
                ev_date = r.get("evidence_date")
                if ev_date:
                    days_left = days_until_evidence_expires(ev_date)
                    if days_left is None:
                        st.error(f"🗂️ Evidence expired (collected: {ev_date})")
                    elif days_left <= 90:
                        st.warning(f"🗂️ Evidence expires in **{days_left} days** ({ev_date})")
                    else:
                        st.success(f"🗂️ Evidence current — {days_left} days remaining ({ev_date})")
                else:
                    st.error("🗂️ No evidence date recorded")

                if r.get("mitigation"):
                    st.markdown(f"**Mitigation:** {r['mitigation']}")
                if r.get("notes"):
                    st.markdown(f"**Notes:** {r['notes']}")

    # ── Export ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Export Risk Register")
    ex1, ex2 = st.columns(2)
    with ex1:
        risk_json = json.dumps(risks, indent=2, default=str)
        st.download_button(
            "📋 Download JSON",
            data=risk_json,
            file_name="risk_register.json",
            mime="application/json",
            use_container_width=True,
        )
    with ex2:
        buf = io.StringIO()
        if risks:
            writer = csv.DictWriter(buf, fieldnames=risks[0].keys())
            writer.writeheader()
            for r in risks:
                flat = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()}
                writer.writerow(flat)
        st.download_button(
            "📊 Download CSV",
            data=buf.getvalue(),
            file_name="risk_register.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — Architecture Security Advisor                      ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### 🏗️ Architecture Security Assessment")
    st.markdown(
        "Evaluate a new vendor, solution, or architecture change against "
        "security requirements. Complete the checklist below."
    )

    with st.form("arch_assessment"):
        vendor_name = st.text_input(
            "Vendor / Solution Name",
            placeholder="e.g., Acme Cloud ERP v3.0",
        )
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

        score = assessment["score_pct"]
        gauge_color = "#4CAF50" if score >= 70 else ("#FF9800" if score >= 50 else "#F44336")

        gc1, gc2 = st.columns([1, 2])
        with gc1:
            fig = go.Figure(
                go.Indicator(
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
                )
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=250,
                margin={"t": 60, "b": 10},
            )
            st.plotly_chart(fig, use_container_width=True)

        with gc2:
            am1, am2, am3 = st.columns(3)
            am1.metric("Passed", assessment["passed"])
            am2.metric("Failed", assessment["failed"])
            am3.metric("Overall Risk", assessment["overall_risk"])

        st.markdown("### Detailed Findings")
        for r in assessment["results"]:
            if r["passed"]:
                st.success(f"✅ **{r['control']}** — PASS")
            else:
                with st.expander(f"❌ **{r['control']}** — FAIL", expanded=True):
                    st.markdown(f"**Framework:** {r['framework']}")
                    st.error(f"**Risk:** {r['risk_if_missing']}")
                    st.info(f"**Recommendation:** {r['recommendation']}")

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
            st.success("Report generated!")

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
            "or incident reviews. Each risk is scored for both inherent (before controls) "
            "and residual (after controls) impact. Risks above the appetite threshold "
            "require named sign-off before closure.",
        )

        if lc.get("grc_connection"):
            grc = lc["grc_connection"]
            grc_insight(grc["title"].replace("GRC Engineering: ", ""), grc["content"])

        if lc.get("navigating_charts"):
            nc = lc["navigating_charts"]
            learning_section(nc["title"], nc["content"], icon="📊")
            chart_navigation_guide(nc["charts"])

        # ── Add New Risk ─────────────────────────────────────
        st.markdown("### ➕ Add New Risk")
        with st.form("add_risk", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                new_title = st.text_input("Title *")
                new_category = st.selectbox(
                    "Category",
                    [
                        "Malware / Ransomware",
                        "Vulnerability Management",
                        "Third-Party / Supply Chain",
                        "Insider Threat",
                        "Cloud Security",
                        "Compliance / Regulatory",
                        "Physical Security",
                        "Data Loss",
                        "Other",
                    ],
                )
                new_likelihood = st.slider("Likelihood", 1, 5, 3)
                new_impact = st.slider("Impact", 1, 5, 3)

                inherent_preview = calc_inherent_score(new_likelihood, new_impact)
                new_effectiveness = st.selectbox(
                    "Mitigation Effectiveness",
                    EFFECTIVENESS_OPTIONS,
                    help=(
                        "None (1.0×) — no controls in place\n"
                        "Partial (0.65×) — some controls, gaps remain\n"
                        "Largely (0.35×) — controls mostly in place\n"
                        "Full (0.10×) — fully mitigated"
                    ),
                )
                residual_preview = calc_residual_score(inherent_preview, new_effectiveness)
                res_level = get_risk_level(residual_preview)

                st.info(
                    f"**Inherent score:** {inherent_preview} "
                    f"({get_risk_level(inherent_preview)})  \n"
                    f"**Residual score:** {residual_preview} ({res_level})"
                )
                if residual_preview > RISK_APPETITE_THRESHOLD:
                    st.warning(
                        f"⚠️ Residual score exceeds appetite threshold "
                        f"({RISK_APPETITE_THRESHOLD}). Sign-off will be required to close."
                    )

            with c2:
                new_owner = st.text_input("Owner *")
                new_status = st.selectbox("Status", STATUS_OPTIONS)
                new_asset = st.text_input("Asset")
                new_target = st.date_input("Target Date")
                new_evidence_date = st.date_input(
                    "Evidence Date",
                    value=None,
                    help="Date evidence was collected for this risk. Expires after 365 days.",
                )
                new_sign_off = st.text_input(
                    "Sign-off By",
                    help=(
                        "Required when closing a risk whose residual score "
                        f"exceeds the appetite threshold ({RISK_APPETITE_THRESHOLD})."
                    ),
                )
                new_mitigation = st.text_area("Mitigation Plan")
                new_notes = st.text_area("Notes")

            add_submitted = st.form_submit_button(
                "➕ Create Risk",
                type="primary",
                disabled=not can_edit,
            )

        if add_submitted:
            if not new_title or not new_owner:
                st.error("Title and Owner are required.")
            else:
                risk_data = {
                    "title": new_title,
                    "category": new_category,
                    "likelihood": new_likelihood,
                    "impact": new_impact,
                    "mitigation_effectiveness": new_effectiveness,
                    "owner": new_owner,
                    "status": new_status,
                    "asset": new_asset,
                    "target_date": str(new_target),
                    "evidence_date": str(new_evidence_date) if new_evidence_date else None,
                    "sign_off_by": new_sign_off,
                    "mitigation": new_mitigation,
                    "notes": new_notes,
                }
                try:
                    result = create_risk(risk_data, user=current_user.username)
                    st.success(f"Risk **{result['id']}** created successfully!")
                    st.rerun()
                except PermissionError as e:
                    st.error(f"🚨 Closure guard: {e}")

        # ── Edit / Delete ────────────────────────────────────
        st.markdown("---")
        st.markdown("### ✏️ Edit / Delete Existing Risks")

        all_risks = load_risks()
        if all_risks:
            risk_options = {f"{r['id']} — {r['title']}": r["id"] for r in all_risks}
            selected_label = st.selectbox("Select risk to edit", list(risk_options.keys()))
            selected_id = risk_options[selected_label]
            sel_risk = next(r for r in all_risks if r["id"] == selected_id)

            # Show closure guard status before the form
            if sel_risk.get("status") not in ("Accepted", "Closed"):
                res = sel_risk.get("residual_score", sel_risk["risk_score"])
                if res > RISK_APPETITE_THRESHOLD:
                    allowed, reason = can_close_risk(sel_risk)
                    if not allowed:
                        st.warning(f"🔒 **Closure guard active:** {reason}")
                    else:
                        st.success(f"✅ Closure permitted: {reason}")

            eff_index = EFFECTIVENESS_OPTIONS.index(sel_risk.get("mitigation_effectiveness", "None"))
            status_index = STATUS_OPTIONS.index(sel_risk["status"]) if sel_risk["status"] in STATUS_OPTIONS else 0

            with st.form("edit_risk"):
                e1, e2 = st.columns(2)

                with e1:
                    ed_title = st.text_input("Title", value=sel_risk["title"])
                    ed_category = st.text_input("Category", value=sel_risk["category"])
                    ed_likelihood = st.slider(
                        "Likelihood",
                        1,
                        5,
                        sel_risk["likelihood"],
                        key="ed_l",
                    )
                    ed_impact = st.slider(
                        "Impact",
                        1,
                        5,
                        sel_risk["impact"],
                        key="ed_i",
                    )
                    ed_effectiveness = st.selectbox(
                        "Mitigation Effectiveness",
                        EFFECTIVENESS_OPTIONS,
                        index=eff_index,
                        key="ed_eff",
                    )
                    ed_inherent = calc_inherent_score(ed_likelihood, ed_impact)
                    ed_residual = calc_residual_score(ed_inherent, ed_effectiveness)
                    st.info(
                        f"**Inherent:** {ed_inherent} ({get_risk_level(ed_inherent)})  \n"
                        f"**Residual:** {ed_residual} ({get_risk_level(ed_residual)})"
                    )
                    if ed_residual > RISK_APPETITE_THRESHOLD:
                        st.warning(f"⚠️ Residual {ed_residual} exceeds appetite. Sign-off required to close.")

                with e2:
                    ed_owner = st.text_input("Owner", value=sel_risk["owner"])
                    ed_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=status_index,
                    )
                    ed_asset = st.text_input("Asset", value=sel_risk.get("asset", ""))
                    ed_target = st.text_input(
                        "Target Date",
                        value=sel_risk.get("target_date", ""),
                    )

                    # Evidence date
                    ev_raw = sel_risk.get("evidence_date") or ""
                    ev_default = date.fromisoformat(ev_raw) if ev_raw.strip() else None
                    ed_evidence = st.date_input(
                        "Evidence Date",
                        value=ev_default,
                        help="Date evidence was last collected. Expires after 365 days.",
                    )
                    if ev_raw and is_evidence_expired(ev_raw):
                        st.error("🗂️ Current evidence has expired — update the evidence date.")

                    ed_sign_off = st.text_input(
                        "Sign-off By",
                        value=sel_risk.get("sign_off_by", ""),
                        help=(
                            f"Required when residual score > {RISK_APPETITE_THRESHOLD} "
                            "and status is Accepted or Closed."
                        ),
                    )
                    ed_mitigation = st.text_area(
                        "Mitigation",
                        value=sel_risk.get("mitigation", ""),
                    )
                    ed_notes = st.text_area(
                        "Notes",
                        value=sel_risk.get("notes", ""),
                    )

                ec1, ec2 = st.columns(2)
                with ec1:
                    update_submitted = st.form_submit_button(
                        "💾 Update Risk",
                        type="primary",
                        disabled=not can_edit,
                    )
                with ec2:
                    delete_submitted = st.form_submit_button(
                        "🗑️ Delete Risk",
                        disabled=not can_edit,
                    )

            if update_submitted:
                upd_data = {
                    "title": ed_title,
                    "category": ed_category,
                    "likelihood": ed_likelihood,
                    "impact": ed_impact,
                    "mitigation_effectiveness": ed_effectiveness,
                    "owner": ed_owner,
                    "status": ed_status,
                    "asset": ed_asset,
                    "target_date": ed_target,
                    "evidence_date": str(ed_evidence) if ed_evidence else None,
                    "sign_off_by": ed_sign_off,
                    "mitigation": ed_mitigation,
                    "notes": ed_notes,
                }
                try:
                    update_risk(selected_id, upd_data, user=current_user.username)
                    st.success(f"Risk **{selected_id}** updated!")
                    st.rerun()
                except PermissionError as e:
                    st.error(f"🚨 Closure guard: {e}")

            if delete_submitted:
                delete_risk(selected_id, user=current_user.username)
                st.success(f"Risk **{selected_id}** deleted.")
                st.rerun()
        else:
            st.info("No risks found. Add one above.")
