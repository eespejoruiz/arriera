from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arriera.db import Base
from arriera.ids import uuid7


def ahora() -> datetime:
    return datetime.now(UTC)


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Uuid, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    requiere_2fa: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    totp_secret_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, onupdate=ahora)
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, lazy="selectin")

    @property
    def role_keys(self) -> list[str]:
        return sorted(r.key for r in self.roles)

    @property
    def requiere_2fa(self) -> bool:
        return any(r.requiere_2fa for r in self.roles)


class Sesion(Base):
    __tablename__ = "sessions"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mfa_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped[User] = relationship(lazy="joined")


class AuditEvent(Base):
    """Auditoría de solo inserción, encadenada: hash = SHA256(prev_hash || evento_canónico)."""

    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_type: Mapped[str] = mapped_column(String(20))  # user | integration | station | system
    user_id: Mapped[object | None] = mapped_column(Uuid, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(60), index=True)
    object_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    object_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), unique=True)


class AuditAnchor(Base):
    __tablename__ = "audit_anchors"
    fecha: Mapped[object] = mapped_column(Date, primary_key=True)
    last_event_id: Mapped[int] = mapped_column(BigInteger)
    last_hash: Mapped[str] = mapped_column(String(64))
    sent_to: Mapped[str | None] = mapped_column(String(254), nullable=True)


from arriera.models.captura import (  # noqa: E402,F401
    ArchivoLote,
    Caja,
    Emparejamiento,
    Estacion,
    Lote,
    Muestreo,
    Pagina,
)
from arriera.models.procesamiento import PasoProceso  # noqa: E402,F401
