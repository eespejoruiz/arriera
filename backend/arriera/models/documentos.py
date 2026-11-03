"""Estructura archivística, personas, documentos, extracciones y tareas de validación (spec 10.2, 10.3, 10.5, 10.6)."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arriera.db import Base
from arriera.ids import uuid7
from arriera.models import ahora


class NodoClasificacion(Base):
    __tablename__ = "classification_nodes"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    parent_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("classification_nodes.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(10))  # fondo | seccion | serie | subserie
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    default_sensitivity: Mapped[str] = mapped_column(String(2), default="N2")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TipoDocumental(Base):
    __tablename__ = "document_types"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    classification_node_id: Mapped[object] = mapped_column(Uuid, ForeignKey("classification_nodes.id"))
    sensitivity: Mapped[str] = mapped_column(String(2), default="N2")  # N1 | N2 | N3
    signals: Mapped[str] = mapped_column(Text, default="")
    fields_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    nodo: Mapped[NodoClasificacion] = relationship(lazy="joined")


class Persona(Base):
    __tablename__ = "persons"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    dni_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    dni_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(6), default="DNI")
    full_name: Mapped[str] = mapped_column(String(200))
    member_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Documento(Base):
    __tablename__ = "documents"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    batch_id: Mapped[object] = mapped_column(Uuid, ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    document_type_id: Mapped[object] = mapped_column(Uuid, ForeignKey("document_types.id"))
    person_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("persons.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sensitivity: Mapped[str] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(14), default="por_validar")  # por_validar | validado | descartado
    type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    tipo: Mapped[TipoDocumental] = relationship(lazy="joined")


class PaginaDocumento(Base):
    __tablename__ = "document_pages"
    document_id: Mapped[object] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    batch_page_id: Mapped[object] = mapped_column(Uuid, ForeignKey("batch_pages.id"), primary_key=True)
    order: Mapped[int] = mapped_column(Integer)
    start_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class Extraccion(Base):
    __tablename__ = "extractions"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    document_id: Mapped[object] = mapped_column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    field_key: Mapped[str] = mapped_column(String(40))
    value_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_norm: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)  # orden dentro del documento (1..n)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)  # motivo local: «DNI no tiene 8 dígitos»…
    source: Mapped[str] = mapped_column(String(6), default="ai")  # ai | human
    status: Mapped[str] = mapped_column(String(14))  # auto_aceptado | pendiente | validado | rechazado | vacio
    validated_by: Mapped[object | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(20))
    __table_args__ = (UniqueConstraint("document_id", "field_key", name="uq_campo_por_documento"),)


class TareaValidacion(Base):
    __tablename__ = "validation_tasks"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    kind: Mapped[str] = mapped_column(String(14))  # campo | clasificacion | separacion
    document_id: Mapped[object] = mapped_column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    extraction_id: Mapped[object | None] = mapped_column(
        Uuid, ForeignKey("extractions.id", ondelete="CASCADE"), nullable=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1 alta (sensible o requerido), 2 normal
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="pendiente")  # pendiente | resuelta
    assignee_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[object | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    resolution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
