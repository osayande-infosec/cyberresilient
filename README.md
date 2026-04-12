# CyberResilient 🛡️

**Enterprise Cybersecurity Training Toolkit**

An open-source, hands-on cybersecurity training platform built with Streamlit. Practice real-world security operations — from executive dashboards and risk management to incident response tabletops and MITRE ATT&CK threat mapping — in a safe, interactive environment.

**Live Demo:** [cyberresilient.streamlit.app](https://cyberresilient.streamlit.app)

---

## Why CyberResilient?

Aspiring cybersecurity professionals often struggle to bridge the gap between theory and practice. CyberResilient gives you a realistic, enterprise-grade toolkit where you can learn hands-on skills the way they're done in the workplace:

- **Build and read executive security dashboards** with real KPIs
- **Run DR/BC simulations** with RTO/RPO analysis and RACI matrices
- **Conduct tabletop exercises** with branching decision trees
- **Manage a risk register** with full CRUD and audit trail
- **Map threats to MITRE ATT&CK** and visualize attack chains
- **Track compliance** against NIST CSF 2.0, ISO 27001, and more
- **Generate professional reports** (PDF and PPTX executive briefs)

---

## Modules

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 1 | **Executive Dashboard** | Security posture scoring, KPI interpretation, trend analysis |
| 2 | **DR/BC Simulator** | RTO/RPO targets, recovery testing, RACI accountability |
| 3 | **Incident Response** | NIST 800-61r2 lifecycle, tabletop exercises, post-mortem writing |
| 4 | **Risk Register** | 5×5 risk matrices, risk ownership, vendor security assessment |
| 5 | **Compliance Tracker** | NIST CSF 2.0, ISO 27001:2022, policy lifecycle management |
| 6 | **Threat Intelligence** | MITRE ATT&CK mapping, coverage heatmaps, attack chain visualization |
| 7 | **Audit Log** | Change tracking, accountability, compliance evidence |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Install & Run

```bash
git clone https://github.com/osayande-infosec/cyberresilient.git
cd CyberResilient
pip install -e ".[dev]"
CyberResilient init --seed     # Initialize DB with sample data
streamlit run app.py        # Opens at http://localhost:8501
```

### Docker

```bash
docker compose up --build -d
# App available at http://localhost:8501
```

---

## Project Structure

```
├── app.py                          # Landing page & auth entry point
├── pages/
│   ├── 1_Dashboard.py              # Executive Security Posture Dashboard
│   ├── 2_DR_Simulator.py           # DR/BC Simulator with history tracking
│   ├── 3_Incident_Response.py      # IR Center, tabletops, post-mortem
│   ├── 4_Risk_Register.py          # Risk Register, CRUD, architecture advisor
│   ├── 5_Compliance.py             # NIST CSF, ISO 27001, policy lifecycle
│   ├── 6_Threat_Intel.py           # MITRE ATT&CK mapper & attack chains
│   └── 7_Audit_Log.py              # Audit trail viewer
├── cyberresilient/                    # Core Python package
│   ├── models/                     # Pydantic & SQLAlchemy models
│   ├── services/                   # Business logic (risk, DR, compliance, auth, reports)
│   ├── config.py                   # YAML-based configuration
│   ├── theme.py                    # UI theming
│   ├── database.py                 # SQLAlchemy engine & session management
│   └── cli.py                      # CLI: init, seed, create-user
├── data/                           # Seed data (JSON)
├── config/                         # Organization profile (YAML)
├── tests/                          # pytest test suite
├── alembic/                        # Database migrations
├── .github/workflows/ci.yml        # GitHub Actions CI pipeline
├── Dockerfile                      # Multi-stage hardened container
└── docker-compose.yml              # Single-command deployment
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit, Plotly, Pandas |
| Backend | Python 3.11+, Pydantic 2, SQLAlchemy 2.0 |
| Database | SQLite (default), any SQL via `DATABASE_URL` |
| Migrations | Alembic |
| Reports | fpdf2 (PDF), python-pptx (PPTX) |
| Auth | Optional RBAC with 4 roles and 12 permissions |
| CI/CD | GitHub Actions (lint, test, security scan, Docker build) |
| Deployment | Docker |

---

## Features

### Learning Mode 🎓
Toggle learning mode to see contextual educational callouts on every page — explaining what each tool does, why it matters, and how it maps to industry frameworks.

### Role-Based Access Control
Enable auth with `CYBERRESILIENT_AUTH=true` to practice RBAC:
- **Admin** — Full access, user management
- **Analyst** — Risk management, simulations, incident response
- **Auditor** — Read-only with audit log access
- **Student** — Dashboard and learning content

### Audit Trail
Every data mutation (create, update, delete) is logged with timestamp, user, and before/after state — just like enterprise GRC platforms.

---

## Configuration

CyberResilient is configurable via `config/org_profile.yaml`:

```yaml
organization:
  name: "Your Organization"
  sector: "Government"
branding:
  app_title: "CyberResilient"
  accent_color: "#D4AF37"
```

Environment variables (see `.env.example`):
- `DATABASE_URL` — SQLAlchemy connection string (default: SQLite)
- `CYBERRESILIENT_AUTH` — Enable authentication (`true`/`false`)

---

## Frameworks & Standards

- NIST Cybersecurity Framework (CSF) v2.0
- NIST SP 800-61r2 (Incident Handling)
- NIST SP 800-53 (Security Controls)
- NIST SP 800-34 (Contingency Planning)
- ISO/IEC 27001:2022 (Annex A)
- MITRE ATT&CK Framework
- CIS Controls v8
- OWASP API Security Top 10
- ISO 31000 (Risk Management)

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v                  # Run tests
ruff check .                      # Lint
ruff format .                     # Format
bandit -r cyberresilient/ -ll        # Security scan
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

Built by [Osayande Agbonkpolor](https://github.com/osayande-infosec)
