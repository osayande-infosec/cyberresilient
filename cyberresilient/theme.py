"""
Theme constants and CSS generation for the Streamlit UI.
"""

from __future__ import annotations

from cyberresilient.config import get_config


def get_theme_colors() -> dict[str, str]:
    """Return the active color palette from config."""
    cfg = get_config()
    return {
        "accent": cfg.branding.accent_color,
        "card_bg": cfg.branding.card_bg,
        "pass": "#4CAF50",
        "fail": "#F44336",
        "warn": "#FFC107",
        "text": "#EAEAEA",
        "muted": "#888",
        "border": "#2A2A2A",
    }


def get_custom_css() -> str:
    """Generate the global CSS using theme colors."""
    c = get_theme_colors()
    return f"""
<style>
    .stMetric .metric-container {{ border-left: 3px solid {c["accent"]}; padding-left: 12px; }}
    div[data-testid="stSidebar"] {{ border-right: 1px solid {c["border"]}; }}
    h1, h2, h3 {{ color: {c["text"]} !important; }}
    .gold {{ color: {c["accent"]}; }}
    .status-pass {{ color: {c["pass"]}; font-weight: 700; }}
    .status-fail {{ color: {c["fail"]}; font-weight: 700; }}
    .status-partial {{ color: {c["warn"]}; font-weight: 700; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.8rem; }}
    .sidebar-brand {{ text-align: center; padding: 1rem 0 0.5rem 0; }}
    .sidebar-brand h1 {{ font-size: 1.6rem; margin: 0; color: {c["accent"]} !important; }}
    .sidebar-brand p {{ font-size: 0.8rem; color: {c["muted"]}; margin: 0; }}
</style>
"""


def render_sidebar_brand() -> str:
    """Return the sidebar branding HTML."""
    cfg = get_config()
    return f"""
    <div class="sidebar-brand">
        <h1>{cfg.branding.app_icon} {cfg.branding.app_title}</h1>
        <p>{cfg.organization.name}<br/>{cfg.branding.app_subtitle}</p>
    </div>
    <hr style="border-color: #2A2A2A; margin: 0.5rem 0;">
    """
