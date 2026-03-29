"""
pages/9_Vendor_Registry.py

Third-Party / Vendor Risk Registry
"""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from cyberresilient.services.auth_service import get_current_user, has_permission
from cyberresilient.services.risk_service import (
    ARCHITECTURE_CHECKS,
    run_architecture_assessment,
)
from cyberresilient.services.vendor_service import (
    CRITICALITY_COLORS,
    DATA_CLASSIFICATIONS,
    TIER_COLORS,
    VENDOR_CATEGORIES,
    VENDOR_CRITICALITIES,
    create_vendor,
    get_assessment_history,
    get_overdue_vendors,
    load_vendors,
    record_assessment,
    vendor_summary,
)
from cyberresilient.theme import get_theme_colors

colors = get_theme_colors()
GOLD = colors["accent"]

st.markdown("# 🤝 Vendor Risk Registry")
st.markdown("Third-party risk management — vendor profiles, assessment history, and re-assessment scheduling.")
st.markdown("---")

summary = vendor_summary()
overdue = get_overdue_vendors()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Vendors", summary["total"])
m2.metric("Not Assessed", summary["not_assessed"])
m3.metric("Overdue Assessment", summary["overdue_assessment"])
m4.metric("Critical Vendors", summary["by_criticality"].get("Critical", 0))

if overdue:
    st.error(
        f"🚨 {len(overdue)} vendor(s) are overdue for reassessment: "
        + ", ".join(v["name"] for v in overdue[:5])
        + ("..." if len(overdue) > 5 else "")
    )

st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    [
        "📋 Vendor Register",
        "🔍 Assess a Vendor",
        "➕ Add Vendor",
    ]
)

with tab1:
    vendors = load_vendors()
    if not vendors:
        st.info("No vendors registered yet. Add one in the 'Add Vendor' tab.")
    else:
        # Risk tier distribution chart
        tier_counts = summary.get("by_tier", {})
        if tier_counts:
            fig = px.pie(
                names=list(tier_counts.keys()),
                values=list(tier_counts.values()),
                color=list(tier_counts.keys()),
                color_discrete_map=TIER_COLORS,
                hole=0.45,
                title="Vendor Risk Tier Distribution",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA",
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

        today = date.today().isoformat()
        for v in sorted(vendors, key=lambda x: x["criticality"]):
            tier_color = TIER_COLORS.get(v["current_risk_tier"], "#888")
            crit_color = CRITICALITY_COLORS.get(v["criticality"], "#888")
            overdue_flag = " ⏰ REASSESSMENT OVERDUE" if v["reassessment_due"] < today else ""

            with st.expander(
                f"**{v['name']}** — {v['current_risk_tier']}{overdue_flag} | Criticality: {v['criticality']}"
            ):
                vc1, vc2, vc3 = st.columns(3)
                with vc1:
                    st.markdown(f"**Category:** {v['category']}")
                    st.markdown(
                        f"**Criticality:** <span style='color:{crit_color}'>{v['criticality']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Data Classification:** {v['data_classification']}")
                with vc2:
                    st.markdown(
                        f"**Risk Tier:** <span style='color:{tier_color}'>{v['current_risk_tier']}</span>",
                        unsafe_allow_html=True,
                    )
                    if v.get("last_assessment_score") is not None:
                        st.markdown(f"**Last Score:** {v['last_assessment_score']}%")
                    st.markdown(f"**Last Assessed:** {v.get('last_assessed_at') or 'Never'}")
                    st.markdown(f"**Next Due:** {v['reassessment_due']}")
                with vc3:
                    if v.get("contact_name"):
                        st.markdown(f"**Contact:** {v['contact_name']}")
                    if v.get("contact_email"):
                        st.markdown(f"**Email:** {v['contact_email']}")
                    if v.get("contract_reference"):
                        st.markdown(f"**Contract:** {v['contract_reference']}")
                    if v.get("contract_expiry"):
                        st.markdown(f"**Contract Expiry:** {v['contract_expiry']}")

                # Assessment history
                history = get_assessment_history(v["id"])
                if history:
                    st.markdown("**Assessment History**")
                    hist_df = pd.DataFrame(history)[
                        ["assessed_at", "score_pct", "risk_tier", "passed", "failed", "assessed_by"]
                    ]
                    hist_df.columns = ["Date", "Score %", "Tier", "Passed", "Failed", "Assessed By"]
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)


with tab2:
    vendors = load_vendors()
    if not vendors:
        st.info("Add a vendor first before running an assessment.")
    else:
        vendor_map = {v["name"]: v["id"] for v in vendors}
        selected_name = st.selectbox("Select Vendor to Assess", list(vendor_map.keys()))
        selected_id = vendor_map[selected_name]

        with st.form("vendor_assessment"):
            st.markdown("#### Security Control Checklist")
            answers = {}
            for check in ARCHITECTURE_CHECKS:
                answers[check["id"]] = st.checkbox(
                    f"**{check['control']}** — {check['question']}",
                    key=f"va_{check['id']}",
                )
                st.caption(f"Framework: {check['framework']}")
            submitted = st.form_submit_button("🔍 Run Assessment", type="primary")

        if submitted:
            result = run_architecture_assessment(answers)
            record_assessment(
                vendor_id=selected_id,
                score_pct=result["score_pct"],
                assessment_detail=result,
                assessed_by=get_current_user().username,
            )
            st.success(
                f"Assessment recorded — {selected_name} scored **{result['score_pct']}%** ({result['overall_risk']})"
            )
            for r in result["results"]:
                if not r["passed"]:
                    st.warning(f"❌ {r['control']}: {r['risk_if_missing']}")
            st.rerun()


with tab3:
    if not has_permission("edit_risks"):
        st.warning("You do not have permission to add vendors.")
    else:
        with st.form("add_vendor"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Vendor Name *")
                category = st.selectbox("Category", VENDOR_CATEGORIES)
                criticality = st.selectbox("Criticality", VENDOR_CRITICALITIES)
                data_class = st.selectbox("Data Classification", DATA_CLASSIFICATIONS)
            with c2:
                contact_name = st.text_input("Contact Name")
                contact_email = st.text_input("Contact Email")
                contract_ref = st.text_input("Contract Reference")
                contract_expiry = st.date_input("Contract Expiry", value=None)
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("➕ Add Vendor", type="primary")

        if submitted:
            if not name:
                st.error("Vendor name is required.")
            else:
                create_vendor(
                    name=name,
                    category=category,
                    criticality=criticality,
                    data_classification=data_class,
                    contact_name=contact_name,
                    contact_email=contact_email,
                    contract_reference=contract_ref,
                    contract_expiry=str(contract_expiry) if contract_expiry else "",
                    notes=notes,
                    created_by=get_current_user().username,
                )
                st.success(f"Vendor '{name}' added.")
                st.rerun()
