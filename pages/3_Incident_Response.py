"""
Page 3 — Incident Response Center & Tabletop Exercise Engine
IR lifecycle walkthrough, interactive tabletop scenario builder,
post-mortem generator, and communication templates.
"""

import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path
from datetime import datetime

from cyberresilient.config import get_config
from cyberresilient.services.auth_service import learning_callout, is_learning_mode
from cyberresilient.services.learning_service import (
    get_content, case_study_panel, learning_section, grc_insight,
)
from cyberresilient.theme import get_theme_colors

cfg = get_config()
colors = get_theme_colors()
GOLD = colors["accent"]

# ── Header ──────────────────────────────────────────────────
st.markdown("# 🚨 Incident Response Center")
st.markdown("NIST SP 800-61r2 aligned IR lifecycle, tabletop exercises, and post-mortem generation.")
st.markdown("---")

lc = get_content("incident_response")

learning_callout(
    "What is Incident Response?",
    "Incident Response (IR) is the systematic process of preparing for, detecting, "
    "containing, eradicating, and recovering from cybersecurity incidents. "
    "NIST SP 800-61 Rev 2 defines four phases: **Preparation → Detection & Analysis "
    "→ Containment, Eradication & Recovery → Post-Incident Activity**. "
    "Every organization needs a tested IR plan — tabletop exercises simulate "
    "incidents so teams can practice decision-making under pressure.",
)

# Case studies (learning mode)
if lc.get("case_studies"):
    case_study_panel(lc["case_studies"]["cases"])

# GRC insight (learning mode)
if lc.get("grc_connection"):
    grc = lc["grc_connection"]
    grc_insight(grc["title"].replace("GRC Engineering: ", ""), grc["content"])

# ── Tabs ────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 IR Lifecycle", "🎯 Tabletop Exercise", "📝 Post-Mortem Generator", "📨 Communication Templates"
])

# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — IR Lifecycle (NIST 800-61r2)                       ║
# ╚══════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown("### NIST SP 800-61r2 — Incident Response Lifecycle")

    phases = [
        {
            "name": "1. Preparation",
            "icon": "🛡️",
            "color": "#4CAF50",
            "description": "Establish and maintain IR capability before incidents occur.",
            "activities": [
                "Maintain up-to-date incident response plan (reviewed quarterly)",
                "Ensure IR team training & tabletop exercise completion",
                "Deploy and validate detection tools (SIEM, EDR, NDR)",
                "Establish communication channels and contact lists",
                "Pre-stage forensic tools and jump kits",
                "Define severity classification criteria (P1–P4)",
                "Coordinate with legal, HR, communications, and executive leadership",
            ],
            "durham_context": f"Organization Context: Coordinate with all departments, law enforcement, privacy regulators, and provincial CSIRT as applicable."
        },
        {
            "name": "2. Detection & Analysis",
            "icon": "🔍",
            "color": "#2196F3",
            "description": "Identify and validate potential security incidents.",
            "activities": [
                "Monitor SIEM alerts and correlate events across IT/OT environments",
                "Triage alerts using severity matrix (impact × urgency)",
                "Gather initial indicators of compromise (IOCs)",
                "Document timeline of events in incident tracking system",
                "Classify incident type (malware, unauthorized access, data breach, etc.)",
                "Determine scope: which systems, data, and departments affected",
                "Notify CISO and initiate ICS (Incident Command Structure) if P1/P2",
            ],
            "durham_context": "MTTD target: < 2.5 hours. OT/SCADA incidents require immediate WaterOps and Safety notification."
        },
        {
            "name": "3. Containment",
            "icon": "🔒",
            "color": "#FF9800",
            "description": "Prevent further damage while preserving evidence.",
            "activities": [
                "Short-term containment: isolate affected systems from network",
                "Long-term containment: apply temporary fixes, enable enhanced monitoring",
                "Preserve forensic evidence (disk images, memory dumps, logs)",
                "Activate network segmentation between IT and OT if lateral movement suspected",
                "Block malicious IPs, domains, and hashes at perimeter",
                "Reset compromised credentials; force MFA re-enrollment",
                "Communicate containment status to stakeholders",
            ],
            "durham_context": "OT containment: Engage SCADA vendor before isolating — manual overrides must be verified first."
        },
        {
            "name": "4. Eradication",
            "icon": "🧹",
            "color": "#F44336",
            "description": "Remove the threat actor and all artifacts from the environment.",
            "activities": [
                "Identify and remove all malware, backdoors, and persistence mechanisms",
                "Patch exploited vulnerabilities",
                "Rebuild compromised systems from known-good images",
                "Validate Active Directory integrity; check for rogue accounts",
                "Scan environment with updated signatures to confirm eradication",
                "Review privileged account activity for unauthorized changes",
            ],
            "durham_context": "SCADA re-imaging requires vendor coordination — 48-hour minimum lead time."
        },
        {
            "name": "5. Recovery",
            "icon": "🔄",
            "color": "#9C27B0",
            "description": "Restore systems to normal operations and verify integrity.",
            "activities": [
                "Restore systems from clean backups (validate backup integrity first)",
                "Implement phased recovery: DR site → test → production",
                "Verify data integrity and completeness post-restoration",
                "Enhanced monitoring for 30 days post-recovery",
                "Gradually re-enable services; validate with business owners",
                "Confirm RTO/RPO targets were met; document deviations",
            ],
            "durham_context": "Public-facing services (water, traffic) prioritized per Tier 1 classification."
        },
        {
            "name": "6. Lessons Learned",
            "icon": "📚",
            "color": GOLD,
            "description": "Document findings and improve future response capability.",
            "activities": [
                "Conduct post-mortem meeting within 5 business days",
                "Document root cause analysis (RCA) and attack chain",
                "Update IR plan, playbooks, and detection rules",
                "Brief executive leadership and Council (if required)",
                "File IPC notification if personal information involved (MFIPPA s.48.6)",
                "Update risk register with new risk entries or adjusted scores",
                "Schedule follow-up tabletop exercise based on lessons learned",
            ],
            "durham_context": "MFIPPA breach notification to IPC must occur 'at the earliest opportunity' — target < 72 hours."
        },
    ]

    for phase in phases:
        with st.expander(f"{phase['icon']} {phase['name']}", expanded=False):
            st.markdown(f"**{phase['description']}**")
            st.markdown("")
            for act in phase["activities"]:
                st.markdown(f"- {act}")
            st.info(f"🏛️ **{cfg.organization.name} Context:** {phase['durham_context']}")

    # Visual timeline
    st.markdown("### IR Lifecycle Flow")
    fig = go.Figure()
    for i, phase in enumerate(phases):
        fig.add_trace(go.Scatter(
            x=[i], y=[0],
            mode="markers+text",
            marker=dict(size=40, color=phase["color"]),
            text=[phase["icon"]],
            textposition="middle center",
            name=phase["name"],
            hovertext=phase["description"],
        ))
        if i < len(phases) - 1:
            fig.add_annotation(
                x=i + 0.5, y=0, text="→", showarrow=False,
                font=dict(size=24, color="#555"),
            )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.5, 0.5]),
        height=120, margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — Tabletop Exercise Builder                          ║
