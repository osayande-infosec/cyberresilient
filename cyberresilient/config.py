"""
CyberResilient Configuration
Loads organization profile from YAML and exposes typed settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class BrandingConfig(BaseModel):
    app_title: str = "CyberResilient"
    app_subtitle: str = "Cybersecurity Resilience Platform"
    app_icon: str = "\U0001f6e1\ufe0f"
    accent_color: str = "#C9A84C"
    card_bg: str = "#1A1A1A"


class OrganizationConfig(BaseModel):
    name: str = "Acme Municipal Government"
    short_name: str = "AcmeMunicipality"
    type: str = "Municipal Government"
    region: str = "Ontario, Canada"
    departments: list[str] = []


class SecurityConfig(BaseModel):
    risk_appetite: str = "Moderate"
    mttd_target_hours: float = 2.5
    mttr_target_hours: float = 8.0
    patch_compliance_target_pct: float = 95
    mfa_coverage_target_pct: float = 100
    dr_readiness_target_pct: float = 90


class CustomFramework(BaseModel):
    name: str
    full_name: str
    enabled: bool = True


class ComplianceConfig(BaseModel):
    nist_csf: bool = True
    iso_27001: bool = True
    custom_frameworks: list[CustomFramework] = []


class AppConfig(BaseModel):
    organization: OrganizationConfig = OrganizationConfig()
    branding: BrandingConfig = BrandingConfig()
    compliance: ComplianceConfig = ComplianceConfig()
    security: SecurityConfig = SecurityConfig()


@lru_cache(maxsize=1)
def load_config(config_path: Path | None = None) -> AppConfig:
    """Load and validate the organization profile from YAML."""
    if config_path is None:
        config_path = CONFIG_DIR / "org_profile.yaml"

    if not config_path.exists():
        return AppConfig()

    with open(config_path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    # Flatten compliance.frameworks into ComplianceConfig
    compliance_raw = raw.get("compliance", {})
    frameworks = compliance_raw.get("frameworks", {})
    compliance_data = {
        "nist_csf": frameworks.get("nist_csf", True),
        "iso_27001": frameworks.get("iso_27001", True),
        "custom_frameworks": frameworks.get("custom_frameworks", []),
    }

    return AppConfig(
        organization=OrganizationConfig(**raw.get("organization", {})),
        branding=BrandingConfig(**raw.get("branding", {})),
        compliance=ComplianceConfig(**compliance_data),
        security=SecurityConfig(**raw.get("security", {})),
    )


def get_config() -> AppConfig:
    """Convenience accessor for the global config."""
    return load_config()
