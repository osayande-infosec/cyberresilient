"""
DurhamResilient — Municipal Cybersecurity Resilience Platform
Main entry point for the Streamlit multi-page application.
"""

import streamlit as st

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="DurhamResilient",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Gold accent overrides */
    .stMetric .metric-container { border-left: 3px solid #C9A84C; padding-left: 12px; }
    div[data-testid="stSidebar"] { border-right: 1px solid #2A2A2A; }
    h1, h2, h3 { color: #EAEAEA !important; }
    .gold { color: #C9A84C; }
    .status-pass { color: #4CAF50; font-weight: 700; }
    .status-fail { color: #F44336; font-weight: 700; }
    .status-partial { color: #FFC107; font-weight: 700; }
    /* Metric value styling */
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    /* Sidebar branding */
    .sidebar-brand { text-align: center; padding: 1rem 0 0.5rem 0; }
    .sidebar-brand h1 { font-size: 1.6rem; margin: 0; color: #C9A84C !important; }
    .sidebar-brand p { font-size: 0.8rem; color: #888; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Branding ────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h1>🛡️ DurhamResilient</h1>
        <p>Municipal Cybersecurity<br/>Resilience Platform</p>
    </div>
    <hr style="border-color: #2A2A2A; margin: 0.5rem 0;">
    """, unsafe_allow_html=True)

# ── Landing Page ────────────────────────────────────────────
st.markdown("# 🛡️ DurhamResilient")
st.markdown("### Municipal Cybersecurity Resilience Platform")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **DurhamResilient** is a comprehensive cybersecurity resilience platform
    designed for municipal government operations. It provides executives
    and security teams with actionable intelligence across five domains:

    - 📊 **Executive Dashboard** — Real-time security posture & KPIs
    - 🔄 **DR/BC Simulator** — Test disaster recovery readiness
    - 🚨 **Incident Response** — IR lifecycle & tabletop exercises
    - ⚠️ **Risk Register** — Heat maps & architecture risk advisor
    - ✅ **Compliance Tracker** — NIST CSF, ISO 27001 & policy lifecycle
    """)

with col2:
    st.markdown("""
    #### Key Capabilities
    | Feature | Detail |
    |---|---|
    | **Frameworks** | NIST CSF 2.0, ISO 27001, CIS Controls |
    | **Compliance** | MFIPPA, Ontario Privacy, Municipal Act |
    | **DR Testing** | RTO/RPO simulation with RACI generation |
    | **Reporting** | PDF export for executive & audit audiences |
    | **Risk Scoring** | 5×5 likelihood × impact matrix |
    | **Architecture** | Vendor security assessment (10-point) |
    """)

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.85rem;'>"
    "Built for the Region of Durham By Osayande Agbonkpolor for The Senior Cybersecurity Specialist Interview Showcase<br/>"
    "Select a module from the sidebar to begin.</p>",
    unsafe_allow_html=True,
)
