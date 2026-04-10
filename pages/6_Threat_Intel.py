"""
Page 6 — MITRE ATT&CK Threat Intelligence Mapper
Map organizational threats to the MITRE ATT&CK framework,
visualize attack chains, and correlate with existing controls.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cyberresilient.config import get_config
from cyberresilient.services.auth_service import learning_callout
from cyberresilient.services.learning_service import (
    case_study_panel,
    chart_navigation_guide,
    get_content,
    grc_insight,
    learning_section,
)
from cyberresilient.theme import get_theme_colors

cfg = get_config()
colors = get_theme_colors()
GOLD = colors["accent"]

# ── Header ──────────────────────────────────────────────────
st.markdown("# 🗺️ MITRE ATT&CK Threat Intelligence Mapper")
st.markdown("Map organizational threats to MITRE ATT&CK tactics and techniques.")
st.markdown("---")

learning_callout(
    "What is MITRE ATT&CK?",
    "MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) is a "
    "globally-accessible knowledge base of adversary behavior. It organizes "
    "attack techniques into **14 Tactics** (the 'why') and hundreds of "
    "**Techniques** (the 'how'). Security teams use ATT&CK to evaluate "
    "detection coverage, prioritize defenses, and communicate threats in a "
    "common language. It's the industry standard for threat-informed defense.",
)

# ── ATT&CK Tactics & Techniques (curated subset) ───────────
ATTACK_DATA = {
    "Reconnaissance": {
        "color": "#9C27B0",
        "techniques": [
            {"id": "T1595", "name": "Active Scanning", "detected": True, "control": "Network monitoring, IDS/IPS"},
            {
                "id": "T1589",
                "name": "Gather Victim Identity Info",
                "detected": False,
                "control": "OSINT monitoring recommended",
            },
            {"id": "T1591", "name": "Gather Victim Org Info", "detected": False, "control": "Public data minimization"},
        ],
    },
    "Initial Access": {
        "color": "#F44336",
        "techniques": [
            {"id": "T1566", "name": "Phishing", "detected": True, "control": "Email gateway + phishing simulation"},
            {
                "id": "T1190",
                "name": "Exploit Public-Facing App",
                "detected": True,
                "control": "WAF, vulnerability scanning",
            },
            {"id": "T1078", "name": "Valid Accounts", "detected": True, "control": "Azure AD Conditional Access + MFA"},
            {
                "id": "T1133",
                "name": "External Remote Services",
                "detected": True,
                "control": "VPN with MFA, network segmentation",
            },
        ],
    },
    "Execution": {
        "color": "#FF5722",
        "techniques": [
            {
                "id": "T1059",
                "name": "Command & Scripting Interpreter",
                "detected": True,
                "control": "PowerShell logging, AMSI",
            },
            {"id": "T1204", "name": "User Execution", "detected": True, "control": "AppLocker, endpoint protection"},
            {"id": "T1047", "name": "WMI", "detected": True, "control": "WMI event monitoring via SIEM"},
        ],
    },
    "Persistence": {
        "color": "#FF9800",
        "techniques": [
            {"id": "T1547", "name": "Boot/Logon Autostart", "detected": True, "control": "Registry monitoring, EDR"},
            {"id": "T1136", "name": "Create Account", "detected": True, "control": "Azure AD audit logs, alert rules"},
            {"id": "T1053", "name": "Scheduled Task/Job", "detected": True, "control": "Task scheduler monitoring"},
        ],
    },
    "Privilege Escalation": {
        "color": "#FFC107",
        "techniques": [
            {
                "id": "T1068",
                "name": "Exploitation for Privilege Escalation",
                "detected": True,
                "control": "Patch management, EDR",
            },
            {"id": "T1548", "name": "Abuse Elevation Control", "detected": True, "control": "UAC enforcement, PAM"},
            {
                "id": "T1134",
                "name": "Access Token Manipulation",
                "detected": False,
                "control": "Advanced EDR correlation needed",
            },
        ],
    },
    "Defense Evasion": {
        "color": "#CDDC39",
        "techniques": [
            {
                "id": "T1027",
                "name": "Obfuscated Files/Information",
                "detected": True,
                "control": "AMSI, sandbox analysis",
            },
            {
                "id": "T1562",
                "name": "Impair Defenses",
                "detected": True,
                "control": "Tamper protection, EDR monitoring",
            },
            {
                "id": "T1070",
                "name": "Indicator Removal",
                "detected": False,
                "control": "Centralized logging, WORM storage",
            },
        ],
    },
    "Credential Access": {
        "color": "#4CAF50",
        "techniques": [
            {
                "id": "T1003",
                "name": "OS Credential Dumping",
                "detected": True,
                "control": "Credential Guard, LSASS protection",
            },
            {
                "id": "T1110",
                "name": "Brute Force",
                "detected": True,
                "control": "Account lockout, Azure AD Smart Lockout",
            },
            {
                "id": "T1557",
                "name": "Adversary-in-the-Middle",
                "detected": False,
                "control": "Certificate pinning recommended",
            },
        ],
    },
    "Discovery": {
        "color": "#009688",
        "techniques": [
            {"id": "T1087", "name": "Account Discovery", "detected": True, "control": "SIEM correlation, honeytokens"},
            {
                "id": "T1082",
                "name": "System Information Discovery",
                "detected": True,
                "control": "EDR behavioral analytics",
            },
        ],
    },
    "Lateral Movement": {
        "color": "#2196F3",
        "techniques": [
            {
                "id": "T1021",
                "name": "Remote Services (RDP/SMB)",
                "detected": True,
                "control": "Network segmentation, jump servers",
            },
            {"id": "T1570", "name": "Lateral Tool Transfer", "detected": True, "control": "File integrity monitoring"},
        ],
    },
    "Collection": {
        "color": "#3F51B5",
        "techniques": [
            {"id": "T1005", "name": "Data from Local System", "detected": True, "control": "DLP, endpoint monitoring"},
            {"id": "T1114", "name": "Email Collection", "detected": True, "control": "M365 audit logs, DLP"},
        ],
    },
    "Exfiltration": {
        "color": "#673AB7",
        "techniques": [
            {
                "id": "T1048",
                "name": "Exfiltration Over Alternative Protocol",
                "detected": True,
                "control": "DNS monitoring, proxy inspection",
            },
            {"id": "T1567", "name": "Exfiltration to Cloud Storage", "detected": True, "control": "CASB, DLP policies"},
        ],
    },
    "Impact": {
        "color": "#E91E63",
        "techniques": [
            {"id": "T1486", "name": "Data Encrypted for Impact", "detected": True, "control": "EDR, immutable backups"},
            {"id": "T1489", "name": "Service Stop", "detected": True, "control": "Service monitoring, auto-restart"},
            {
                "id": "T1499",
                "name": "Endpoint Denial of Service",
                "detected": True,
                "control": "DDoS protection, rate limiting",
            },
        ],
    },
}

# ── Tabs ────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Coverage Heatmap", "🔗 Attack Chain Builder", "📋 Technique Detail"])

# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — Coverage Heatmap                                   ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown("### Detection Coverage by ATT&CK Tactic")

    learning_callout(
        "Reading a Coverage Heatmap",
        "This heatmap shows how many techniques your organization can detect "
        "within each ATT&CK tactic. Green = strong coverage, red = gaps. "
        "No organization achieves 100% — the goal is to prioritize detection "
        "for techniques used by your most likely threat actors.",
    )

    tactics = list(ATTACK_DATA.keys())
    detected_counts = []
    gap_counts = []
    total_counts = []
    coverage_pcts = []

    for tactic in tactics:
        techs = ATTACK_DATA[tactic]["techniques"]
        total = len(techs)
        detected = sum(1 for t in techs if t["detected"])
        detected_counts.append(detected)
        gap_counts.append(total - detected)
        total_counts.append(total)
        coverage_pcts.append(round(detected / total * 100) if total else 0)

    # Stacked bar chart
    fig_cov = go.Figure()
    fig_cov.add_trace(
        go.Bar(
            name="Detected",
            x=tactics,
            y=detected_counts,
            marker_color="#4CAF50",
            text=detected_counts,
            textposition="inside",
        )
    )
    fig_cov.add_trace(
        go.Bar(
            name="Gap",
            x=tactics,
            y=gap_counts,
            marker_color="#F44336",
            text=gap_counts,
            textposition="inside",
        )
    )
    fig_cov.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        yaxis_title="Techniques",
        xaxis={"gridcolor": "#222", "tickangle": 45},
        yaxis={"gridcolor": "#222"},
        height=450,
        legend={"bgcolor": "rgba(0,0,0,0)"},
        margin={"b": 120},
    )
    st.plotly_chart(fig_cov, use_container_width=True)

    # Overall metrics
    total_all = sum(total_counts)
    detected_all = sum(detected_counts)
    overall_pct = round(detected_all / total_all * 100)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Techniques Tracked", total_all)
    m2.metric("Detected", detected_all)
    m3.metric("Gaps", total_all - detected_all)
    m4.metric("Overall Coverage", f"{overall_pct}%")

    # Per-tactic table
    st.markdown("### Tactic Coverage Detail")
    tactic_df = pd.DataFrame(
        {
            "Tactic": tactics,
            "Total": total_counts,
            "Detected": detected_counts,
            "Gaps": gap_counts,
            "Coverage %": coverage_pcts,
        }
    )
    st.dataframe(
        tactic_df.style.background_gradient(subset=["Coverage %"], cmap="RdYlGn"),
        use_container_width=True,
        hide_index=True,
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — Attack Chain Builder                               ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### 🔗 Attack Chain Visualization")

    learning_callout(
        "Understanding Attack Chains",
        "An attack chain (or kill chain) models the sequence of tactics an "
        "adversary follows during an intrusion. By mapping real-world attacks "
        "to ATT&CK tactics, defenders can identify which phases they can "
        "detect and where blind spots exist. This is the foundation of "
        "**threat-informed defense**.",
    )

    ATTACK_CHAINS = {
        "Ransomware (Municipal Government)": [
            ("Reconnaissance", "T1591", "Gather Victim Org Info"),
            ("Initial Access", "T1566", "Phishing"),
            ("Execution", "T1059", "Command & Scripting Interpreter"),
            ("Persistence", "T1547", "Boot/Logon Autostart"),
            ("Privilege Escalation", "T1068", "Exploitation for Privilege Escalation"),
            ("Lateral Movement", "T1021", "Remote Services (RDP/SMB)"),
            ("Collection", "T1005", "Data from Local System"),
            ("Exfiltration", "T1567", "Exfiltration to Cloud Storage"),
            ("Impact", "T1486", "Data Encrypted for Impact"),
        ],
        "Insider Threat (Data Exfiltration)": [
            ("Initial Access", "T1078", "Valid Accounts"),
            ("Discovery", "T1087", "Account Discovery"),
            ("Collection", "T1005", "Data from Local System"),
            ("Collection", "T1114", "Email Collection"),
            ("Exfiltration", "T1567", "Exfiltration to Cloud Storage"),
        ],
        "OT/SCADA Targeting": [
            ("Reconnaissance", "T1595", "Active Scanning"),
            ("Initial Access", "T1133", "External Remote Services"),
            ("Execution", "T1059", "Command & Scripting Interpreter"),
            ("Credential Access", "T1003", "OS Credential Dumping"),
            ("Lateral Movement", "T1021", "Remote Services (RDP/SMB)"),
            ("Impact", "T1489", "Service Stop"),
        ],
    }

    selected_chain = st.selectbox("Select Attack Scenario", list(ATTACK_CHAINS.keys()))
    chain = ATTACK_CHAINS[selected_chain]

    # Build Sankey diagram
    labels = []
    sources = []
    targets = []
    values = []
    node_colors = []

    for i, (tactic, tech_id, tech_name) in enumerate(chain):
        label = f"{tactic}\n{tech_id}: {tech_name}"
        labels.append(label)
        tactic_color = ATTACK_DATA.get(tactic, {}).get("color", "#888")
        node_colors.append(tactic_color)
        if i > 0:
            sources.append(i - 1)
            targets.append(i)
            values.append(1)

    fig_chain = go.Figure(
        go.Sankey(
            node={
                "pad": 15,
                "thickness": 20,
                "label": labels,
                "color": node_colors,
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": "rgba(200,200,200,0.3)",
            },
        )
    )
    fig_chain.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA",
        height=400,
        margin={"t": 20, "b": 20},
    )
    st.plotly_chart(fig_chain, use_container_width=True)

    # Detection status for chain
    st.markdown("### Detection Status Along Kill Chain")
    for tactic, tech_id, tech_name in chain:
        techs = ATTACK_DATA.get(tactic, {}).get("techniques", [])
        match = next((t for t in techs if t["id"] == tech_id), None)
        if match:
            icon = "✅" if match["detected"] else "❌"
            st.markdown(f"{icon} **{tactic}** → {tech_id}: {tech_name} — *{match['control']}*")
        else:
            st.markdown(f"⚪ **{tactic}** → {tech_id}: {tech_name}")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 3 — Technique Detail                                   ║
# ╚══════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown("### 📋 Full Technique Inventory")

    learning_callout(
        "Using ATT&CK for Gap Analysis",
        "Walk through each tactic and its techniques. Techniques marked as "
        "'Gap' are your detection blind spots — these should be prioritized "
        "in your security roadmap. Cross-reference with your NIST CSF Protect "
        "and Detect functions for a unified view of control effectiveness.",
    )

    filter_status = st.radio("Filter", ["All", "Detected Only", "Gaps Only"], horizontal=True)

    # GRC Engineering: Threat-Informed Compliance
    lc = get_content("threat_intel")
    if lc.get("grc_connection"):
        gc = lc["grc_connection"]
        grc_insight(gc["title"].replace("GRC Engineering: ", ""), gc["content"])

    if lc.get("case_studies"):
        case_study_panel(lc["case_studies"]["cases"])

    if lc.get("threat_actors"):
        ta = lc["threat_actors"]
        learning_section(ta["title"], ta["content"], icon="🎭")

    if lc.get("detection_gaps"):
        dg = lc["detection_gaps"]
        learning_section(dg["title"], dg["content"], icon="🔍")

    if lc.get("navigating_charts"):
        nc = lc["navigating_charts"]
        learning_section(nc["title"], nc["content"], icon="📊")
        chart_navigation_guide(nc["charts"])

    for tactic, tactic_data in ATTACK_DATA.items():
        techs = tactic_data["techniques"]
        if filter_status == "Detected Only":
            techs = [t for t in techs if t["detected"]]
        elif filter_status == "Gaps Only":
            techs = [t for t in techs if not t["detected"]]

        if not techs:
            continue

        with st.expander(f"**{tactic}** ({len(techs)} techniques)"):
            for t in techs:
                icon = "✅" if t["detected"] else "❌"
                st.markdown(f"{icon} **{t['id']}** — {t['name']}")
                st.caption(f"Control: {t['control']}")
