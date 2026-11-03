"""Identidad (usuarios, roles, sesiones) y auditoría encadenada de solo inserción.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("key", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("requiere_2fa", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("totp_secret_enc", sa.Text),
        sa.Column("totp_confirmado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Uuid, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("mfa_ok", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip", pg.INET),
        sa.Column("user_agent", sa.String(300)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Uuid, index=True),
        sa.Column("action", sa.String(60), nullable=False, index=True),
        sa.Column("object_type", sa.String(40)),
        sa.Column("object_id", sa.String(80)),
        sa.Column("ip", sa.String(45)),
        sa.Column("user_agent", sa.String(300)),
        sa.Column("details", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False, unique=True),
    )
    op.create_table(
        "audit_anchors",
        sa.Column("fecha", sa.Date, primary_key=True),
        sa.Column("last_event_id", sa.BigInteger, nullable=False),
        sa.Column("last_hash", sa.String(64), nullable=False),
        sa.Column("sent_to", sa.String(254)),
    )
    # Solo inserción: nadie puede modificar ni borrar eventos, ni siquiera el dueño de la tabla.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION arriera_auditoria_inmutable() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'La auditoría es de solo inserción: % no está permitido', TG_OP;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER audit_events_inmutable BEFORE UPDATE OR DELETE ON audit_events
          FOR EACH ROW EXECUTE FUNCTION arriera_auditoria_inmutable();
        CREATE TRIGGER audit_events_sin_truncate BEFORE TRUNCATE ON audit_events
          FOR EACH STATEMENT EXECUTE FUNCTION arriera_auditoria_inmutable();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_sin_truncate ON audit_events")
    op.execute("DROP TRIGGER IF EXISTS audit_events_inmutable ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS arriera_auditoria_inmutable()")
    for t in ("audit_anchors", "audit_events", "sessions", "user_roles", "users", "roles"):
        op.drop_table(t)
