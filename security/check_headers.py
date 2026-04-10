"""
Security Headers Checker
Validates HTTP security headers on a running CyberResilient instance.
Run: python security/check_headers.py [url]
"""

from __future__ import annotations

import ssl
import sys
import urllib.request

REQUIRED_HEADERS = {
    "X-Content-Type-Options": {
        "expected": "nosniff",
        "severity": "HIGH",
        "description": "Prevents MIME-type sniffing attacks",
        "cwe": "CWE-16",
    },
    "X-Frame-Options": {
        "expected": ["DENY", "SAMEORIGIN"],
        "severity": "HIGH",
        "description": "Prevents clickjacking attacks",
        "cwe": "CWE-1021",
    },
    "X-XSS-Protection": {
        "expected": "0",  # Modern best practice: rely on CSP, disable legacy filter
        "severity": "MEDIUM",
        "description": "Legacy XSS filter control (should be 0 with CSP)",
        "cwe": "CWE-79",
    },
    "Referrer-Policy": {
        "expected": [
            "no-referrer",
            "strict-origin-when-cross-origin",
            "strict-origin",
            "same-origin",
            "no-referrer-when-downgrade",
        ],
        "severity": "MEDIUM",
        "description": "Controls referrer information leakage",
        "cwe": "CWE-200",
    },
    "Permissions-Policy": {
        "expected": None,  # Just check presence
        "severity": "MEDIUM",
        "description": "Restricts browser feature access (camera, mic, geolocation)",
        "cwe": "CWE-16",
    },
    "Strict-Transport-Security": {
        "expected": None,  # Just check presence; only meaningful over HTTPS
        "severity": "HIGH",
        "description": "Enforces HTTPS connections (HSTS)",
        "cwe": "CWE-319",
    },
    "Content-Security-Policy": {
        "expected": None,  # Check presence + validate directives
        "severity": "HIGH",
        "description": "Prevents XSS, injection, and data exfiltration",
        "cwe": "CWE-79",
    },
}

RECOMMENDED_CSP_DIRECTIVES = [
    "default-src",
    "script-src",
    "style-src",
    "img-src",
    "frame-ancestors",
]


def check_headers(url: str) -> dict:
    """Check security headers on the given URL. Returns results dict."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": "cyberresilient-SecurityScanner/1.0"})
    try:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:  # nosec B310
            headers = {k.lower(): v for k, v in resp.headers.items()}
    except Exception as e:
        return {"error": str(e), "pass": False, "results": []}

    results = []
    passed = 0
    failed = 0

    for header_name, config in REQUIRED_HEADERS.items():
        header_key = header_name.lower()
        value = headers.get(header_key)

        result = {
            "header": header_name,
            "severity": config["severity"],
            "description": config["description"],
            "cwe": config.get("cwe", ""),
            "value": value,
        }

        if value is None:
            result["status"] = "MISSING"
            result["message"] = f"{header_name} header not set"
            failed += 1
        elif config["expected"] is None:
            # Just need to be present
            result["status"] = "PASS"
            result["message"] = f"Present: {value}"
            passed += 1
        elif isinstance(config["expected"], list):
            if value in config["expected"]:
                result["status"] = "PASS"
                result["message"] = f"Correct: {value}"
                passed += 1
            else:
                result["status"] = "FAIL"
                result["message"] = f"Got '{value}', expected one of {config['expected']}"
                failed += 1
        else:
            if value == config["expected"]:
                result["status"] = "PASS"
                result["message"] = f"Correct: {value}"
                passed += 1
            else:
                result["status"] = "FAIL"
                result["message"] = f"Got '{value}', expected '{config['expected']}'"
                failed += 1

        results.append(result)

    # CSP directive analysis
    csp_value = headers.get("content-security-policy", "")
    csp_analysis = []
    if csp_value:
        directives = {d.strip().split()[0]: d.strip() for d in csp_value.split(";") if d.strip()}
        for rec in RECOMMENDED_CSP_DIRECTIVES:
            if rec in directives:
                csp_analysis.append({"directive": rec, "status": "PRESENT", "value": directives[rec]})
            else:
                csp_analysis.append({"directive": rec, "status": "MISSING", "value": ""})
    else:
        csp_analysis = [{"directive": d, "status": "MISSING", "value": ""} for d in RECOMMENDED_CSP_DIRECTIVES]

    # Additional dangerous headers that should NOT be present
    dangerous = []
    if headers.get("server"):
        dangerous.append({"header": "Server", "value": headers["server"], "message": "Server version disclosure"})
    if headers.get("x-powered-by"):
        dangerous.append(
            {"header": "X-Powered-By", "value": headers["x-powered-by"], "message": "Technology disclosure"}
        )

    return {
        "url": url,
        "pass": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": len(REQUIRED_HEADERS),
        "results": results,
        "csp_analysis": csp_analysis,
        "dangerous_headers": dangerous,
    }


def print_report(report: dict) -> int:
    """Print a formatted security headers report. Returns exit code (0=pass, 1=fail)."""
    if "error" in report:
        print(f"\n❌ ERROR: Could not connect to {report.get('url', 'unknown')}")
        print(f"   {report['error']}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  Security Headers Report — {report['url']}")
    print(f"{'=' * 60}")
    print(f"  Result: {'✅ PASS' if report['pass'] else '❌ FAIL'}")
    print(f"  Passed: {report['passed']}/{report['total']}")
    print(f"{'=' * 60}\n")

    for r in report["results"]:
        icon = {"PASS": "✅", "FAIL": "❌", "MISSING": "⚠️"}.get(r["status"], "❓")
        print(f"  {icon} [{r['severity']}] {r['header']}")
        print(f"     {r['message']}")
        print(f"     {r['description']} ({r['cwe']})")
        print()

    if report.get("csp_analysis"):
        print(f"\n{'─' * 60}")
        print("  Content-Security-Policy Directives")
        print(f"{'─' * 60}")
        for d in report["csp_analysis"]:
            icon = "✅" if d["status"] == "PRESENT" else "⚠️"
            print(f"  {icon} {d['directive']}: {d['value'] or 'NOT SET'}")

    if report.get("dangerous_headers"):
        print(f"\n{'─' * 60}")
        print("  ⚠️  Information Disclosure Headers (should be removed)")
        print(f"{'─' * 60}")
        for d in report["dangerous_headers"]:
            print(f"  ❌ {d['header']}: {d['value']} — {d['message']}")

    print()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
    report = check_headers(target)
    exit_code = print_report(report)
    sys.exit(exit_code)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
    report = check_headers(target)
    print_report(report)
    sys.exit(0 if report.get("pass") else 1)
