"""
Learning Mode Service — Rich educational content rendering.
Provides contextual explanations, case studies, guided exercises,
GRC engineering insights, and jargon tooltips for learning mode.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

from cyberresilient.services.auth_service import is_learning_mode

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@st.cache_data
def _load_content() -> dict:
    """Load learning content from JSON knowledge base."""
    path = DATA_DIR / "learning_content.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def get_content(section: str) -> dict:
    """Get learning content for a specific section (e.g., 'dashboard', 'compliance')."""
    data = _load_content()
    return data.get(section, {})


def get_glossary() -> dict[str, str]:
    """Get the full glossary of cybersecurity terms."""
    data = _load_content()
    return data.get("glossary", {})


# ─── Rich UI Components ────────────────────────────────────


def learning_section(title: str, content: str, icon: str = "💡") -> None:
    """Render a learning callout with rich formatting. Only shown in learning mode."""
    if not is_learning_mode():
        return
    st.info(f"{icon} **{title}**\n\n{content}")


def case_study_panel(cases: list[dict]) -> None:
    """Render case studies as expandable panels with lessons learned."""
    if not is_learning_mode():
        return
    for case in cases:
        with st.expander(f"📖 Case Study: {case['name']}", expanded=False):
            if "summary" in case:
                st.markdown(case["summary"])
            if "ir_timeline" in case:
                st.markdown(f"**IR Timeline:** {case['ir_timeline']}")
            if "rto_context" in case:
                st.markdown(f"**DR Context:** {case['rto_context']}")
            if "how_it_scores" in case:
                st.markdown(f"**Risk Scoring:** {case['how_it_scores']}")
            if "mitigation" in case:
                st.markdown(f"**Mitigation:** {case['mitigation']}")
            if "lesson" in case:
                st.success(f"**Key Lesson:** {case['lesson']}")


def try_this_panel(exercises: list[str]) -> None:
    """Render guided exercise prompts."""
    if not is_learning_mode():
        return
    with st.expander("🎯 Try This — Guided Exercises", expanded=False):
        for i, exercise in enumerate(exercises, 1):
            st.markdown(f"**Exercise {i}:** {exercise}")
            st.markdown("")


def grc_insight(title: str, content: str) -> None:
    """Render a GRC engineering insight panel with distinct styling."""
    if not is_learning_mode():
        return
    st.markdown(
        f"""<div style="border-left: 4px solid #C9A84C; padding: 12px 16px;
        background: rgba(201, 168, 76, 0.08); border-radius: 0 8px 8px 0;
        margin: 12px 0;">
        <strong>🏛️ GRC Engineering: {title}</strong><br><br>
        {content}
        </div>""",
        unsafe_allow_html=True,
    )


def evidence_mapping_table(mappings: list[dict]) -> None:
    """Render a table mapping metrics to compliance frameworks."""
    if not is_learning_mode():
        return
    with st.expander("📋 Evidence-to-Framework Mapping", expanded=False):
        header = "| Metric | NIST CSF | ISO 27001 | Evidence Type |\n|---|---|---|---|\n"
        rows = "\n".join(
            f"| {m['metric']} | {m['nist_csf']} | {m['iso27001']} | {m['evidence_type']} |"
            for m in mappings
        )
        st.markdown(header + rows)


def kpi_explanation(kpi_data: dict) -> None:
    """Render a deep-dive explanation for a KPI metric."""
    if not is_learning_mode():
        return
    with st.expander(f"📊 Deep Dive: {kpi_data['label']}", expanded=False):
        st.markdown(kpi_data["explanation"])
        st.markdown(f"**Industry Benchmark:** {kpi_data['benchmark']}")
        st.markdown(f"**Real-World Example:** {kpi_data['real_world']}")


def compliance_comparison_table(comparisons: list[dict]) -> None:
    """Render a Traditional vs. Engineering GRC comparison."""
    if not is_learning_mode():
        return
    with st.expander("⚖️ Traditional GRC vs. Compliance Engineering", expanded=False):
        header = "| Traditional GRC | Engineering-Driven GRC |\n|---|---|\n"
        rows = "\n".join(
            f"| ❌ {c['traditional']} | ✅ {c['engineering']} |"
            for c in comparisons
        )
        st.markdown(header + rows)


def evidence_types_panel(evidence_types: list[dict]) -> None:
    """Render evidence type explanations with examples and frequency."""
    if not is_learning_mode():
        return
    with st.expander("🗂️ Evidence Collection Guide", expanded=False):
        for et in evidence_types:
            st.markdown(f"**{et['type']}** — {et['description']}")
            st.markdown(f"- *Example in this tool:* {et['example']}")
            st.markdown(f"- *Collection frequency:* {et['frequency']}")
            st.markdown("")


def compliance_pipeline_panel(stages: list[dict]) -> None:
    """Render the compliance tracking pipeline stages."""
    if not is_learning_mode():
        return
    with st.expander("🔄 Compliance Tracking Pipeline", expanded=False):
        for stage in stages:
            st.markdown(f"### {stage['stage']}")
            st.markdown(stage["description"])
            st.caption(f"🔧 In CyberResilient: {stage['tool_mapping']}")
            st.markdown("")


def auditor_questions_panel(questions: list[dict]) -> None:
    """Render common auditor questions with evidence guidance."""
    if not is_learning_mode():
        return
    with st.expander("🔍 What Auditors Actually Ask (and How to Answer)", expanded=False):
        for q in questions:
            st.markdown(f"**Q:** *\"{q['question']}\"*")
            st.markdown(f"**Evidence:** {q['evidence']}")
            st.markdown("")


def nist_function_detail(func_name: str, func_data: dict) -> None:
    """Render detailed NIST CSF function explanation."""
    if not is_learning_mode():
        return
    with st.expander(f"📘 Learn More: {func_name}", expanded=False):
        st.markdown(f"**Purpose:** {func_data['purpose']}")
        st.markdown(f"**Real-World Context:** {func_data['real_world']}")
        st.markdown(f"**Key Categories:** {func_data['key_categories']}")
        st.success(f"**GRC Tip:** {func_data['grc_tip']}")


def audit_logging_principles(principles: list[dict]) -> None:
    """Render audit logging best practices."""
    if not is_learning_mode():
        return
    with st.expander("📚 Audit Logging Principles", expanded=False):
        for p in principles:
            st.markdown(f"**{p['name']}:** {p['definition']}")
            st.caption(f"Standard: {p['standard']}")
            st.markdown("")


def glossary_tooltip(term: str) -> str:
    """Return the glossary definition for a term, or empty string if not found."""
    glossary = get_glossary()
    return glossary.get(term, "")
