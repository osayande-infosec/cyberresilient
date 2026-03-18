# DurhamResilient

**Municipal Cybersecurity Resilience Platform**

Built for the Region of Durham by Osayande Agbonkpolor — Senior Cybersecurity Specialist Interview Showcase.

---

## Overview

DurhamResilient is a five-module cybersecurity command center designed for municipal government operations. It delivers real-time security posture visibility, disaster recovery simulation, incident response management, risk assessment, and compliance tracking — all aligned to frameworks and regulations relevant to Ontario municipalities.

---

## Modules

| # | Module | Purpose |
|---|--------|---------|
| 1 | **Executive Dashboard** | Security score gauge, KPI cards, incident trends, department radar comparison |
| 2 | **DR/BC Simulator** | RTO/RPO simulation across 8 municipal systems and 5 threat scenarios with RACI generation |
| 3 | **Incident Response Center** | NIST 800-61r2 IR lifecycle, tabletop exercises, post-mortem generator, communication templates |
| 4 | **Risk Register & Architecture Advisor** | 5×5 heat map, 10 scored risks, 10-point vendor security assessment |
| 5 | **Compliance & Policy Tracker** | NIST CSF 2.0, ISO 27001:2022, MFIPPA mapping, policy lifecycle, audit readiness score |

---

## Durham Region Alignment

| JD Requirement | Module | Evidence |
|---|---|---|
| Cybersecurity risk assessment | Risk Register | 5×5 matrix, mitigation tracking |
| Disaster recovery & business continuity | DR/BC Simulator | RTO/RPO simulation, recovery checklists |
| Incident response planning | IR Center | Tabletop exercises, post-mortem reports |
| Security architecture reviews | Architecture Advisor | 10-point vendor assessment |
| Compliance & regulatory frameworks | Compliance Tracker | NIST CSF 2.0, ISO 27001, MFIPPA |
| OT/SCADA security | Systems & Scenarios | Water/wastewater SCADA with OT controls |
| Executive reporting | PDF Export | Downloadable DR and risk reports |

---

## Quick Start

### Local

```bash
git clone https://github.com/osayande-infosec/durhamresilient.git
cd durhamresilient
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

### Docker

```bash
docker compose up --build -d
```

### AWS ECS Fargate

```bash
# Authenticate, build, push to ECR, then force deploy
./deploy.sh
```

See `ecs-task-definition.json` for the Fargate task config.

---

## Project Structure

```
├── app.py                      # Landing page & Streamlit entry point
├── pages/
│   ├── 1_Dashboard.py          # Executive Security Posture Dashboard
│   ├── 2_DR_Simulator.py       # DR/BC Simulator
│   ├── 3_Incident_Response.py  # IR Center & Tabletop Exercises
│   ├── 4_Risk_Register.py      # Risk Register & Architecture Advisor
│   └── 5_Compliance.py         # Compliance & Policy Tracker
├── utils/                      # Simulation engines, scoring, PDF generation
├── data/                       # JSON data files (KPIs, systems, risks, controls, policies)
├── Dockerfile                  # Multi-stage hardened build (non-root, healthcheck)
├── docker-compose.yml
├── ecs-task-definition.json    # AWS Fargate task definition
└── deploy.sh                   # AWS deployment script
```

---

## Tech Stack

Python 3.11 · Streamlit · Plotly · Pandas · fpdf2 · matplotlib

---

## Security

- Non-root container user (`appuser`, UID 1000)
- ECR image scanning on push
- Healthcheck on `/_stcore/health`
- No external database — all data is local JSON
- **Stateless simulation** — DR simulator uses randomized variance for realistic variability
- **Dark theme** — Professional presentation with gold (#C9A84C) accent
- **Modular utilities** — Scoring, simulation, and PDF logic separated from UI

---

## 📋 Frameworks & Standards Referenced

- NIST Cybersecurity Framework (CSF) v2.0
- NIST SP 800-61r2 (Incident Handling)
- NIST SP 800-53 (Security Controls)
- ISO/IEC 27001:2022 (Annex A)
- CIS Controls v8
- OWASP API Security Top 10
- MFIPPA (Municipal Freedom of Information and Protection of Privacy Act)
- CYFSA (Child, Youth and Family Services Act)
- PIPEDA (Personal Information Protection and Electronic Documents Act)

---

## 👤 Author

**Osayande** — Cybersecurity Professional  
Built as a technical showcase for the Region of Durham Senior Cybersecurity Specialist role.

---

## 📄 License

This project is for interview/demonstration purposes.
