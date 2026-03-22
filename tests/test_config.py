"""Tests for the config loading system."""

from pathlib import Path

from cyberresilient.config import AppConfig, load_config


def test_default_config_loads():
    """Config loads with sensible defaults even without a YAML file."""
    cfg = AppConfig()
    assert cfg.branding.app_title == "CyberResilient"
    assert cfg.organization.name == "Acme Municipal Government"
    assert cfg.security.mttd_target_hours == 2.5


def test_config_from_yaml(tmp_path: Path):
    """Config correctly reads from a YAML file."""
    yaml_content = """
organization:
  name: "Test Corp"
  short_name: "TestCorp"
  type: "Healthcare"
  region: "British Columbia, Canada"
  departments:
    - "IT"
    - "Clinical"

branding:
  app_title: "TestShield"
  accent_color: "#FF0000"

compliance:
  frameworks:
    nist_csf: true
    iso_27001: false

security:
  mttd_target_hours: 1.0
"""
    config_file = tmp_path / "test_profile.yaml"
    config_file.write_text(yaml_content)

    # Clear lru_cache so we load fresh
    load_config.cache_clear()
    cfg = load_config(config_file)

    assert cfg.organization.name == "Test Corp"
    assert cfg.branding.app_title == "TestShield"
    assert cfg.branding.accent_color == "#FF0000"
    assert cfg.compliance.nist_csf is True
    assert cfg.compliance.iso_27001 is False
    assert cfg.security.mttd_target_hours == 1.0

    # Clean up cache
    load_config.cache_clear()
