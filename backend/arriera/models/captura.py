"""Inventario físico y captura: cajas, muestreos, estaciones (dispositivos), lotes, archivos y páginas."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arriera.db import Base
from arriera.ids import uuid7
from arriera.models import ahora


class Caja(Base):
    __tablename__ = "boxes"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # C-0045
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    shelf_location: Mapped[str | None] = mapped_column(String(40), nullable=True)
    year_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    series_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    paper_condition: Mapped[str] = mapped_column(String(10), default="bueno")  # bueno | regular | malo
    estimated_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="registrada"
    )  # registrada | en_captura | capturada | devuelta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Muestreo(Base):
    __tablename__ = "inventory_samples"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    box_id: Mapped[object] = mapped_column(Uuid, ForeignKey("boxes.id", ondelete="CASCADE"), index=True)
    folders_counted: Mapped[int] = mapped_column(Integer)
    pages_counted: Mapped[int] = mapped_column(Integer)
    sampled_by: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id"))
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Estacion(Base):
    """Dispositivo de captura: agente con escáner USB, celular, multifuncional de red o navegador."""

    __tablename__ = "capture_stations"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(20))  # agente | celular | red | navegador
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    paired_by: Mapped[object | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    device_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Emparejamiento(Base):
    """Código de un solo uso que un celular canjea por una llave de estación, ligado a un lote."""

    __tablename__ = "pairing_codes"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    batch_id: Mapped[object | None] = mapped_column(
        Uuid, ForeignKey("batches.id", ondelete="CASCADE"), nullable=True
    )
    created_by: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    station_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("capture_stations.id"), nullable=True)


class Lote(Base):
    __tablename__ = "batches"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # L-2026-000123
    box_id: Mapped[object] = mapped_column(Uuid, ForeignKey("boxes.id"), index=True)
    station_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("capture_stations.id"), nullable=True)
    operator_id: Mapped[object] = mapped_column(Uuid, ForeignKey("users.id"))
    origen: Mapped[str] = mapped_column(String(20), default="celular")  # agente | celular | red | navegador
    expected_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    received_pages: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="creado")
    # creado | recibiendo | procesando | con_rechazos | procesado | cerrado
    cover_printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    manifest: Mapped[dict] = mapped_column(JSONB, default=dict)
    microformas: Mapped[bool] = mapped_column(Boolean, default=False)  # sigue los pasos de la NTP 392.030-2
    caja: Mapped[Caja] = relationship(lazy="joined")


class ArchivoLote(Base):
    __tablename__ = "batch_files"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    batch_id: Mapped[object] = mapped_column(Uuid, ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(300))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    mime: Mapped[str] = mapped_column(String(60))
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    __table_args__ = (UniqueConstraint("batch_id", "sha256", name="uq_archivo_por_lote"),)


class Pagina(Base):
    __tablename__ = "batch_pages"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    batch_id: Mapped[object] = mapped_column(Uuid, ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    batch_file_id: Mapped[object] = mapped_column(Uuid, ForeignKey("batch_files.id", ondelete="CASCADE"))
    page_index: Mapped[int] = mapped_column(Integer)
    image_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    thumb_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dpi: Mapped[int | None] = mapped_column(Integer, nullable=True)  # resolución efectiva sobre el ancho de un A4
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    blank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    skew_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    blur_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    qc_status: Mapped[str] = mapped_column(
        String(20), default="pendiente"
    )  # pendiente | ok | corregida | reescanear | en_blanco
    qc_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # OCR (Sprint 2): pendiente | ok | sin_texto | omitida | error
    ocr_status: Mapped[str] = mapped_column(String(12), default="pendiente")
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ocr_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ocr_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handwriting_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    __table_args__ = (UniqueConstraint("batch_id", "page_index", name="uq_pagina_por_lote"),)
