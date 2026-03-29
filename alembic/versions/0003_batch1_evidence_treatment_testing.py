"""
Alembic migration — Batch 1: evidence_artifacts, risk_treatments, control_tests

Revision ID: 0003_batch1_evidence_treatment_testing
Revises: 0002_residual_evidence
Create Date: 2026-03-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_batch1_evidence_treatment_testing"
down_revision = "a3b1c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(16), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("original_filename", sa.String(256), nullable=False),
        sa.Column("stored_filename", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, default=""),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by", sa.String(128), nullable=False),
        sa.Column("uploaded_at", sa.String(10), nullable=False),
    )

    op.create_table(
        "risk_treatments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("risk_id", sa.String(16), nullable=False),
        sa.Column("treatment_type", sa.String(16), nullable=False),
        sa.Column("mitigation_plan", sa.Text, default=""),
        sa.Column("target_date", sa.String(10), default=""),
        sa.Column("justification", sa.Text, default=""),
        sa.Column("sign_off_by", sa.String(128), default=""),
        sa.Column("policy_reference", sa.String(256), default=""),
        sa.Column("third_party", sa.String(256), default=""),
        sa.Column("notes", sa.Text, default=""),
        sa.Column("recorded_by", sa.String(128), nullable=False),
        sa.Column("recorded_at", sa.String(10), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, default=True),
    )

    op.create_table(
        "control_tests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("control_id", sa.String(64), nullable=False),
        sa.Column("framework", sa.String(32), nullable=False),
        sa.Column("test_method", sa.String(32), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("result_weight", sa.Float, nullable=False),
        sa.Column("tester", sa.String(128), nullable=False),
        sa.Column("finding", sa.Text, default=""),
        sa.Column("corrective_action_id", sa.String(36), default=""),
        sa.Column("notes", sa.Text, default=""),
        sa.Column("tested_at", sa.String(10), nullable=False),
        sa.Column("retest_due", sa.String(10), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("control_tests")
    op.drop_table("risk_treatments")
    op.drop_table("evidence_artifacts")
