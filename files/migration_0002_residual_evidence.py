"""add residual risk and evidence tracking fields

Revision ID: 0002_residual_evidence
Revises: 0001_initial  (update to match your actual base revision)
Create Date: 2026-03-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_residual_evidence"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # risks table — new columns for residual risk and evidence tracking
    # -----------------------------------------------------------------------
    with op.batch_alter_table("risks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "residual_score",
                sa.Integer(),
                nullable=False,
                # Back-fill: treat existing risk_score as inherent == residual
                server_default=sa.text("risk_score"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "mitigation_effectiveness",
                sa.String(32),
                nullable=False,
                server_default="None",
            )
        )
        batch_op.add_column(
            sa.Column(
                "evidence_date",
                sa.String(10),  # ISO 8601 date string YYYY-MM-DD
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "sign_off_by",
                sa.String(128),
                nullable=False,
                server_default="",
            )
        )

    # -----------------------------------------------------------------------
    # policies table — add review_date if not already present
    # -----------------------------------------------------------------------
    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(
            sa.Column(
                "review_date",
                sa.String(10),
                nullable=True,
            )
        )

    # -----------------------------------------------------------------------
    # nist_csf_categories table (if using a normalised controls table)
    # Add evidence_date per control for staleness tracking.
    # Skip if your controls live only in JSON seed data.
    # -----------------------------------------------------------------------
    # Uncomment if you have a controls table:
    # with op.batch_alter_table("nist_csf_categories") as batch_op:
    #     batch_op.add_column(
    #         sa.Column("evidence_date", sa.String(10), nullable=True)
    #     )


def downgrade() -> None:
    with op.batch_alter_table("risks") as batch_op:
        batch_op.drop_column("sign_off_by")
        batch_op.drop_column("evidence_date")
        batch_op.drop_column("mitigation_effectiveness")
        batch_op.drop_column("residual_score")

    with op.batch_alter_table("policies") as batch_op:
        batch_op.drop_column("review_date")
