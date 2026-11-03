"""OCR por página, índice de texto completo (español y simple, sin tildes) y registro de pasos.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Configuraciones de búsqueda: español con raíces y "simple" para nombres y otros idiomas, ambas sin tildes.
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'es_unaccent') THEN
            CREATE TEXT SEARCH CONFIGURATION es_unaccent (COPY = pg_catalog.spanish);
            ALTER TEXT SEARCH CONFIGURATION es_unaccent
              ALTER MAPPING FOR hword, hword_part, word WITH unaccent, spanish_stem;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'simple_unaccent') THEN
            CREATE TEXT SEARCH CONFIGURATION simple_unaccent (COPY = pg_catalog.simple);
            ALTER TEXT SEARCH CONFIGURATION simple_unaccent
              ALTER MAPPING FOR hword, hword_part, word WITH unaccent, simple;
          END IF;
        END $$;
        """
    )
    op.add_column(
        "batch_pages", sa.Column("ocr_status", sa.String(12), nullable=False, server_default="pendiente")
    )
    op.add_column("batch_pages", sa.Column("ocr_text", sa.Text))
    op.add_column("batch_pages", sa.Column("ocr_conf", sa.Float))
    op.add_column("batch_pages", sa.Column("ocr_lang", sa.String(8)))
    op.add_column("batch_pages", sa.Column("ocr_key", sa.String(300)))
    op.add_column("batch_pages", sa.Column("ocr_at", sa.DateTime(timezone=True)))
    op.add_column("batch_pages", sa.Column("handwriting_ratio", sa.Float))
    op.add_column("batch_pages", sa.Column("tsv", pg.TSVECTOR))
    op.create_index("ix_batch_pages_tsv", "batch_pages", ["tsv"], postgresql_using="gin")

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("subject_type", sa.String(12), nullable=False),
        sa.Column("subject_id", sa.String(64), nullable=False, index=True),
        sa.Column("step", sa.String(30), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("provider", sa.String(40)),
        sa.Column("model", sa.String(80)),
        sa.Column("input_units", sa.Integer, nullable=False, server_default="1"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("pipeline_runs")
    op.drop_index("ix_batch_pages_tsv", table_name="batch_pages")
    for col in ("tsv", "handwriting_ratio", "ocr_at", "ocr_key", "ocr_lang", "ocr_conf", "ocr_text", "ocr_status"):
        op.drop_column("batch_pages", col)
    op.execute(
        "DROP TEXT SEARCH CONFIGURATION IF EXISTS simple_unaccent; DROP TEXT SEARCH CONFIGURATION IF EXISTS es_unaccent;"
    )