# ╚══════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("### 🎯 Interactive Tabletop Exercise")
    st.markdown("Walk through a scenario with decision-based branching.")

    # Tabletop exercise guide (learning mode)
    if lc.get("tabletop_guide"):
        tg = lc["tabletop_guide"]
        learning_section(tg["title"], tg["content"], icon="🎯")
        if is_learning_mode():
            with st.expander("📝 Tips for Effective Tabletop Exercises", expanded=False):
                for tip in tg.get("tips", []):
                    st.markdown(f"- {tip}")

    EXERCISES = {
        "Ransomware Attack on Financial Systems": {
            "inject": "At 6:30 AM Monday, the IT help desk receives multiple calls reporting that staff cannot access the ERP Financial System. Screen displays show a ransom note demanding 50 BTC. The attack appears to have spread from a phishing email opened Friday afternoon.",
            "questions": [
                {
                    "question": "The attacker demands 50 BTC within 48 hours. What is your immediate response?",
                    "options": {
                        "Do NOT pay — initiate IR plan and contact law enforcement": {
                            "feedback": "✅ CORRECT. Durham's policy prohibits ransom payments. Engage OPP Cyber Crime unit and activate IR plan.",
                            "score": 10,
                        },
                        "Pay the ransom to restore services quickly": {
                            "feedback": "❌ INCORRECT. Paying ransom funds criminal activity, does not guarantee decryption, and may violate sanctions. Durham policy prohibits payment.",
                            "score": 0,
                        },
                        "Negotiate to reduce the ransom amount": {
                            "feedback": "⚠️ PARTIAL. While negotiation may buy time, Durham's policy prohibits ransom payments. Focus should be on containment and recovery.",
                            "score": 3,
                        },
                    },
                },
                {
                    "question": "Lateral movement is detected toward the Water Treatment SCADA network. What do you do?",
                    "options": {
                        "Immediately isolate the IT/OT boundary and verify SCADA manual override capability": {
                            "feedback": "✅ CORRECT. Protect life-safety OT systems first. Verify operators can maintain manual control before network isolation.",
                            "score": 10,
                        },
                        "Monitor the activity to gather more intelligence before acting": {
                            "feedback": "❌ INCORRECT. OT/SCADA compromise is a life-safety risk. Immediate containment takes priority over intelligence gathering.",
                            "score": 0,
                        },
                        "Shut down all network connectivity region-wide": {
                            "feedback": "⚠️ PARTIAL. Over-isolation can disrupt emergency services. Targeted IT/OT segmentation is preferred.",
                            "score": 5,
                        },
                    },
                },
                {
                    "question": "Personal information (SIN numbers) of 500 social services clients may have been exfiltrated. What is the notification obligation?",
                    "options": {
                        "Notify the IPC Ontario at the earliest opportunity per MFIPPA s.48.6 and affected individuals": {
                            "feedback": "✅ CORRECT. MFIPPA requires notification to IPC 'at the earliest opportunity'. Affected individuals must also be notified.",
                            "score": 10,
                        },
                        "Wait for forensic confirmation before any notification": {
                            "feedback": "⚠️ PARTIAL. While full investigation is important, MFIPPA requires notification based on reasonable belief, not confirmed evidence.",
                            "score": 4,
                        },
                        "No notification required — this is an internal IT matter": {
                            "feedback": "❌ INCORRECT. SIN numbers are highly sensitive personal information. MFIPPA breach notification is mandatory.",
                            "score": 0,
                        },
                    },
                },
                {
                    "question": "72 hours post-incident, systems are recovered from backup. What comes next?",
                    "options": {
                        "Conduct post-mortem within 5 business days, update IR plan, and brief Council": {
                            "feedback": "✅ CORRECT. Lessons learned meeting is critical. Update playbooks, detection rules, and brief leadership per governance requirements.",
                            "score": 10,
                        },
                        "Return to normal operations — the incident is over": {
                            "feedback": "❌ INCORRECT. Without lessons learned, the same attack vector may be exploited again. Post-mortem is mandatory per IR plan.",
                            "score": 0,
                        },
                        "Focus only on technical remediation and patching": {
                            "feedback": "⚠️ PARTIAL. Technical fixes are necessary but insufficient. Process, people, and governance improvements are equally important.",
                            "score": 5,
                        },
                    },
                },
            ],
        },
        "Insider Threat — Data Exfiltration": {
            "inject": "An HR manager notices unusual activity: a departing IT administrator has been accessing Social Services case files outside their role. DLP alerts show 2.4 GB of data transferred to a personal cloud storage account over the past week.",
            "questions": [
                {
                    "question": "What is the first action to take upon receiving this report?",
                    "options": {
                        "Preserve evidence (logs, DLP alerts), restrict the account, and engage HR and Legal": {
                            "feedback": "✅ CORRECT. Evidence preservation is critical. Restrict access without alerting the subject. Coordinate with HR and Legal for employment law considerations.",
                            "score": 10,
                        },
                        "Immediately confront the employee": {
                            "feedback": "❌ INCORRECT. Confrontation may cause evidence destruction. Legal and HR must be involved before any employee interaction.",
                            "score": 0,
                        },
                        "Disable the account immediately and investigate later": {
                            "feedback": "⚠️ PARTIAL. Account restriction is correct, but abrupt disabling without evidence preservation may lose forensic data.",
                            "score": 5,
                        },
                    },
                },
                {
                    "question": "The exfiltrated data contains personal information of vulnerable persons (child welfare cases). What are the privacy implications?",
                    "options": {
                        "Extremely serious — MFIPPA breach, potential CYFSA implications, mandatory IPC notification": {
                            "feedback": "✅ CORRECT. Child welfare data is among the most sensitive categories. IPC notification is mandatory. CYFSA (Child, Youth and Family Services Act) may also apply.",
                            "score": 10,
                        },
                        "Standard privacy breach — handle through normal channels": {
                            "feedback": "❌ INCORRECT. This involves highly sensitive data about vulnerable persons. Elevated response is required.",
                            "score": 2,
                        },
                    },
                },
            ],
        },
    }

    selected_exercise = st.selectbox("Select Tabletop Scenario", list(EXERCISES.keys()))
    exercise = EXERCISES[selected_exercise]

    st.markdown("#### Scenario Inject")
    st.warning(exercise["inject"])

    total_score = 0
    max_score = len(exercise["questions"]) * 10

    for i, q in enumerate(exercise["questions"]):
        st.markdown(f"---")
        st.markdown(f"**Decision Point {i+1}:** {q['question']}")
        choice = st.radio(
            "Select your response:",
            list(q["options"].keys()),
            key=f"tabletop_{selected_exercise}_{i}",
            index=None,
        )
        if choice:
            result = q["options"][choice]
            if result["score"] >= 8:
                st.success(result["feedback"])
            elif result["score"] >= 4:
                st.warning(result["feedback"])
            else:
                st.error(result["feedback"])
            total_score += result["score"]

    if any(
        st.session_state.get(f"tabletop_{selected_exercise}_{i}") is not None
        for i in range(len(exercise["questions"]))
    ):
        st.markdown("---")
        pct = round((total_score / max_score) * 100) if max_score > 0 else 0
        st.markdown(f"### 📊 Exercise Score: **{total_score}/{max_score}** ({pct}%)")
        if pct >= 80:
            st.success("Excellent performance! Strong IR decision-making demonstrated.")
        elif pct >= 50:
            st.warning("Adequate performance. Review areas marked with ⚠️ for improvement.")
        else:
            st.error("Needs significant improvement. Schedule additional IR training.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 3 — Post-Mortem Generator                              ║
# ╚══════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown("### 📝 Post-Mortem Report Generator")
    st.markdown("Complete the form below to generate a structured post-mortem document.")

    with st.form("postmortem_form"):
        col1, col2 = st.columns(2)
        with col1:
            inc_id = st.text_input("Incident ID", value="INC-2024-001")
            inc_date = st.date_input("Incident Date")
            inc_type = st.selectbox("Incident Type", [
                "Ransomware", "Phishing", "Data Breach", "DDoS",
                "Insider Threat", "OT/SCADA Compromise", "Unauthorized Access",
                "System Outage", "Malware", "Other"
            ])
            severity = st.selectbox("Severity", ["P1 — Critical", "P2 — High", "P3 — Medium", "P4 — Low"])

        with col2:
            lead = st.text_input("Incident Commander", "Senior Cybersecurity Specialist")
            affected_systems = st.text_area("Affected Systems", "ERP Financial System, M365 Email")
            detection_method = st.selectbox("Detection Method", [
                "SIEM Alert", "User Report", "EDR Alert", "DLP Alert",
                "Network Anomaly", "Vendor Notification", "External Report"
            ])

        st.markdown("#### Timeline")
        timeline = st.text_area(
            "Event Timeline (one event per line)",
            "06:30 — Help desk receives first reports of inaccessible systems\n"
            "06:45 — SIEM analyst confirms ransomware indicators\n"
            "07:00 — CISO notified; IR plan activated\n"
            "07:15 — Affected systems isolated from network\n"
            "07:30 — Forensic evidence preservation initiated\n"
            "12:00 — Scope determined: 3 systems affected, no OT impact\n"
            "18:00 — Eradication complete; rebuild from clean backups initiated\n"
            "Day 2 08:00 — Systems restored and validated\n"
            "Day 3 — Enhanced monitoring confirmed no re-infection",
            height=200,
        )

        root_cause = st.text_area("Root Cause Analysis", "Phishing email bypassed email gateway. User clicked link and entered credentials on spoofed login page. Attacker used stolen credentials to deploy ransomware via RDP.")
        lessons = st.text_area(
            "Lessons Learned & Action Items",
            "1. Implement conditional access policies to block legacy auth\n"
            "2. Deploy phishing-resistant MFA (FIDO2/passkeys)\n"
            "3. Enhance email gateway rules for lookalike domains\n"
            "4. Conduct targeted phishing awareness for Finance department\n"
            "5. Update IR playbook with ransomware-specific decision tree",
        )

        submitted = st.form_submit_button("📄 Generate Post-Mortem", type="primary")

    if submitted:
        st.markdown("---")
        st.markdown(f"## Post-Mortem Report: {inc_id}")
        st.markdown(f"**Date:** {inc_date} | **Type:** {inc_type} | **Severity:** {severity}")
        st.markdown(f"**Incident Commander:** {lead}")
        st.markdown(f"**Detection Method:** {detection_method}")
        st.markdown(f"**Affected Systems:** {affected_systems}")
        st.markdown("### Timeline of Events")
        for line in timeline.strip().split("\n"):
            if line.strip():
                st.markdown(f"- {line.strip()}")
        st.markdown("### Root Cause Analysis")
        st.markdown(root_cause)
        st.markdown("### Lessons Learned & Action Items")
        for line in lessons.strip().split("\n"):
            if line.strip():
                st.markdown(f"- {line.strip()}")
        st.markdown("---")
        st.info("💡 In production, this would export to PDF and be logged in the IR tracking system.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 4 — Communication Templates                            ║
# ╚══════════════════════════════════════════════════════════════╝
with tab4:
    st.markdown("### 📨 Incident Communication Templates")
    st.markdown("Pre-built templates for stakeholder communication during incidents.")

    templates = {
        "Executive Notification (P1/P2)": {
            "audience": "CAO, Department Directors, Council (if required)",
            "timing": "Within 1 hour of incident declaration",
            "template": """**INCIDENT NOTIFICATION — CONFIDENTIAL**

**To:** Chief Administrative Officer, [Department] Director
**From:** Chief Information Security Officer
**Date:** {date}
**Subject:** Security Incident — {type} — Severity {severity}

**Summary:**
A {type} security incident has been detected affecting {systems}. The incident was detected at {time} via {method}.

**Current Status:** Containment in progress.

**Impact Assessment:**
- Systems affected: {systems}
- Data at risk: [Under investigation]
- Service disruption: [Details]
- Public impact: [Assessment]

**Actions Taken:**
1. Incident Response Plan activated
2. Affected systems isolated
3. Forensic investigation initiated
4. [Additional actions]

**Next Steps:**
- Status update in 4 hours
- Post-mortem within 5 business days

**Contact:** Senior Cybersecurity Specialist — [phone]""",
        },
        "IPC Ontario — Privacy Breach Notification": {
            "audience": "Information and Privacy Commissioner of Ontario",
            "timing": "At the earliest opportunity (target < 72 hours)",
            "template": """**PRIVACY BREACH NOTIFICATION — MFIPPA s.48.6**

**To:** Information and Privacy Commissioner of Ontario
**From:** Region of Durham — Head of Institution
**Date:** {date}

**1. Description of the Breach:**
On {date}, the Region of Durham identified a privacy breach involving {description}.

**2. Personal Information Involved:**
- Types of information: [e.g., SIN, health information, addresses]
- Number of individuals affected: [count]
- Sensitivity level: [High/Medium]

**3. Containment Measures:**
[Details of steps taken to contain the breach]

**4. Notification to Affected Individuals:**
[Plan for notifying affected individuals, including timeline and method]

**5. Steps to Prevent Recurrence:**
[Remediation actions and preventive measures]

**6. Contact Information:**
Region of Durham — Privacy Office
[Contact details]""",
        },
        "Staff-Wide Communication": {
            "audience": "All Regional Staff",
            "timing": "Within 4 hours (for user-impacting incidents)",
            "template": """**INFORMATION TECHNOLOGY SERVICE UPDATE**

**To:** All Regional Staff
**From:** IT Services
**Date:** {date}

We are aware of a service disruption affecting {systems}.

**What happened:** Our IT team identified a technical issue that is impacting access to certain systems.

**What we're doing:** Our cybersecurity and infrastructure teams are actively working to resolve the issue. We are following our established incident response procedures.

**What you should do:**
- Do NOT attempt to access affected systems
- Report any suspicious activity to the IT Help Desk
- Do NOT share details of this incident on social media
- Use alternative procedures provided by your department

**Expected resolution:** We will provide an update by {time}.

For questions, contact the IT Help Desk at [phone/email].""",
        },
    }

    selected_template = st.selectbox("Select Template", list(templates.keys()))
    tmpl = templates[selected_template]

    st.markdown(f"**Audience:** {tmpl['audience']}")
    st.markdown(f"**Timing:** {tmpl['timing']}")
    st.code(tmpl["template"], language="markdown")
    st.info("📋 Copy and customize the template above with incident-specific details.")
