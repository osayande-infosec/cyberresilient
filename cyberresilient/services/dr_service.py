"""
DR Simulation Engine
Calculates RTO/RPO achievement and generates RACI matrices.
"""

from __future__ import annotations

import json
import random
from datetime import datetime

from cyberresilient.config import DATA_DIR


def _db_available(table: str) -> bool:
    try:
        from sqlalchemy import inspect

        from cyberresilient.database import get_engine

        return inspect(get_engine()).has_table(table)
    except Exception:
        return False


def load_systems() -> list[dict]:
    if _db_available("systems"):
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import SystemRow

        session = get_session()
        try:
            rows = session.query(SystemRow).all()
            if rows:
                return [r.to_dict() for r in rows]
        finally:
            session.close()
    with open(DATA_DIR / "systems.json", encoding="utf-8") as f:
        return json.load(f)


def load_scenarios() -> list[dict]:
    if _db_available("scenarios"):
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import ScenarioRow

        session = get_session()
        try:
            rows = session.query(ScenarioRow).all()
            if rows:
                return [r.to_dict() for r in rows]
        finally:
            session.close()
    with open(DATA_DIR / "scenarios.json", encoding="utf-8") as f:
        return json.load(f)


def simulate_dr(system: dict, scenario: dict) -> dict:
    """Run a DR simulation for a given system under a given scenario."""
    rto_target = system["rto_target_hours"]
    rpo_target = system["rpo_target_hours"]

    variance = random.uniform(0.85, 1.25)  # nosec B311
    rto_estimated = round(rto_target * scenario["rto_impact_multiplier"] * variance, 1)
    rpo_estimated = round(rpo_target * scenario["rpo_impact_multiplier"] * variance, 1)

    rto_met = rto_estimated <= rto_target
    rpo_met = rpo_estimated <= rpo_target

    rto_gap = max(0, round(rto_estimated - rto_target, 1))
    rpo_gap = max(0, round(rpo_estimated - rpo_target, 1))

    return {
        "system_name": system["name"],
        "system_id": system["id"],
        "scenario_name": scenario["name"],
        "scenario_type": scenario["type"],
        "severity": scenario["severity"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rto_target_hours": rto_target,
        "rto_estimated_hours": rto_estimated,
        "rto_met": rto_met,
        "rto_gap_hours": rto_gap,
        "rpo_target_hours": rpo_target,
        "rpo_estimated_hours": rpo_estimated,
        "rpo_met": rpo_met,
        "rpo_gap_hours": rpo_gap,
        "overall_pass": rto_met and rpo_met,
        "dr_strategy": system["current_dr_strategy"],
        "recovery_steps": scenario["recovery_steps"],
        "departments_affected": scenario["impact"]["departments_affected"],
        "public_impact": scenario["impact"]["public_impact"],
        "recommendations": _generate_recommendations(system, scenario, rto_met, rpo_met),
    }


def _generate_recommendations(system: dict, scenario: dict, rto_met: bool, rpo_met: bool) -> list[str]:
    recs = []
    if not rto_met:
        recs.append(
            f"RTO FAILED: Consider upgrading DR strategy from '{system['current_dr_strategy']}' "
            f"to a higher-availability option (e.g., Hot Standby or Active-Active)."
        )
        recs.append("Conduct root cause analysis on recovery bottlenecks — review automation of failover steps.")
    if not rpo_met:
        recs.append("RPO FAILED: Increase backup frequency or implement continuous data replication.")
        recs.append("Review backup integrity — ensure point-in-time recovery capability.")
    if system["type"] == "OT":
        recs.append("OT System: Ensure manual override procedures are documented and staff are trained.")
        recs.append("Validate network segmentation between IT and OT (Purdue Model compliance).")
    if scenario["severity"] == "Critical":
        recs.append(
            "Critical scenario: Ensure executive communication plan and external notification procedures are tested."
        )
    if rto_met and rpo_met:
        recs.append("All targets met — schedule next test per quarterly cadence.")
        recs.append("Document successful test results and update DR plan with any process improvements noted.")
    return recs


def generate_raci(system: dict, scenario: dict) -> list[dict]:
    """Generate a RACI matrix for DR activation."""
    dept = system["department"]
    return [
        {
            "activity": "Declare disaster / activate DR plan",
            "responsible": "CISO",
            "accountable": "CAO",
            "consulted": f"{dept} Director",
            "informed": "All Department Heads",
        },
        {
            "activity": "Isolate affected systems",
            "responsible": "Security Operations",
            "accountable": "CISO",
            "consulted": "Network Team",
            "informed": f"{dept} Manager",
        },
        {
            "activity": "Activate failover / DR environment",
            "responsible": "Infrastructure Team",
            "accountable": "IT Director",
            "consulted": "Application Owner",
            "informed": "Security Operations",
        },
        {
            "activity": "Validate data integrity post-failover",
            "responsible": "DBA / App Team",
            "accountable": "Application Owner",
            "consulted": "Security Operations",
            "informed": f"{dept} Manager",
        },
        {
            "activity": "Communicate status to stakeholders",
            "responsible": "Communications",
            "accountable": "CAO",
            "consulted": "CISO",
            "informed": "Council / Public",
        },
        {
            "activity": "Restore primary systems",
            "responsible": "Infrastructure Team",
            "accountable": "IT Director",
            "consulted": "Vendor Support",
            "informed": "Security Operations",
        },
        {
            "activity": "Conduct post-mortem / lessons learned",
            "responsible": "Security Lead",
            "accountable": "CISO",
            "consulted": "All Participants",
            "informed": "IT Director",
        },
        {
            "activity": "Update DR plan with findings",
            "responsible": "Security Lead",
            "accountable": "CISO",
            "consulted": f"{dept} Manager",
            "informed": "Audit & Compliance",
        },
    ]


def save_simulation(result: dict, user: str = "system") -> None:
    """Persist a DR simulation result to the database."""
    if not _db_available("simulation_history"):
        return
    import json as _json

    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import SimulationHistoryRow

    session = get_session()
    try:
        row = SimulationHistoryRow(
            user=user,
            system_id=result["system_id"],
            system_name=result["system_name"],
            scenario_name=result["scenario_name"],
            severity=result["severity"],
            rto_target=result["rto_target_hours"],
            rto_estimated=result["rto_estimated_hours"],
            rto_met=int(result["rto_met"]),
            rpo_target=result["rpo_target_hours"],
            rpo_estimated=result["rpo_estimated_hours"],
            rpo_met=int(result["rpo_met"]),
            overall_pass=int(result["overall_pass"]),
            dr_strategy=result.get("dr_strategy", ""),
            result_json=_json.dumps(result, default=str),
        )
        session.add(row)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def load_simulation_history(limit: int = 50) -> list[dict]:
    """Load recent simulation results from the database."""
    if not _db_available("simulation_history"):
        return []
    from cyberresilient.database import get_session
    from cyberresilient.models.db_models import SimulationHistoryRow

    session = get_session()
    try:
        rows = session.query(SimulationHistoryRow).order_by(SimulationHistoryRow.timestamp.desc()).limit(limit).all()
        return [r.to_dict() for r in rows]
    finally:
        session.close()
