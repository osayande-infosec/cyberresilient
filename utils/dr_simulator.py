"""
DR Simulation Engine
Calculates RTO/RPO achievement and generates RACI matrices
for municipal disaster recovery testing.
"""

import json
import random
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_systems():
    with open(DATA_DIR / "systems.json", "r") as f:
        return json.load(f)


def load_scenarios():
    with open(DATA_DIR / "scenarios.json", "r") as f:
        return json.load(f)


def simulate_dr(system: dict, scenario: dict) -> dict:
    """
    Run a DR simulation for a given system under a given scenario.
    Returns estimated recovery metrics and gap analysis.
    """
    rto_target = system["rto_target_hours"]
    rpo_target = system["rpo_target_hours"]

    # Apply scenario multipliers with some variance
    variance = random.uniform(0.85, 1.25)
    rto_estimated = round(rto_target * scenario["rto_impact_multiplier"] * variance, 1)
    rpo_estimated = round(rpo_target * scenario["rpo_impact_multiplier"] * variance, 1)

    rto_met = rto_estimated <= rto_target
    rpo_met = rpo_estimated <= rpo_target

    # Calculate gap
    rto_gap = max(0, round(rto_estimated - rto_target, 1))
    rpo_gap = max(0, round(rpo_estimated - rpo_target, 1))

    # Overall pass/fail
    overall_pass = rto_met and rpo_met

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
        "overall_pass": overall_pass,
        "dr_strategy": system["current_dr_strategy"],
        "recovery_steps": scenario["recovery_steps"],
        "departments_affected": scenario["impact"]["departments_affected"],
        "public_impact": scenario["impact"]["public_impact"],
        "recommendations": _generate_recommendations(system, scenario, rto_met, rpo_met),
    }


def _generate_recommendations(system, scenario, rto_met, rpo_met):
    recs = []
    if not rto_met:
        recs.append(
            f"RTO FAILED: Consider upgrading DR strategy from '{system['current_dr_strategy']}' "
            f"to a higher-availability option (e.g., Hot Standby or Active-Active)."
        )
        recs.append(
            "Conduct root cause analysis on recovery bottlenecks — review automation of failover steps."
        )
    if not rpo_met:
        recs.append(
            "RPO FAILED: Increase backup frequency or implement continuous data replication."
        )
        recs.append(
            "Review backup integrity — ensure point-in-time recovery capability."
        )
    if system["type"] == "OT":
        recs.append(
            "OT System: Ensure manual override procedures are documented and staff are trained."
        )
        recs.append(
            "Validate network segmentation between IT and OT (Purdue Model compliance)."
        )
    if scenario["severity"] == "Critical":
        recs.append(
            "Critical scenario: Ensure executive communication plan and external notification procedures are tested."
        )
    if rto_met and rpo_met:
        recs.append("All targets met — schedule next test per quarterly cadence.")
        recs.append(
            "Document successful test results and update DR plan with any process improvements noted."
        )
    return recs


def generate_raci(system: dict, scenario: dict) -> list[dict]:
    """Generate a RACI matrix for DR activation."""
    dept = system["department"]
    return [
        {"activity": "Declare disaster / activate DR plan", "responsible": "CISO", "accountable": "CAO", "consulted": f"{dept} Director", "informed": "All Department Heads"},
        {"activity": "Isolate affected systems", "responsible": "Security Operations", "accountable": "CISO", "consulted": "Network Team", "informed": f"{dept} Manager"},
        {"activity": "Activate failover / DR environment", "responsible": "Infrastructure Team", "accountable": "IT Director", "consulted": "Application Owner", "informed": "Security Operations"},
        {"activity": "Validate data integrity post-failover", "responsible": "DBA / App Team", "accountable": "Application Owner", "consulted": "Security Operations", "informed": f"{dept} Manager"},
        {"activity": "Communicate status to stakeholders", "responsible": "Communications", "accountable": "CAO", "consulted": "CISO", "informed": "Council / Public"},
        {"activity": "Restore primary systems", "responsible": "Infrastructure Team", "accountable": "IT Director", "consulted": "Vendor Support", "informed": "Security Operations"},
        {"activity": "Conduct post-mortem / lessons learned", "responsible": "Senior Cybersecurity Specialist", "accountable": "CISO", "consulted": "All Participants", "informed": "Director, IT Services"},
        {"activity": "Update DR plan with findings", "responsible": "Senior Cybersecurity Specialist", "accountable": "CISO", "consulted": f"{dept} Manager", "informed": "Audit & Compliance"},
    ]
