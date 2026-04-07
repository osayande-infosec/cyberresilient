"""
cyberresilient/services/notification_service.py

Notification & Reminder Service.

Generates a digest of all pending alerts across the platform:
  - Evidence expiry (risks + controls)
  - Risk review overdue
  - Policy expiry proximity (≤ 30 days)
  - CAP overdue
  - Vendor reassessment overdue

Can be called from:
  1. Streamlit sidebar (passive, on page load)
  2. GitHub Actions scheduled workflow (active email/Slack push)
  3. CLI: `cyberresilient notify --send`

Email and Slack sending requires env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, NOTIFY_TO
  SLACK_WEBHOOK_URL
"""

from __future__ import annotations

import json
import os
import smtplib
import urllib.request
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ---------------------------------------------------------------------------
# Digest builder
# ---------------------------------------------------------------------------


def build_digest() -> dict:
    """
    Collect all pending alerts across the platform.
    Returns a structured digest — call this from any context.
    """
    alerts: list[dict] = []

    # 1. Risk evidence expiry
    try:
        from cyberresilient.services.risk_service import (
            days_until_evidence_expires,
            is_evidence_expired,
            load_risks,
        )

        for r in load_risks():
            ev = r.get("evidence_date")
            if is_evidence_expired(ev):
                alerts.append(
                    {
                        "type": "risk_evidence_expired",
                        "severity": "high",
                        "entity": r["id"],
                        "title": r["title"],
                        "message": f"Evidence expired or missing for risk {r['id']}: {r['title']}",
                        "due": ev or "never collected",
                    }
                )
            else:
                days = days_until_evidence_expires(ev)
                if days is not None and days <= 30:
                    alerts.append(
                        {
                            "type": "risk_evidence_expiring",
                            "severity": "medium",
                            "entity": r["id"],
                            "title": r["title"],
                            "message": f"Risk {r['id']} evidence expires in {days} days",
                            "due": ev,
                        }
                    )
    except Exception:
        pass

    # 2. Risk review overdue
    try:
        from cyberresilient.services.review_service import (
            days_until_review,
            is_review_overdue,
        )
        from cyberresilient.services.risk_service import load_risks

        for r in load_risks():
            if is_review_overdue(r):
                overdue_days = abs(days_until_review(r))
                alerts.append(
                    {
                        "type": "risk_review_overdue",
                        "severity": "high" if overdue_days > 30 else "medium",
                        "entity": r["id"],
                        "title": r["title"],
                        "message": f"Risk {r['id']} review overdue by {overdue_days} days",
                        "due": r.get("last_reviewed_at", "never reviewed"),
                    }
                )
    except Exception:
        pass

    # 3. Policy expiry
    try:
        from cyberresilient.services.compliance_service import (
            get_policy_summary,
            load_policies,
        )

        summary = get_policy_summary(load_policies())
        for p in summary.get("expiring_soon", []):
            days = p["days_remaining"]
            alerts.append(
                {
                    "type": "policy_expiring",
                    "severity": "high" if days <= 7 else "medium",
                    "entity": p.get("id", ""),
                    "title": p["title"],
                    "message": f"Policy '{p['title']}' review due in {days} days",
                    "due": p["review_date"],
                }
            )
    except Exception:
        pass

    # 4. CAP overdue
    try:
        from cyberresilient.services.cap_service import load_caps

        today = date.today().isoformat()
        for cap in load_caps():
            if cap["status"] not in ("Closed",) and cap["target_date"] < today:
                overdue_days = (date.today() - date.fromisoformat(cap["target_date"])).days
                alerts.append(
                    {
                        "type": "cap_overdue",
                        "severity": "high" if cap["priority"] in ("Critical", "High") else "medium",
                        "entity": cap["id"],
                        "title": cap["title"],
                        "message": f"CAP '{cap['title']}' overdue by {overdue_days} days",
                        "due": cap["target_date"],
                    }
                )
    except Exception:
        pass

    # 5. Vendor reassessment overdue
    try:
        from cyberresilient.services.vendor_service import get_overdue_vendors

        for v in get_overdue_vendors():
            alerts.append(
                {
                    "type": "vendor_reassessment_overdue",
                    "severity": "high" if v["criticality"] in ("Critical", "High") else "medium",
                    "entity": v["id"],
                    "title": v["name"],
                    "message": f"Vendor '{v['name']}' reassessment overdue (due {v['reassessment_due']})",
                    "due": v["reassessment_due"],
                }
            )
    except Exception:
        pass

    high = [a for a in alerts if a["severity"] == "high"]
    medium = [a for a in alerts if a["severity"] == "medium"]

    return {
        "generated_at": date.today().isoformat(),
        "total_alerts": len(alerts),
        "high_severity": len(high),
        "medium_severity": len(medium),
        "alerts": sorted(alerts, key=lambda x: (x["severity"] != "high", x["due"])),
    }


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _format_email_body(digest: dict) -> str:
    lines = [
        f"CyberResilient GRC Alert Digest — {digest['generated_at']}",
        f"Total alerts: {digest['total_alerts']} ({digest['high_severity']} high, {digest['medium_severity']} medium)",
        "",
    ]
    for a in digest["alerts"]:
        sev = "🔴" if a["severity"] == "high" else "🟡"
        lines.append(f"{sev} [{a['type'].upper()}] {a['message']} (due: {a['due']})")
    return "\n".join(lines)


def _format_slack_blocks(digest: dict) -> list[dict]:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🛡️ CyberResilient Alerts — {digest['generated_at']}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{digest['total_alerts']} alerts* — "
                    f":red_circle: {digest['high_severity']} high  "
                    f":yellow_circle: {digest['medium_severity']} medium"
                ),
            },
        },
        {"type": "divider"},
    ]
    for a in digest["alerts"][:20]:  # Slack has block limits
        emoji = ":red_circle:" if a["severity"] == "high" else ":large_yellow_circle:"
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{a['title']}*\n{a['message']} — due `{a['due']}`",
                },
            }
        )
    return blocks


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------


def send_email_digest(digest: dict, to_address: str | None = None) -> bool:
    """
    Send digest via SMTP. Reads config from environment variables.
    Returns True on success.
    """
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    to = to_address or os.getenv("NOTIFY_TO", "")

    if not all([host, user, password, to]):
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"CyberResilient GRC Alerts — {digest['high_severity']} High, {digest['medium_severity']} Medium"
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(_format_email_body(digest), "plain"))

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to], msg.as_string())
        return True
    except Exception:
        return False


def send_slack_digest(digest: dict, webhook_url: str | None = None) -> bool:
    """
    Post digest to Slack via incoming webhook.
    Returns True on success.
    """
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
    if not url or not digest["total_alerts"]:
        return False

    if not url.startswith(("https://",)):
        return False

    payload = json.dumps({"blocks": _format_slack_blocks(digest)}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 — controlled webhook URL
            return resp.status == 200
    except Exception:
        return False


def notify_all(digest: dict | None = None) -> dict:
    """
    Build digest and attempt all configured delivery channels.
    Returns delivery status per channel.
    """
    if digest is None:
        digest = build_digest()

    if not digest["total_alerts"]:
        return {"email": False, "slack": False, "reason": "No alerts to send"}

    return {
        "email": send_email_digest(digest),
        "slack": send_slack_digest(digest),
        "total_alerts": digest["total_alerts"],
    }
