"""Solicitudes de copia y de acceso: el pedido de una persona (copia de su expediente, de su historia clínica,
de una escritura, una constancia o el acceso a sus datos personales) con plazo, documentos y entrega auditada."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from arriera.db import Base
from arriera.ids import uuid7
from arriera.models import ahora


class Solicitud(Base):
    __tablename__ = "requests"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    number: Mapped[str] = mapped_column(String(20), unique=True)  # S-2026-00001
    kind: Mapped[str] = mapped_column(String(20))  # copia | copia_hc | acceso_datos | constancia
    status: Mapped[str] = mapped_column(String(14), default="recibida")
    # recibida | en_busqueda | lista | entregada | rechazada
    requester_name: Mapped[str] = mapped_column(String(200))
    requester_doc_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    requester_doc_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    requester_contact_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    relation: Mapped[str | None] = mapped_column(String(60), nullable=True)  # titular, apoderado, familiar…
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    redaction: Mapped[str] = mapped_column(String(20), default="ninguno")  # ninguno | sensibles | dni_y_sensibles
    copy_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    copy_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    copy_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_by: Mapped[object | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    delivery_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    history: Mapped[list] = mapped_column(JSONB, default=list)
    created_by: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class ItemSolicitud(Base):
    __tablename__ = "request_items"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    request_id: Mapped[object] = mapped_column(Uuid, ForeignKey("requests.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[object] = mapped_column(Uuid, ForeignKey("documents.id"))
    order: Mapped[int] = mapped_column(Integer, default=0)
    added_by: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    __table_args__ = (UniqueConstraint("request_id", "document_id", name="uq_documento_por_solicitud"),)
