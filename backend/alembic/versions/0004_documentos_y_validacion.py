"""Estructura archivística, tipos documentales, personas, documentos, extracciones y tareas de validación.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _ts(nombre: str, nulo: bool = True):
    return sa.Column(nombre, sa.DateTime(timezone=True), nullable=nulo)


def upgrade() -> None:
    op.create_table(
        "classification_nodes",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("parent_id", sa.Uuid, sa.ForeignKey("classification_nodes.id")),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("default_sensitivity", sa.String(2), nullable=False, server_default="N2"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "document_types",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("key", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("classification_node_id", sa.Uuid, sa.ForeignKey("classification_nodes.id"), nullable=False),
        sa.Column("sensitivity", sa.String(2), nullable=False, server_default="N2"),
        sa.Column("signals", sa.Text, nullable=False, server_default=""),
        sa.Column("fields_schema", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "persons",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("dni_hash", sa.String(64), unique=True),
        sa.Column("dni_enc", sa.Text),
        sa.Column("doc_type", sa.String(6), nullable=False, server_default="DNI"),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("member_code", sa.String(40)),
        _ts("created_at", False),
    )
    op.execute("CREATE INDEX ix_persons_nombre_trgm ON persons USING gin (full_name gin_trgm_ops)")
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "batch_id", sa.Uuid, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("document_type_id", sa.Uuid, sa.ForeignKey("document_types.id"), nullable=False),
        sa.Column("person_id", sa.Uuid, sa.ForeignKey("persons.id"), index=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("doc_date", sa.Date),
        sa.Column("sensitivity", sa.String(2), nullable=False),
        sa.Column("status", sa.String(14), nullable=False, server_default="por_validar"),
        sa.Column("type_confidence", sa.Float),
        sa.Column("ai_confidence", sa.Float),
        sa.Column("evidence", pg.JSONB, nullable=False, server_default="[]"),
        _ts("created_at", False),
    )
    op.create_table(
        "document_pages",
        sa.Column("document_id", sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("batch_page_id", sa.Uuid, sa.ForeignKey("batch_pages.id"), primary_key=True),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("start_confidence", sa.Float),
    )
    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "document_id", sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("field_key", sa.String(40), nullable=False),
        sa.Column("value_raw", sa.Text),
        sa.Column("value_norm", sa.Text),
        sa.Column("confidence", sa.Float),
        sa.Column("page_no", sa.Integer),
        sa.Column("evidence", sa.Text),
        sa.Column("bbox", pg.JSONB),
        sa.Column("note", sa.Text),
        sa.Column("source", sa.String(6), nullable=False, server_default="ai"),
        sa.Column("status", sa.String(14), nullable=False),
        sa.Column("validated_by", sa.Uuid, sa.ForeignKey("users.id")),
        _ts("validated_at"),
        sa.Column("prompt_version", sa.String(20), nullable=False),
        sa.UniqueConstraint("document_id", "field_key", name="uq_campo_por_documento"),
    )
    op.create_table(
        "validation_tasks",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("kind", sa.String(14), nullable=False),
        sa.Column(
            "document_id", sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("extraction_id", sa.Uuid, sa.ForeignKey("extractions.id", ondelete="CASCADE")),
        sa.Column("priority", sa.Integer, nullable=False, server_default="2"),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pendiente"),
        sa.Column("assignee_id", sa.Uuid, sa.ForeignKey("users.id")),
        _ts("created_at", False),
        _ts("resolved_at"),
        sa.Column("resolved_by", sa.Uuid, sa.ForeignKey("users.id")),
        sa.Column("resolution", pg.JSONB),
    )
    op.create_index("ix_validation_tasks_created_at", "validation_tasks", ["created_at"])
    op.add_column("pipeline_runs", sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"))
    op.add_column("pipeline_runs", sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"))
    op.add_column("pipeline_runs", sa.Column("prompt_version", sa.String(20)))


def downgrade() -> None:
    for col in ("prompt_version", "tokens_out", "tokens_in"):
        op.drop_column("pipeline_runs", col)
    for t in (
        "validation_tasks",
        "extractions",
        "document_pages",
        "documents",
        "persons",
        "document_types",
        "classification_nodes",
    ):
        op.drop_table(t)
