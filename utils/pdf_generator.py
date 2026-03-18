"""
PDF Report Generator
Creates professional PDF reports for DR tests, risk assessments,
and compliance summaries using fpdf2.
"""

from fpdf import FPDF
from datetime import datetime
from pathlib import Path
import os

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _ensure_reports_dir():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class DurhamPDF(FPDF):
    """Custom PDF with DurhamShield branding."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(42, 42, 42)
        self.cell(0, 10, "DurhamShield", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"DurhamShield — Municipal Cybersecurity Resilience Platform | Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(42, 42, 42)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def kv_row(self, key: str, value: str, bold_value: bool = False):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(42, 42, 42)
        self.cell(60, 7, key)
        style = "B" if bold_value else ""
        self.set_font("Helvetica", style, 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    def status_badge(self, text: str, passed: bool):
        if passed:
            self.set_text_color(0, 128, 0)
        else:
            self.set_text_color(200, 0, 0)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(60, 60, 60)


def generate_dr_report(sim_result: dict, raci: list) -> str:
    """Generate a DR simulation test report PDF. Returns file path."""
    _ensure_reports_dir()
    pdf = DurhamPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(42, 42, 42)
    pdf.cell(0, 15, "Disaster Recovery Simulation Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Summary
    pdf.section_title("1. Simulation Summary")
    pdf.kv_row("System:", sim_result["system_name"])
    pdf.kv_row("System ID:", sim_result["system_id"])
    pdf.kv_row("Scenario:", sim_result["scenario_name"])
    pdf.kv_row("Scenario Type:", sim_result["scenario_type"])
    pdf.kv_row("Severity:", sim_result["severity"])
    pdf.kv_row("DR Strategy:", sim_result["dr_strategy"])
    pdf.kv_row("Simulation Date:", sim_result["timestamp"])
    pdf.ln(3)

    # RTO/RPO Results
    pdf.section_title("2. RTO / RPO Analysis")
    rto_status = "PASS" if sim_result["rto_met"] else "FAIL"
    rpo_status = "PASS" if sim_result["rpo_met"] else "FAIL"
    overall = "PASS" if sim_result["overall_pass"] else "FAIL"

    pdf.kv_row("RTO Target:", f"{sim_result['rto_target_hours']} hours")
    pdf.kv_row("RTO Estimated:", f"{sim_result['rto_estimated_hours']} hours")
    pdf.status_badge(f"RTO Result: {rto_status}", sim_result["rto_met"])
    if sim_result["rto_gap_hours"] > 0:
        pdf.kv_row("RTO Gap:", f"{sim_result['rto_gap_hours']} hours")
    pdf.ln(2)

    pdf.kv_row("RPO Target:", f"{sim_result['rpo_target_hours']} hours")
    pdf.kv_row("RPO Estimated:", f"{sim_result['rpo_estimated_hours']} hours")
    pdf.status_badge(f"RPO Result: {rpo_status}", sim_result["rpo_met"])
    if sim_result["rpo_gap_hours"] > 0:
        pdf.kv_row("RPO Gap:", f"{sim_result['rpo_gap_hours']} hours")
    pdf.ln(2)

    pdf.status_badge(f"Overall Result: {overall}", sim_result["overall_pass"])
    pdf.ln(5)

    # Impact
    pdf.section_title("3. Impact Assessment")
    pdf.kv_row("Departments Affected:", ", ".join(sim_result["departments_affected"]))
    pdf.body_text(f"Public Impact: {sim_result['public_impact']}")
    pdf.ln(3)

    # Recovery Steps
    pdf.section_title("4. Recovery Steps")
    for i, step in enumerate(sim_result["recovery_steps"], 1):
        pdf.body_text(f"{i}. {step}")

    # Recommendations
    pdf.add_page()
    pdf.section_title("5. Recommendations")
    for rec in sim_result["recommendations"]:
        pdf.body_text(f"• {rec}")

    # RACI Matrix
    pdf.section_title("6. RACI Matrix — DR Activation")
    pdf.set_font("Helvetica", "B", 8)
    col_widths = [45, 30, 25, 45, 40]
    headers = ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for row in raci:
        vals = [row["activity"], row["responsible"], row["accountable"], row["consulted"], row["informed"]]
        max_h = 7
        for w, v in zip(col_widths, vals):
            pdf.cell(w, max_h, v[:30], border=1)
        pdf.ln()

    # Save
    filename = f"DR_Report_{sim_result['system_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = REPORTS_DIR / filename
    pdf.output(str(filepath))
    return str(filepath)


def generate_risk_report(assessment: dict, vendor_name: str) -> str:
    """Generate an Architecture Risk Assessment PDF. Returns file path."""
    _ensure_reports_dir()
    pdf = DurhamPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Architecture Security Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.section_title("1. Assessment Summary")
    pdf.kv_row("Vendor / Solution:", vendor_name)
    pdf.kv_row("Date:", datetime.now().strftime("%Y-%m-%d"))
    pdf.kv_row("Total Checks:", str(assessment["total_checks"]))
    pdf.kv_row("Passed:", str(assessment["passed"]))
    pdf.kv_row("Failed:", str(assessment["failed"]))
    pdf.kv_row("Score:", f"{assessment['score_pct']}%")
    pdf.status_badge(f"Overall Risk: {assessment['overall_risk']}", assessment["score_pct"] >= 70)
    pdf.ln(5)

    pdf.section_title("2. Detailed Findings")
    for r in assessment["results"]:
        status_str = "PASS" if r["passed"] else "FAIL"
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(0, 128, 0) if r["passed"] else pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 7, f"[{status_str}] {r['control']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(60, 60, 60)
        pdf.set_font("Helvetica", "", 9)
        pdf.body_text(f"   Framework: {r['framework']}")
        if not r["passed"]:
            pdf.body_text(f"   Risk: {r['risk_if_missing']}")
            pdf.body_text(f"   Recommendation: {r['recommendation']}")
        pdf.ln(1)

    filename = f"ArchRisk_{vendor_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = REPORTS_DIR / filename
    pdf.output(str(filepath))
    return str(filepath)
