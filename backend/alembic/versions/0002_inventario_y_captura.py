"""Inventario físico y captura: cajas, muestreos, estaciones, emparejamientos, lotes, archivos y páginas.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _ts(nombre: str, nulo: bool = True):
    return sa.Column(nombre, sa.DateTime(timezone=True), nullable=nulo)


def upgrade() -> None:
    op.create_table(
        "boxes",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("label", sa.String(160)),
        sa.Column("shelf_location", sa.String(40)),
        sa.Column("year_from", sa.Integer),
        sa.Column("year_to", sa.Integer),
        sa.Column("series_hint", sa.String(120)),
        sa.Column("paper_condition", sa.String(10), nullable=False, server_default="bueno"),
        sa.Column("estimated_pages", sa.Integer),
        sa.Column("status", sa.String(20), nullable=False, server_default="registrada"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "inventory_samples",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("box_id", sa.Uuid, sa.ForeignKey("boxes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("folders_counted", sa.Integer, nullable=False),
        sa.Column("pages_counted", sa.Integer, nullable=False),
        sa.Column("sampled_by", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sampled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "capture_stations",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("location", sa.String(120)),
        sa.Column("api_key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("paired_by", sa.Uuid, sa.ForeignKey("users.id")),
        sa.Column("device_info", pg.JSONB, nullable=False, server_default="{}"),
        _ts("last_heartbeat_at"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "batches",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("box_id", sa.Uuid, sa.ForeignKey("boxes.id"), nullable=False, index=True),
        sa.Column("station_id", sa.Uuid, sa.ForeignKey("capture_stations.id")),
        sa.Column("operator_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("origen", sa.String(20), nullable=False, server_default="celular"),
        sa.Column("expected_pages", sa.Integer),
        sa.Column("received_pages", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="creado"),
        _ts("cover_printed_at"),
        _ts("received_at"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("manifest", pg.JSONB, nullable=False, server_default="{}"),
    )
    op.execute("CREATE SEQUENCE batch_code_seq START 1")
    op.create_table(
        "pairing_codes",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("batch_id", sa.Uuid, sa.ForeignKey("batches.id", ondelete="CASCADE")),
        sa.Column("created_by", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        _ts("expires_at", nulo=False),
        _ts("used_at"),
        sa.Column("station_id", sa.Uuid, sa.ForeignKey("capture_stations.id")),
    )
    op.create_table(
        "batch_files",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "batch_id", sa.Uuid, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("storage_key", sa.String(300), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("mime", sa.String(60), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "sha256", name="uq_archivo_por_lote"),
    )
    op.create_table(
        "batch_pages",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "batch_id", sa.Uuid, sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("batch_file_id", sa.Uuid, sa.ForeignKey("batch_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_index", sa.Integer, nullable=False),
        sa.Column("image_key", sa.String(300)),
        sa.Column("thumb_key", sa.String(300)),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("is_cover", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("blank_score", sa.Float),
        sa.Column("skew_deg", sa.Float),
        sa.Column("blur_score", sa.Float),
        sa.Column("qc_status", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("qc_reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "page_index", name="uq_pagina_por_lote"),
    )


def downgrade() -> None:
    for t in (
        "batch_pages",
        "batch_files",
        "pairing_codes",
        "batches",
        "capture_stations",
        "inventory_samples",
        "boxes",
    ):
        op.drop_table(t)
    op.execute("DROP SEQUENCE IF EXISTS batch_code_seq")
