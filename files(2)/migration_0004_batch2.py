"""
Alembic migration — Batch 2: risk_reviews, corrective_action_plans,
vendors, vendor_assessments + last_reviewed_at on risks

Revision ID: 0004_batch2_reviews_caps_vendors
Revises: 0003_batch1_evidence_treatment_testing
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_batch2_reviews_caps_vendors"
down_revision = "0003_batch1_evidence_treatment_testing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_reviewed_at to existing risks table
    with op.batch_alter_table("risks") as batch_op:
        batch_op.add_column(
            sa.Column("last_reviewed_at", sa.String(10), nullable=True)
        )

    op.create_table(
        "risk_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("risk_id", sa.String(16), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text, default=""),
        sa.Column("residual_score_at_review", sa.Integer, default=0),
        sa.Column("reviewed_at", sa.String(10), nullable=False),
    )

    op.create_table(
        "corrective_action_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, default=""),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, default="Open"),
        sa.Column("target_date", sa.String(10), nullable=False),
        sa.Column("linked_control_id", sa.String(64), default=""),
        sa.Column("linked_risk_id", sa.String(16), default=""),
        sa.Column("linked_test_id", sa.String(36), default=""),
        sa.Column("resolution_notes", sa.Text, default=""),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.String(10), nullable=False),
        sa.Column("closed_at", sa.String(10), default=""),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("criticality", sa.String(16), nullable=False),
        sa.Column("data_classification", sa.String(64), nullable=False),
        sa.Column("contact_name", sa.String(128), default=""),
        sa.Column("contact_email", sa.String(256), default=""),
        sa.Column("contract_reference", sa.String(256), default=""),
        sa.Column("contract_expiry", sa.String(10), default=""),
        sa.Column("notes", sa.Text, default=""),
        sa.Column("current_risk_tier", sa.String(32), default="Not Assessed"),
        sa.Column("last_assessment_score", sa.Integer, nullable=True),
        sa.Column("last_assessed_at", sa.String(10), default=""),
        sa.Column("reassessment_due", sa.String(10), nullable=False),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.String(10), nullable=False),
    )

    op.create_table(
        "vendor_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vendor_id", sa.String(36), nullable=False),
        sa.Column("score_pct", sa.Integer, nullable=False),
        sa.Column("risk_tier", sa.String(32), nullable=False),
        sa.Column("passed", sa.Integer, default=0),
        sa.Column("failed", sa.Integer, default=0),
        sa.Column("assessed_by", sa.String(128), nullable=False),
        sa.Column("assessed_at", sa.String(10), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("vendor_assessments")
    op.drop_table("vendors")
    op.drop_table("corrective_action_plans")
    op.drop_table("risk_reviews")
    with op.batch_alter_table("risks") as batch_op:
        batch_op.drop_column("last_reviewed_at")
