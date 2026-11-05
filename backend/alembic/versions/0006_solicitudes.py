"""Solicitudes de copia y de acceso a datos, con plazo, documentos y copia entregada con huella.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "requests",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("number", sa.String(20), nullable=False, unique=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(14), nullable=False, server_default="recibida"),
        sa.Column("requester_name", sa.String(200), nullable=False),
        sa.Column("requester_doc_hash", sa.String(64), index=True),
        sa.Column("requester_doc_enc", sa.Text),
        sa.Column("requester_contact_enc", sa.Text),
        sa.Column("relation", sa.String(60)),
        sa.Column("detail", sa.Text),
        sa.Column("received_on", sa.Date, nullable=False),
        sa.Column("due_on", sa.Date, nullable=False),
        sa.Column("redaction", sa.String(20), nullable=False, server_default="ninguno"),
        sa.Column("copy_key", sa.String(300)),
        sa.Column("copy_sha256", sa.String(64)),
        sa.Column("copy_pages", sa.Integer),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_by", sa.Uuid, sa.ForeignKey("users.id")),
        sa.Column("delivery_note", sa.Text),
        sa.Column("history", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_by", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "request_items",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "request_id", sa.Uuid, sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("document_id", sa.Uuid, sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("added_by", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("request_id", "document_id", name="uq_documento_por_solicitud"),
    )


def downgrade() -> None:
    op.drop_table("request_items")
    op.drop_table("requests")
