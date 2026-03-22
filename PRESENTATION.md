# DurhamResilient — Deep Dive Presentation

## Municipal Cybersecurity Resilience Platform

**Presented by:** Osayande Agbonkpolor
**Position:** Senior Cybersecurity Specialist Interview Showcase
**Built for:** The Region of Durham

---

## Table of Contents

1. [Opening Statement](#opening-statement)
2. [Platform Overview & Architecture](#platform-overview--architecture)
3. [Module 1 — Executive Dashboard](#module-1--executive-dashboard)
4. [Module 2 — DR/BC Simulator](#module-2--drbc-simulator)
5. [Module 3 — Incident Response Center](#module-3--incident-response-center)
6. [Module 4 — Risk Register & Architecture Advisor](#module-4--risk-register--architecture-advisor)
7. [Module 5 — Compliance Tracker](#module-5--compliance-tracker)
8. [Municipal Systems Inventory](#municipal-systems-inventory)
9. [Threat Scenarios](#threat-scenarios)
10. [Docker & Deployment Security](#docker--deployment-security)
11. [Durham Alignment & Ontario-Specific Intelligence](#durham-alignment--ontario-specific-intelligence)
12. [Talking Points & Demo Walkthrough](#talking-points--demo-walkthrough)
13. [Corrections & Refinements Made](#corrections--refinements-made)
14. [Deployment Commands Reference](#deployment-commands-reference)
15. [Closing Statement](#closing-statement)

---

## Opening Statement

> "Good afternoon. I'm Osayande Agbonkpolor, and I've built DurhamResilient — a comprehensive cybersecurity resilience platform designed specifically for the Region of Durham's municipal operations. This isn't a generic security dashboard. Every data point, every scenario, every compliance framework is mapped to Durham's real infrastructure — from Water Treatment SCADA to Social Services case management — and Ontario's regulatory landscape including MFIPPA and the Ontario Cyber Security Framework. Let me walk you through it."

---

## Platform Overview & Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Python 3.11 + Streamlit (multi-page) |
| **Visualization** | Plotly, Matplotlib |
| **Data Layer** | Pandas, JSON-based data models |
| **PDF Export** | FPDF2 |
| **Presentation Export** | python-pptx |
| **Containerization** | Docker (multi-stage, non-root) |
| **Cloud Hosting** | AWS Fargate (ECS + ECR) |
| **Theme** | Dark mode — primaryColor `#C9A84C` (gold), backgroundColor `#0A0A0A` |

### Application Structure

```
DurhamResilient/
├── app.py                          # Landing page & Streamlit entry point
├── pages/
│   ├── 1_Dashboard.py              # Executive dashboard with 8 KPIs
│   ├── 2_DR_Simulator.py           # DR/BC simulation engine
│   ├── 3_Incident_Response.py      # IR lifecycle & tabletop exercises
│   ├── 4_Risk_Register.py          # Risk heat map & architecture advisor
│   └── 5_Compliance.py             # Frameworks, sunburst, audit score
├── utils/
│   ├── risk_calculator.py          # Risk scoring engine (5×5 matrix)
│   ├── dr_simulator.py             # DR simulation logic & RACI generator
│   ├── compliance_scorer.py        # NIST CSF & ISO 27001 scoring
│   └── pdf_generator.py           # PDF export for reports
├── data/
│   ├── risks.json                  # 12 risk register entries
│   ├── systems.json                # 8 municipal systems
│   ├── scenarios.json              # 5 threat scenarios
│   ├── nist_csf.json               # NIST CSF 2.0 controls
│   ├── iso27001.json               # ISO 27001:2022 controls
│   └── policies.json               # Policy lifecycle data
├── Dockerfile                      # Multi-stage, security-hardened
├── docker-compose.yml              # Local orchestration
├── ecs-task-definition.json        # AWS Fargate deployment
├── deploy.sh                       # Deployment automation
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

### Five Modules at a Glance

| # | Module | Purpose |
|---|--------|---------|
| 1 | **Executive Dashboard** | Real-time security posture, 8 KPIs, department risk radar |
| 2 | **DR/BC Simulator** | Test disaster recovery against 5 threat scenarios, RACI generation |
| 3 | **Incident Response** | IR lifecycle (NIST 800-61r2), tabletop exercises, post-mortem generator |
| 4 | **Risk Register** | 5×5 heat map, 12 risks, 10-point architecture security advisor |
| 5 | **Compliance Tracker** | NIST CSF 2.0, ISO 27001:2022, MFIPPA, audit readiness composite score |

---

## Module 1 — Executive Dashboard

### 8 Key Performance Indicators

| KPI | Value | Trend | Context |
|-----|-------|-------|---------|
| **Security Score** | 78/100 | — | Composite organizational score |
| **MTTD** | 2.4 hrs | ↓12% | Mean Time to Detect |
| **MTTR** | 6.8 hrs | ↓8% | Mean Time to Respond |
| **Critical Vulnerabilities** | 7 | -3 | Open critical findings |
| **Active Incidents** | 2 | — | Currently being managed |
| **Patch Compliance** | 91.3% | ↑2.1% | Systems up to date |
| **DR Readiness** | 85% | — | Tested recovery capability |
| **MFA Coverage** | 98.5% | ↑1.5% | Accounts with MFA enabled |

### Talking Point — KPIs

> "These aren't vanity metrics. MTTD at 2.4 hours means we're detecting threats faster than the industry average of 197 days for advanced persistent threats. The 12% improvement shows the SOC maturity program is working. And with 98.5% MFA coverage, we're closing the number one attack vector — credential compromise."

### Security Score Gauge

- **Dial chart**: 0–100 scale with color zones
- **0–40**: 🔴 Critical (immediate attention)
- **40–70**: 🟡 Needs Improvement
- **70–100**: 🟢 Good posture
- **Current**: 78/100 — solid but room for growth

### Department Risk Comparison (Radar Chart)

7 departments plotted across 5 axes:

| Department | Risk Score | Compliance | Incidents | Vulnerability | Training |
|-----------|-----------|-----------|----------|--------------|---------|
| Public Works | 72 | 78 | 85 | 70 | 88 |
| Public Health | 65 | 82 | 90 | 75 | 85 |
| Finance | 70 | 88 | 82 | 80 | 90 |
| IT Services | 80 | 85 | 78 | 65 | 92 |
| Water & Wastewater | 85 | 70 | 75 | 60 | 78 |
| Social Services | 68 | 80 | 88 | 78 | 82 |
| Planning & Development | 55 | 85 | 92 | 82 | 80 |

### Talking Point — Radar Chart

> "The radar chart is where department heads pay attention. Water & Wastewater scores 85 on risk — highest in the region — because they operate OT/SCADA systems that are inherently harder to secure. But look at their compliance at 70% — that's our remediation target for Q3. Conversely, Planning & Development has the lowest risk score at 55 because they're primarily IT-based with less critical infrastructure exposure."

### Additional Visualizations

- **Monthly Incident Trend**: Line chart (12 months) — incidents, resolved, pending
- **Vulnerability Severity Distribution**: Donut chart — Critical/High/Medium/Low
- **Compliance Framework Scores**: Grouped bar chart — NIST CSF (81%), ISO 27001 (76%), MFIPPA

---

## Module 2 — DR/BC Simulator

### How It Works

1. **Select** a municipal system (8 available)
2. **Select** a threat scenario (5 available)
3. **Run simulation** — calculates estimated RTO/RPO using:

$$\text{Estimated RTO} = \text{Target RTO} \times \text{Scenario Multiplier} \times \text{Variance}_{(0.85–1.25)}$$

4. **Results** show pass/fail against targets with gap analysis
5. **RACI matrix** auto-generates for the recovery workflow
6. **PDF export** packages everything for executive reporting

### 8 Municipal Systems

| ID | System | Type | Tier | RTO | RPO | DR Strategy |
|---|--------|------|------|-----|-----|------------|
| SYS-001 | Public Health Electronic Records | IT | 1 (Critical) | 4h | 1h | Warm Standby |
| SYS-002 | Water Treatment SCADA | OT | 1 (Critical) | 2h | 0.5h | Hot Standby + Manual Override |
| SYS-003 | ERP Financial System | IT | 1 (Critical) | 4h | 1h | Pilot Light (AWS) |
| SYS-004 | Traffic Management System | OT | 2 | 8h | 4h | Cold Standby |
| SYS-005 | Email & Collaboration (M365) | Cloud | 1 (Critical) | 1h | 15min | Cloud-Native Redundancy |
| SYS-006 | Social Services Case Mgmt | IT | 2 | 8h | 4h | Vendor-Managed DR |
| SYS-007 | Wastewater SCADA | OT | 1 (Critical) | 2h | 0.5h | Hot Standby + Manual Override |
| SYS-008 | GIS & Mapping Platform | IT | 3 | 24h | 8h | Backup & Restore |

### 5 Threat Scenarios

| ID | Scenario | Severity | Affected Systems | Est. Downtime |
|---|----------|----------|------------------|---------------|
| SCN-001 | Ransomware Attack — Municipal Network | 🔴 Critical | ERP, M365, Case Mgmt | 12 hours |
| SCN-002 | Cloud Region Outage — Azure East Canada | 🟠 High | Public Health, M365 | 6 hours |
| SCN-003 | OT Compromise — Water Treatment SCADA | 🔴 Critical | Water Treatment SCADA | 8 hours |
| SCN-004 | Insider Threat — Data Exfiltration | 🟠 High | Case Management | 0 hours |
| SCN-005 | Hardware Failure — Primary Data Center | 🟡 Medium | ERP, Traffic, GIS | 4 hours |

### RACI Matrix (Auto-Generated)

8 activities mapped to 5 roles for every simulation:

| Activity | IT Security | IT Ops | Business | Executive | Legal/PR |
|----------|:---------:|:------:|:--------:|:---------:|:--------:|
| Declare DR Event | **R** | C | I | **A** | I |
| Activate Recovery Plan | I | **R** | I | **A** | I |
| Communications | I | I | C | **A** | **R** |
| System Recovery | C | **R** | I | I | I |
| Data Validation | **R** | C | **A** | I | I |
| Service Restoration | I | **R** | **A** | I | I |
| Post-Incident Review | **R** | C | C | **A** | I |
| Documentation | **R** | C | I | **A** | C |

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

### Talking Point — DR Simulator

> "This is the module that proves readiness. Instead of just saying 'we have a DR plan,' I can run Water Treatment SCADA against an OT compromise scenario right now and show you whether our 2-hour RTO target holds. The 2.0× multiplier for OT attacks reflects the reality that SCADA recovery involves manual industrial process validation — you can't just restore from backup and go. The RACI matrix eliminates the 'who does what?' confusion in a real crisis."

---

## Module 3 — Incident Response Center

### IR Lifecycle — 6 NIST 800-61r2 Phases

| Phase | Durham Context |
|-------|---------------|
| **1. Preparation** | Municipal IR team structure, contact lists, tool readiness, OT isolation procedures |
| **2. Detection & Analysis** | SIEM correlation, OT anomaly detection, triage criteria for municipal services |
| **3. Containment** | Short-term (isolate) vs. long-term (segment) — special handling for SCADA |
| **4. Eradication** | Root cause removal, reimaging, OT firmware verification |
| **5. Recovery** | Staged restoration per RTO tiers, service validation before public access |
| **6. Lessons Learned** | Post-mortem with all stakeholders, playbook updates, council briefing |

### 2 Tabletop Exercises

#### Exercise 1: Ransomware Attack on Municipal Network

- **Total Points:** 40 (scored across decisions)
- **Scenario Stages:**
  - 🕐 Stage 1 — Initial Detection (SOC alert at 3 AM)
  - 🕐 Stage 2 — Scope Assessment (lateral movement detected)
  - 🕐 Stage 3 — Containment Decision (isolate vs. monitor)
  - 🕐 Stage 4 — Recovery & Communication

Each stage presents decision points with scoring:
- Correct decision: +10 points
- Partial credit: +5 points
- Incorrect: 0 points

**Scoring Thresholds:**
- 35-40: ✅ Excellent — IR team ready for real incident
- 25-34: ⚠️ Good — Minor gaps to address
- 15-24: 🟡 Needs Work — Schedule additional training
- 0-14: 🔴 Critical — Immediate remediation required

#### Exercise 2: Insider Threat — Data Exfiltration

- **Focus:** Social Services PII exfiltration
- **Key Decisions:** Account suspension timing, evidence preservation, IPC notification, staff communication
- **Ontario-Specific:** MFIPPA breach protocol, IPC (Information and Privacy Commissioner) obligations

### Post-Mortem Report Generator

Structured fields for comprehensive documentation:
- Incident ID & title
- Severity & category
- Detection timestamp & method
- Timeline of events
- Root cause analysis
- Impact assessment
- Remediation actions taken
- Lessons learned
- Playbook updates required

### 3 Communication Templates

#### Template 1: Executive Briefing
- **Audience:** CAO, Regional Council
- **Content:** Incident summary, impact to services, current status, remediation timeline
- **Tone:** Concise, decisive, no technical jargon

#### Template 2: IPC Ontario Notification
- **Audience:** Information and Privacy Commissioner of Ontario
- **Content:** Nature of breach, personal information affected, individuals impacted, containment measures, notification plan
- **Ontario-Specific:** MFIPPA Section 28(2) breach notification requirements
- **Timeline:** Must notify at earliest reasonable opportunity (target < 72 hours)

#### Template 3: Staff-Wide Communication
- **Audience:** All 4,000+ regional employees
- **Content:** What happened (high level), what we're doing, what staff should do, who to contact
- **Tone:** Reassuring, actionable, non-alarmist

### Talking Point — Incident Response

> "The IR Center isn't just a reference document — it's an interactive training platform. The tabletop exercises force real decision-making under pressure. When I run the ransomware tabletop, participants have to decide: Do we isolate the network immediately and accept the service disruption, or do we monitor for 30 more minutes to understand scope? Both are defensible — but the scoring reflects municipal reality. In government, a 30-minute delay with citizen data at risk is rarely the right call."

---

## Module 4 — Risk Register & Architecture Advisor

### Risk Heat Map — 5×5 Matrix

**Axes:**
- **X-axis (Likelihood):** 1 (Rare) → 5 (Almost Certain)
- **Y-axis (Impact):** 1 (Negligible) → 5 (Catastrophic)

**4-Level Risk Scale:**

| Level | Score Range | Color | Icon |
|-------|-----------|-------|------|
| **Low** | 1–4 | 🟢 Green (#4CAF50) | 🟢 |
| **Medium** | 5–9 | 🟡 Yellow (#FFC107) | 🟡 |
| **High** | 10–15 | 🟠 Orange (#FF9800) | 🟠 |
| **Very High** | 16–25 | 🔴 Red (#F44336) | 🔴 |

### 12 Risk Register Entries

| ID | Risk | L×I | Score | Level |
|----|------|-----|-------|-------|
| RISK-001 | Ransomware targeting municipal infrastructure | 4×5 | 20 | 🔴 Very High |
| RISK-002 | Unpatched OT/SCADA vulnerabilities | 3×5 | 15 | 🟠 High |
| RISK-003 | Phishing & credential compromise | 5×3 | 15 | 🟠 High |
| RISK-004 | Third-party vendor data breach | 3×4 | 12 | 🟠 High |
| RISK-005 | Insider threat — data exfiltration | 2×4 | 8 | 🟡 Medium |
| RISK-006 | Cloud misconfiguration (Azure/AWS) | 3×4 | 12 | 🟠 High |
| RISK-007 | Disaster recovery plan gaps | 3×5 | 15 | 🟠 High |
| RISK-008 | Legacy system end-of-life (Server 2012/2016) | 4×3 | 12 | 🟠 High |
| RISK-009 | Inadequate network segmentation | 3×4 | 12 | 🟠 High |
| RISK-010 | Compliance gaps — MFIPPA & Ontario Cyber Framework | 2×4 | 8 | 🟡 Medium |
| RISK-011 | Outdated security awareness training materials | 2×2 | 4 | 🟢 Low |
| RISK-012 | Physical access logging gaps at secondary facilities | 1×2 | 2 | 🟢 Low |

**Distribution:** Very High: 1 | High: 7 | Medium: 2 | Low: 2

### Architecture Security Advisor — 10-Point Vendor Assessment

| # | Control | Framework | Question |
|---|---------|-----------|----------|
| CHK-01 | Single Sign-On (SSO) Integration | NIST 800-53 IA-2 | Does solution support SAML/OIDC with Azure AD? |
| CHK-02 | Data Encryption at Rest | NIST 800-53 SC-28 | AES-256 encryption at rest? |
| CHK-03 | Data Encryption in Transit | NIST 800-53 SC-8 | TLS 1.2+ in transit? |
| CHK-04 | Multi-Factor Authentication | NIST 800-53 IA-2(1) | MFA enforced for all admin access? |
| CHK-05 | SOC 2 Type II Certification | AICPA TSC | Vendor holds current SOC 2 Type II? |
| CHK-06 | Data Residency (Canada) | MFIPPA/PIPEDA | All data stored/processed in Canada? |
| CHK-07 | Backup & Disaster Recovery | NIST 800-53 CP-9 | Automated backups with tested DR? |
| CHK-08 | Incident Notification SLA | NIST 800-53 IR-6 | Vendor notifies within 24 hours of breach? |
| CHK-09 | API Security | OWASP API Top 10 | APIs authenticated, rate-limited, logged? |
| CHK-10 | Vulnerability Management | CIS Control 7 | Vendor has vuln management & patching program? |

**Scoring:**
- 90–100%: 🟢 Low Risk
- 70–89%: 🟡 Medium Risk
- 50–69%: 🟠 High Risk
- < 50%: 🔴 Critical Risk

**Output:** Gauge chart, pass/fail counts, detailed findings for each failed control, PDF export

### Talking Point — Risk Register

> "This isn't a static spreadsheet. The 5×5 heat map is interactive — you can filter by risk level, status, or sort by score. RISK-001 (Ransomware) sits at 20 — the only Very High — because the likelihood of 4 reflects the reality of increased attacks on Canadian municipalities. The City of Hamilton, the Town of Wasaga Beach, the Municipal Property Assessment Corporation — these are real-world examples that directly inform our scoring. The Architecture Advisor gives the procurement team a structured 10-point checklist before signing any vendor contract."

---

## Module 5 — Compliance Tracker

### NIST CSF 2.0 — 6 Functions

| Function | Description | Score | Color |
|----------|-------------|-------|-------|
| **Govern** | Manage cybersecurity risk as part of overall governance | [%] | Purple |
| **Identify** | Develop organizational understanding to manage cybersecurity risk | [%] | Blue |
| **Protect** | Implement safeguards to ensure delivery of critical services | [%] | Green |
| **Detect** | Develop and implement activities to identify cybersecurity events | [%] | Orange |
| **Respond** | Develop incident response capabilities during events | [%] | Red |
| **Recover** | Develop recovery capabilities to restore systems/data | [%] | Gold |

**Overall NIST CSF 2.0 Score: 81%** (Target: 80%)

### Sunburst Visualization

- **Center:** "NIST CSF 2.0"
- **Ring 1:** 6 Functions with percentages
- **Ring 2:** Categories under each function, color-coded:
  - 🟢 Green: Implemented
  - 🟡 Yellow: Partial
  - 🔴 Red: Gap

### ISO 27001:2022 Compliance

- **Stacked bar chart** across 14 Annex A domains
- **Segments:** Implemented (green), Partial (yellow), Gap (red)
- **Overall Score: 76%**

### MFIPPA Compliance (Ontario-Specific)

| Requirement | Status | Detail |
|-------------|--------|--------|
| Privacy Impact Assessments (PIAs) | ✅ Implemented | Required for all new systems processing personal info |
| Access to Information Requests | ✅ Implemented | 30-day response window; tracked in FOIP system |
| Privacy Breach Protocol | ✅ Implemented | IPC notification at earliest opportunity; target < 72h |
| Data Minimization | ⚠️ Partial | Policy exists; enforcement gaps in legacy systems |
| Retention & Disposal Schedules | ⚠️ Partial | Schedules for most record types; OT data under review |
| Staff Privacy Training | ✅ Implemented | Annual mandatory with completion tracking |
| Third-Party Data Sharing Agreements | ⚠️ Partial | Templates exist; not all vendors have current DSAs |

### Policy Lifecycle Management

| Status | Icon | Description |
|--------|------|-------------|
| Current | ✅ | Active and up-to-date |
| Under Review | 🔄 | Being reviewed for updates |
| Draft | 📝 | New policy in development |
| Expired | ⛔ | Past review date |

### Audit Readiness Score — Composite Formula

$$\text{Audit Readiness} = (\text{NIST CSF 2.0} \times 0.40) + (\text{ISO 27001} \times 0.35) + (\text{Policy Currency} \times 0.25)$$

**Example:** $(81\% \times 0.40) + (76\% \times 0.35) + (X\% \times 0.25) = \text{Score}\%$

**Thresholds:**
- ≥ 80%: ✅ Strong audit readiness. Maintain current trajectory.
- 60–79%: ⚠️ Moderate readiness. Address gaps in NIST CSF and policy reviews.
- < 60%: ❌ Significant gaps. Prioritize compliance remediation immediately.

### Talking Point — Compliance

> "Compliance in a municipality isn't optional — it's legally mandated. MFIPPA is Ontario's version of FIPPA at the federal level, and it governs how we handle personal information. The sunburst chart gives an executive a one-glance view of where we stand across all 6 NIST CSF functions and their sub-categories. The audit readiness score — a weighted composite of NIST, ISO, and policy currency — tells you in a single number whether we're ready for an IPC audit. At 81% NIST and 76% ISO, we're in good shape but the 3 partial MFIPPA items need attention before the next review cycle."

---

## Municipal Systems Inventory

### 8 Systems — Full Detail

#### SYS-001: Public Health Electronic Records
- **Department:** Public Health | **Type:** IT | **Tier:** 1 (Critical)
- **Hosting:** Azure Hybrid | **RTO:** 4h | **RPO:** 1h
- **DR Strategy:** Warm Standby
- **Dependencies:** Azure AD, SQL Database, VPN Gateway
- **Last Test:** 2025-11-15 ✅ Pass

#### SYS-002: Water Treatment SCADA Network
- **Department:** Water & Wastewater | **Type:** OT | **Tier:** 1 (Critical)
- **Hosting:** On-Premises | **RTO:** 2h | **RPO:** 0.5h
- **DR Strategy:** Hot Standby + Manual Override
- **Dependencies:** PLCs, HMI Workstations, Historian Server, Firewall DMZ
- **Last Test:** 2025-08-22 ⚠️ Partial

#### SYS-003: ERP Financial System
- **Department:** Finance | **Type:** IT | **Tier:** 1 (Critical)
- **Hosting:** On-Premises + Cloud Backup | **RTO:** 4h | **RPO:** 1h
- **DR Strategy:** Pilot Light (AWS)
- **Dependencies:** Oracle DB, Application Server, Load Balancer, HSM
- **Last Test:** 2026-01-10 ✅ Pass

#### SYS-004: Traffic Management System
- **Department:** Public Works | **Type:** OT | **Tier:** 2
- **Hosting:** On-Premises | **RTO:** 8h | **RPO:** 4h
- **DR Strategy:** Cold Standby
- **Dependencies:** Traffic Controllers, Central Server, Fiber Network, UPS
- **Last Test:** 2025-06-30 ❌ Fail

#### SYS-005: Email & Collaboration (M365)
- **Department:** IT Services | **Type:** Cloud-Native | **Tier:** 1 (Critical)
- **Hosting:** Cloud (Microsoft 365) | **RTO:** 1h | **RPO:** 15min
- **DR Strategy:** Cloud-Native Redundancy
- **Dependencies:** Azure AD, Exchange Online, SharePoint, Teams
- **Last Test:** 2026-02-28 ✅ Pass

#### SYS-006: Social Services Case Management
- **Department:** Social Services | **Type:** IT | **Tier:** 2
- **Hosting:** Provincial Cloud | **RTO:** 8h | **RPO:** 4h
- **DR Strategy:** Vendor-Managed DR
- **Dependencies:** Provincial VPN, SAMS Application, Citrix Gateway
- **Last Test:** 2025-09-20 ✅ Pass

#### SYS-007: Wastewater SCADA Network
- **Department:** Water & Wastewater | **Type:** OT | **Tier:** 1 (Critical)
- **Hosting:** On-Premises | **RTO:** 2h | **RPO:** 0.5h
- **DR Strategy:** Hot Standby + Manual Override
- **Dependencies:** PLCs, HMI Workstations, Historian Server, Firewall DMZ
- **Last Test:** 2025-07-15 ⚠️ Partial

#### SYS-008: GIS & Mapping Platform
- **Department:** Planning & Development | **Type:** IT | **Tier:** 3
- **Hosting:** Hybrid (On-Prem + AWS) | **RTO:** 24h | **RPO:** 8h
- **DR Strategy:** Backup & Restore
- **Dependencies:** ArcGIS Server, PostgreSQL, S3 Storage
- **Last Test:** 2025-04-10 ✅ Pass

---

## Threat Scenarios

### SCN-001: Ransomware Attack — Municipal Network
- **Severity:** 🔴 Critical | **Affected:** ERP, M365, Case Management
- **Departments:** Finance, IT Services, Social Services
- **Downtime:** 12 hours | **RTO Multiplier:** 1.8× | **RPO Multiplier:** 1.5×
- **Public Impact:** Service disruptions in tax payments, social assistance
- **Recovery:** 10 steps — isolate, assess, preserve evidence, activate DR, restore, validation, re-image, AD verification, post-mortem, IPC notification

### SCN-002: Cloud Region Outage — Azure East Canada
- **Severity:** 🟠 High | **Affected:** Public Health, M365
- **Departments:** Public Health, IT Services, All (Azure AD)
- **Downtime:** 6 hours | **RTO Multiplier:** 1.3× | **RPO Multiplier:** 1.2×
- **Public Impact:** Immunization clinics disrupted, staff authentication failure
- **Recovery:** 8 steps — confirm status, activate comms, backup auth, failover, monitor, validation, lessons learned

### SCN-003: OT Compromise — Water Treatment SCADA
- **Severity:** 🔴 Critical | **Affected:** Water Treatment SCADA
- **Department:** Water & Wastewater
- **Downtime:** 8 hours | **RTO Multiplier:** 2.0× | **RPO Multiplier:** 1.0×
- **Public Impact:** Potential public health emergency — unsafe drinking water
- **Recovery:** 10 steps — manual override, isolation, VPN revocation, water quality check, IR activation, forensics, restoration, segmentation, MOE notification, joint post-mortem

### SCN-004: Insider Threat — Data Exfiltration
- **Severity:** 🟠 High | **Affected:** Case Management
- **Department:** Social Services
- **Downtime:** 0 hours | **RTO Multiplier:** 1.0× | **RPO Multiplier:** 1.0×
- **Public Impact:** Privacy breach affecting vulnerable population, IPC notification required
- **Recovery:** 10 steps — disable account, image workstation, DLP review, engage HR/Legal, scope assessment, IPC notification, client notification, enhanced DLP, offboarding checklist, lessons learned

### SCN-005: Hardware Failure — Primary Data Center
- **Severity:** 🟡 Medium | **Affected:** ERP, Traffic, GIS
- **Departments:** Finance, Public Works, Planning & Development
- **Downtime:** 4 hours | **RTO Multiplier:** 1.4× | **RPO Multiplier:** 1.3×
- **Public Impact:** Traffic signal disruption at major intersections, delayed financial processing
- **Recovery:** 9 steps — assess damage, activate backup power, ERP failover, manual traffic control, secondary boot, integrity checks, GIS restore, UPS repair, DR plan update

---

## Docker & Deployment Security

### Multi-Stage Dockerfile — Security Hardening

| Control | Implementation | Benefit |
|---------|---------------|---------|
| **Base Image** | python:3.11-slim | Minimal attack surface vs. full image |
| **Build Stage** | Multi-stage with separate builder | Dependencies don't ship in final image |
| **Package Cleanup** | `--no-install-recommends` + `rm -rf /var/lib/apt/lists/*` | Reduces image size and CVEs |
| **Non-Root User** | `appuser` (UID 1000, GID 1000) | Prevents container escape privilege escalation |
| **Directory Permissions** | `chown -R appuser:appuser /app` | User can't write outside /app |
| **Health Check** | `curl http://localhost:8501/_stcore/health` | 30s interval, 10s timeout, 3 retries |
| **Metadata Labels** | Maintainer, description, version | DocOps tracking and audit |
| **Streamlit Config** | `--server.headless=true`, `--browser.gatherUsageStats=false` | No telemetry, CLI-only operation |

### Hardening Checklist
- ✅ No vulnerable base layers
- ✅ Non-root user execution
- ✅ Minimal installed packages
- ✅ Health checks configured
- ✅ No unnecessary telemetry
- ✅ Explicit port/address configuration
- ✅ Clean layer strategy

---

## Durham Alignment & Ontario-Specific Intelligence

### Why This Matters for Durham

| Feature | Durham Relevance |
|---------|-----------------|
| **Water/Wastewater SCADA** | Durham operates 8 water treatment plants, 12 WPCPs — OT security is non-negotiable |
| **MFIPPA Compliance** | Ontario's Municipal Freedom of Information law governs every system processing PII |
| **IPC Breach Notification** | Ontario's Information and Privacy Commissioner requires notification at earliest opportunity |
| **Social Services PII** | Ontario Works case management handles vulnerable population data |
| **Provincial Integration** | SAMS application, Citrix Gateway — provincial dependencies |
| **7 Departments** | Maps exactly to Durham's organizational structure |
| **Azure AD** | Durham's identity provider — conditional access, MFA enforcement |
| **Multi-Tier Infrastructure** | IT + OT + Cloud — reflects Durham's actual hybrid environment |

### Ontario Regulatory Landscape

| Regulation | Coverage in Platform |
|-----------|---------------------|
| **MFIPPA** | Full compliance module, 7 requirements tracked, breach protocol |
| **Ontario Cyber Security Framework** | Risk register entries, compliance gap tracking |
| **PIPEDA** | Data residency checks in Architecture Advisor |
| **Municipal Act** | Council reporting templates, audit readiness |
| **Safe Drinking Water Act** | Water SCADA scenarios, MOE notification protocols |

---

## Talking Points & Demo Walkthrough

### Suggested Demo Flow (15-20 minutes)

1. **Landing Page** (1 min)
   - Show platform overview, five module navigation

2. **Dashboard** (3 min)
   - Walk through 8 KPIs, highlight MTTD/MTTR improvements
   - Show radar chart — explain Water & Wastewater risk profile
   - Reference security score of 78

3. **DR Simulator** (4 min)
   - Select "Water Treatment SCADA" + "OT Compromise"
   - Run simulation — discuss RTO/RPO results
   - Show RACI matrix — emphasize accountability clarity
   - Export PDF

4. **Incident Response** (3 min)
   - Walk through 6 NIST phases with Durham context
   - Start ransomware tabletop — make 1-2 decisions
   - Show IPC notification template — highlight MFIPPA compliance

5. **Risk Register** (3 min)
   - Show heat map — point out Very High ransomware risk
   - Filter to High risks — discuss top concerns
   - Demo Architecture Advisor — run 10-point assessment

6. **Compliance** (3 min)
   - Show sunburst for NIST CSF 2.0
   - Highlight MFIPPA section — discuss Ontario-specific requirements
   - Show audit readiness composite score

7. **Closing** (1 min)
   - Return to landing page, summarize value proposition

### Key Interview Questions & Prepared Responses

**Q: "How does this help Durham's security posture?"**
> "DurhamResilient provides centralized visibility across all security domains. Instead of managing risk in spreadsheets, DR plans in Word documents, and compliance in email threads, everything is unified with real-time scoring and interactive simulation. The audit readiness score alone saves weeks of preparation by continuously tracking our posture against three frameworks."

**Q: "How did you decide which systems to include?"**
> "The 8 systems map directly to Durham's critical infrastructure — Tier 1 systems like Water Treatment SCADA have 2-hour RTO because public health depends on it. I categorized by IT, OT, and Cloud to reflect the hybrid environment. Each system's RTO/RPO targets are based on industry standards for municipal government, adjusted for Durham's scale."

**Q: "What makes this different from commercial tools?"**
> "Commercial tools are generic. This platform knows that when Durham's Water Treatment SCADA is compromised, the first call isn't just to the SOC — it's to the Ministry of the Environment. The MFIPPA compliance module isn't an add-on — it's built into every incident response template. The tabletop exercises use Durham's actual systems, not hypothetical scenarios."

---

## Corrections & Refinements Made

### Rename: DurhamShield → DurhamResilient
- Updated naming across all files: `app.py`, 4 page modules, `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `ecs-task-definition.json`, `README.md`
- Zero legacy references remaining

### Risk Level Scale — 4 Iterations
1. **Initial:** 5-level scale (Low/Medium/High/Critical/Extreme)
2. **Round 1:** Changed to 4-level (Low/Medium/High/Critical)
3. **Round 2:** Changed to 4-level (Low/Medium/High/Very High) with corrected thresholds on a 5×5 matrix
4. **Final:** Low (1–4), Medium (5–9), High (10–15), Very High (16–25)
   - Added RISK-011 (Outdated training materials, score 4) and RISK-012 (Physical access logging gaps, score 2) to ensure Low category representation on the pie chart

### Footer Text Update
- Changed to: *"Built for the Region of Durham By Osayande Agbonkpolor for The Senior Cybersecurity Specialist Interview Showcase"*

---

## Deployment Commands Reference

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

### Docker Build & Run
```bash
# Build image
docker build -t durhamresilient .

# Run container
docker run -p 8501:8501 durhamresilient

# Or use docker-compose
docker-compose up --build -d
```

### AWS ECR + ECS Fargate Deployment

```bash
# 1. Authenticate AWS SSO
aws sso login --profile AdministratorAccess-181957456121

# 2. Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 --profile AdministratorAccess-181957456121 | docker login --username AWS --password-stdin 181957456121.dkr.ecr.us-east-1.amazonaws.com

# 3. Build, tag, and push
docker build -t durhamshield-durhamresilient .
docker tag durhamshield-durhamresilient:latest 181957456121.dkr.ecr.us-east-1.amazonaws.com/durhamshield:latest
docker push 181957456121.dkr.ecr.us-east-1.amazonaws.com/durhamshield:latest

# 4. Force new ECS deployment
aws ecs update-service --cluster durhamshield-cluster --service durhamshield-service --force-new-deployment --region us-east-1 --profile AdministratorAccess-181957456121
```

### Scale Down (Stop Billing) / Scale Up
```bash
# Scale to 0 (stop billing ~$32.50/mo)
aws ecs update-service --cluster durhamshield-cluster --service durhamshield-service --desired-count 0 --region us-east-1 --profile AdministratorAccess-181957456121

# Scale back up
aws ecs update-service --cluster durhamshield-cluster --service durhamshield-service --desired-count 1 --region us-east-1 --profile AdministratorAccess-181957456121
```

### Git Push
```bash
git add -A
git commit -m "your message"
git push origin main
```

---

## Closing Statement

> "DurhamResilient demonstrates that cybersecurity in municipal government isn't just about buying tools — it's about building operational resilience that's specific to your environment, your regulations, and your infrastructure. Every module in this platform maps to a real Durham challenge, from SCADA security to MFIPPA compliance. I built this to show not just what I know, but how I think about security in a municipal context. Thank you."

---

## Summary Statistics

| Category | Total | Notes |
|----------|-------|-------|
| **Pages** | 5 | Dashboard, DR Simulator, Incident Response, Risk Register, Compliance |
| **Municipal Systems** | 8 | IT (4), OT (3), Cloud (1) |
| **Threat Scenarios** | 5 | 2 Critical, 2 High, 1 Medium |
| **Risk Entries** | 12 | Very High: 1, High: 7, Medium: 2, Low: 2 |
| **Architecture Checks** | 10 | NIST, CIS, OWASP, AICPA, MFIPPA |
| **NIST CSF Functions** | 6 | Govern, Identify, Protect, Detect, Respond, Recover |
| **IR Lifecycle Phases** | 6 | NIST 800-61r2 |
| **Tabletop Exercises** | 2 | Ransomware, Insider Threat |
| **Communication Templates** | 3 | Executive, IPC Notification, Staff-Wide |
| **Departments** | 7 | Public Works, Health, Finance, IT, Water, Social Services, Planning |
| **Compliance Frameworks** | 3+ | NIST CSF 2.0, ISO 27001:2022, MFIPPA |
| **RACI Activities** | 8 | Auto-generated per DR simulation |
