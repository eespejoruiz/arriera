"""Modo microformas: lotes marcados, pasos con responsable y rol, actas con huella, resolución por página.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("batches", sa.Column("microformas", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("batch_pages", sa.Column("dpi", sa.Integer))
    op.create_table(
        "batch_steps",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "batch_id", sa.Uuid, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("step", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("batch_id", "step", name="uq_paso_por_lote"),
    )
    op.create_table(
        "acts",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("number", sa.String(40), nullable=False, unique=True),
        sa.Column("batch_id", sa.Uuid, sa.ForeignKey("batches.id"), index=True),
        sa.Column("pdf_key", sa.String(300), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("payload", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.Uuid, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("acts")
    op.drop_table("batch_steps")
    op.drop_column("batch_pages", "dpi")
    op.drop_column("batches", "microformas")
