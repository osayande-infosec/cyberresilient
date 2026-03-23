"""add_residual_evidence_columns

Revision ID: a3b1c4d5e6f7
Revises: 92af1072f7ec
Create Date: 2026-03-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b1c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '92af1072f7ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add residual-risk, mitigation-effectiveness, evidence, and sign-off columns."""

    # ── risks table ─────────────────────────────────────────
    with op.batch_alter_table("risks") as batch_op:
        batch_op.add_column(
            sa.Column("residual_score", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("mitigation_effectiveness", sa.String(20),
                       server_default="None", nullable=False)
        )
        batch_op.add_column(
            sa.Column("evidence_date", sa.String(20),
                       server_default="", nullable=False)
        )
        batch_op.add_column(
            sa.Column("sign_off_by", sa.String(100),
                       server_default="", nullable=False)
        )

    # Back-fill residual_score = risk_score for existing rows.
    op.execute("UPDATE risks SET residual_score = risk_score WHERE residual_score IS NULL")

    # ── policies table ──────────────────────────────────────
    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(
            sa.Column("review_alert_sent", sa.Integer(),
                       server_default="0", nullable=False)
        )


def downgrade() -> None:
    """Remove the new columns."""
    with op.batch_alter_table("policies") as batch_op:
        batch_op.drop_column("review_alert_sent")

    with op.batch_alter_table("risks") as batch_op:
        batch_op.drop_column("sign_off_by")
        batch_op.drop_column("evidence_date")
        batch_op.drop_column("mitigation_effectiveness")
        batch_op.drop_column("residual_score")
