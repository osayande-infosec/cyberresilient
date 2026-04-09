"""
CyberResilient — Enterprise Cybersecurity Resilience Toolkit
Main entry point for the Streamlit multi-page application.
"""

import streamlit as st

from cyberresilient.config import get_config
from cyberresilient.database import get_session, init_db
from cyberresilient.services.auth_service import (
    is_auth_enabled,
    is_learning_mode,
    render_learning_toggle,
    render_login_form,
    render_user_info,
)
from cyberresilient.theme import get_custom_css, render_sidebar_brand

cfg = get_config()

# ── Auto-initialise database tables (safe to call repeatedly) ──
init_db()

# ── Auto-seed if database is empty ──
_session = get_session()
try:
    from cyberresilient.models.db_models import RiskRow

    if not _session.query(RiskRow).first():
        import argparse

        from cyberresilient.cli import seed

        seed(argparse.Namespace(force=False))
finally:
    _session.close()

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title=cfg.branding.app_title,
    page_icon=cfg.branding.app_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Sidebar Branding ────────────────────────────────────────
with st.sidebar:
    st.markdown(render_sidebar_brand(), unsafe_allow_html=True)

# ── Auth ────────────────────────────────────────────────────
if is_auth_enabled():
    if not render_login_form():
        st.stop()
    render_user_info()

# ── Learning Mode Toggle ───────────────────────────────────
with st.sidebar:
    render_learning_toggle()

# ── Landing Page ────────────────────────────────────────────
st.markdown(f"# {cfg.branding.app_icon} {cfg.branding.app_title}")
st.markdown(f"### {cfg.branding.app_subtitle}")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **{cfg.branding.app_title}** is a comprehensive cybersecurity resilience platform
    that provides executives and security teams with actionable
    intelligence across five domains:

    - 📊 **Executive Dashboard** — Real-time security posture & KPIs
    - 🔄 **DR/BC Simulator** — Test disaster recovery readiness
    - 🚨 **Incident Response** — IR lifecycle & tabletop exercises
    - ⚠️ **Risk Register** — Heat maps & architecture risk advisor
    - ✅ **Compliance Tracker** — NIST CSF, ISO 27001 & policy lifecycle

    **Organization:** {cfg.organization.name}
    """)

with col2:
    st.markdown("""
    #### Key Capabilities
    | Feature | Detail |
    |---|---|
    | **Frameworks** | NIST CSF 2.0, ISO 27001, CIS Controls |
    | **DR Testing** | RTO/RPO simulation with RACI generation |
    | **Reporting** | PDF export for executive & audit audiences |
    | **Risk Scoring** | 5×5 likelihood × impact matrix |
    | **Architecture** | Vendor security assessment (10-point) |
    | **Customizable** | Configure your own org profile via YAML |
    """)

if is_learning_mode():
    st.info(
        "📚 **Learning Mode Active**\n\n"
        "You'll see educational callouts throughout the platform "
        "explaining real-world cybersecurity concepts, frameworks, "
        "and best practices. Toggle this off in the sidebar when you're ready."
    )

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.85rem;'>"
    "Built by Osayande Agbonkpolor — Open-source cybersecurity training toolkit<br/>"
    "Select a module from the sidebar to begin.</p>",
    unsafe_allow_html=True,
)
