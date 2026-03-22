"""
CyberResilient CLI — management commands.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cyberresilient.config import DATA_DIR


def seed(args: argparse.Namespace) -> None:
    """Seed the database from JSON data files."""
    from cyberresilient.database import get_session, init_db
    from cyberresilient.models.db_models import (
        KPIMetricRow,
        MonthlyIncidentRow,
        PolicyRow,
        RiskRow,
        ScenarioRow,
        SystemRow,
    )
    from cyberresilient.services.audit_service import log_action

    init_db()
    session = get_session()

    try:
        _seed_risks(session, args.force)
        _seed_systems(session, args.force)
        _seed_scenarios(session, args.force)
        _seed_policies(session, args.force)
        _seed_kpi(session, args.force)

        log_action(session, action="SEED", entity_type="database", details="Seeded from JSON data files")
        session.commit()
        print("Database seeded successfully.")  # noqa: T201
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed_risks(session, force: bool) -> None:
    from cyberresilient.models.db_models import RiskRow

    if not force and session.query(RiskRow).first():
        print("  Risks table already has data — skipping (use --force to overwrite)")  # noqa: T201
        return

    if force:
        session.query(RiskRow).delete()

    data = _load_json("risks.json")
    for r in data:
        session.add(RiskRow(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            likelihood=r["likelihood"],
            impact=r["impact"],
            risk_score=r["risk_score"],
            owner=r["owner"],
            status=r["status"],
            mitigation=r["mitigation"],
            asset=r["asset"],
            target_date=r["target_date"],
            notes=r.get("notes", ""),
        ))
    print(f"  Seeded {len(data)} risks")  # noqa: T201


def _seed_systems(session, force: bool) -> None:
    from cyberresilient.models.db_models import SystemRow

    if not force and session.query(SystemRow).first():
        print("  Systems table already has data — skipping (use --force to overwrite)")  # noqa: T201
        return

    if force:
        session.query(SystemRow).delete()

    data = _load_json("systems.json")
    for s in data:
        session.add(SystemRow(
            id=s["id"],
            name=s["name"],
            department=s["department"],
            type=s["type"],
            hosting=s.get("hosting", ""),
            tier=s["tier"],
            rto_target_hours=s["rto_target_hours"],
            rpo_target_hours=s["rpo_target_hours"],
            current_dr_strategy=s["current_dr_strategy"],
            last_tested=s.get("last_tested", ""),
            test_result=s.get("test_result", ""),
            dependencies=json.dumps(s.get("dependencies", [])),
            description=s.get("description", ""),
        ))
    print(f"  Seeded {len(data)} systems")  # noqa: T201


def _seed_scenarios(session, force: bool) -> None:
    from cyberresilient.models.db_models import ScenarioRow

    if not force and session.query(ScenarioRow).first():
        print("  Scenarios table already has data — skipping (use --force to overwrite)")  # noqa: T201
        return

    if force:
        session.query(ScenarioRow).delete()

    data = _load_json("scenarios.json")
    for s in data:
        session.add(ScenarioRow(
            id=s["id"],
            name=s["name"],
            type=s["type"],
            severity=s["severity"],
            description=s["description"],
            affected_systems=json.dumps(s.get("affected_systems", [])),
            impact_json=json.dumps(s.get("impact", {})),
            recovery_steps=json.dumps(s.get("recovery_steps", [])),
            rto_impact_multiplier=s["rto_impact_multiplier"],
            rpo_impact_multiplier=s["rpo_impact_multiplier"],
        ))
    print(f"  Seeded {len(data)} scenarios")  # noqa: T201


def _seed_policies(session, force: bool) -> None:
    from cyberresilient.models.db_models import PolicyRow

    if not force and session.query(PolicyRow).first():
        print("  Policies table already has data — skipping (use --force to overwrite)")  # noqa: T201
        return

    if force:
        session.query(PolicyRow).delete()

    data = _load_json("policies.json")
    for p in data:
        session.add(PolicyRow(
            id=p["id"],
            name=p["name"],
            owner=p["owner"],
            version=p["version"],
            status=p["status"],
            last_reviewed=p.get("last_reviewed") or "",
            next_review=p.get("next_review") or "",
            approved_by=p.get("approved_by") or "",
            description=p.get("description") or "",
        ))
    print(f"  Seeded {len(data)} policies")  # noqa: T201


def _seed_kpi(session, force: bool) -> None:
    from cyberresilient.models.db_models import KPIMetricRow, MonthlyIncidentRow

    if not force and session.query(KPIMetricRow).first():
        print("  KPI tables already have data — skipping (use --force to overwrite)")  # noqa: T201
        return

    if force:
        session.query(KPIMetricRow).delete()
        session.query(MonthlyIncidentRow).delete()

    data = _load_json("kpi_data.json")

    for m in data.get("kpi_metrics", []):
        session.add(KPIMetricRow(
            label=m["label"],
            value=m["value"],
            unit=m.get("unit", ""),
            trend=m.get("trend", ""),
            lower_is_better=1 if m.get("lower_is_better") else 0,
        ))

    for mi in data.get("monthly_incidents", []):
        session.add(MonthlyIncidentRow(
            month=mi["month"],
            count=mi["count"],
            critical=mi.get("critical", 0),
        ))

    kpi_count = len(data.get("kpi_metrics", []))
    incident_count = len(data.get("monthly_incidents", []))
    print(f"  Seeded {kpi_count} KPI metrics, {incident_count} monthly incidents")  # noqa: T201


def create_user(args: argparse.Namespace) -> None:
    """Create a new user account."""
    import bcrypt

    from cyberresilient.database import get_session, init_db
    from cyberresilient.models.db_models import UserRow
    from cyberresilient.services.audit_service import log_action

    init_db()
    session = get_session()

    try:
        existing = session.query(UserRow).filter_by(username=args.username).first()
        if existing:
            print(f"User '{args.username}' already exists.")  # noqa: T201
            sys.exit(1)

        password_hash = bcrypt.hashpw(args.password.encode(), bcrypt.gensalt()).decode()
        user = UserRow(
            username=args.username,
            name=args.name,
            email=args.email or "",
            password_hash=password_hash,
            role=args.role,
        )
        session.add(user)
        log_action(
            session,
            action="CREATE",
            entity_type="user",
            entity_id=args.username,
            details=f"Created user with role '{args.role}'",
        )
        session.commit()
        print(f"User '{args.username}' created with role '{args.role}'.")  # noqa: T201
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_command(args: argparse.Namespace) -> None:
    """Initialize database and optionally seed."""
    from cyberresilient.database import init_db

    init_db()
    print("Database initialized.")  # noqa: T201

    if args.seed:
        args.force = False
        seed(args)


def _load_json(filename: str) -> list | dict:
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(prog="CyberResilient", description="CyberResilient CLI")
    sub = parser.add_subparsers(dest="command")

    # init
    init_parser = sub.add_parser("init", help="Initialize database tables")
    init_parser.add_argument("--seed", action="store_true", help="Also seed data")

    # seed
    seed_parser = sub.add_parser("seed", help="Seed database from JSON data files")
    seed_parser.add_argument("--force", action="store_true", help="Overwrite existing data")

    # create-user
    user_parser = sub.add_parser("create-user", help="Create a user account")
    user_parser.add_argument("username")
    user_parser.add_argument("--name", required=True)
    user_parser.add_argument("--password", required=True)
    user_parser.add_argument("--email", default="")
    user_parser.add_argument("--role", choices=["admin", "analyst", "auditor", "student"], default="student")

    args = parser.parse_args()

    if args.command == "init":
        init_command(args)
    elif args.command == "seed":
        seed(args)
    elif args.command == "create-user":
        create_user(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
