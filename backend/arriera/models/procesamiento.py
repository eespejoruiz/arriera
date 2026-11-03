"""Registro de cada paso del flujo de IA: proveedor, modelo, costo y duración (spec 7.1 y 7.10)."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from arriera.db import Base
from arriera.ids import uuid7
from arriera.models import ahora


class PasoProceso(Base):
    __tablename__ = "pipeline_runs"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid7)
    subject_type: Mapped[str] = mapped_column(String(12))  # batch | document | page
    subject_id: Mapped[str] = mapped_column(String(64), index=True)
    step: Mapped[str] = mapped_column(String(30))  # ocr, calidad, separacion...
    status: Mapped[str] = mapped_column(String(12))  # ok | error
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_units: Mapped[int] = mapped_column(Integer, default=1)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)
