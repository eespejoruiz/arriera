"""Auditoría encadenada: cada evento guarda SHA256(prev_hash || evento_canónico).

La tabla es de solo inserción (un trigger en la base impide UPDATE y DELETE).
Si alguien alterara un evento directamente en disco, `verificar` lo detecta.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from arriera.models import AuditAnchor, AuditEvent

GENESIS = "0" * 64
_LOCK = 774201  # candado de transacción para serializar la cadena


def _canonico(ev: dict) -> str:
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _evento(e: AuditEvent) -> dict:
    return {
        "ts": e.ts.astimezone(UTC).isoformat(timespec="microseconds"),
        "actor_type": e.actor_type,
        "user_id": str(e.user_id) if e.user_id else None,
        "action": e.action,
        "object_type": e.object_type,
        "object_id": e.object_id,
        "ip": e.ip,
        "details": e.details or {},
    }


def calcular_hash(prev: str, e: AuditEvent) -> str:
    return hashlib.sha256((prev + _canonico(_evento(e))).encode()).hexdigest()


def registrar(
    db: Session,
    action: str,
    *,
    actor_type: str = "user",
    user_id=None,
    object_type: str | None = None,
    object_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> AuditEvent:
    """Agrega un evento a la cadena dentro de la transacción actual (no hace commit)."""
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LOCK})
    prev = db.scalar(select(AuditEvent.hash).order_by(AuditEvent.id.desc()).limit(1)) or GENESIS
    ev = AuditEvent(
        ts=datetime.now(UTC),
        actor_type=actor_type,
        user_id=user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        ip=ip,
        user_agent=(user_agent or "")[:300] or None,
        details=details or {},
        prev_hash=prev,
    )
    ev.hash = calcular_hash(prev, ev)
    db.add(ev)
    db.flush()
    return ev


@dataclass
class Verificacion:
    integra: bool
    eventos: int
    ultimo_hash: str
    primer_error_id: int | None = None
    motivo: str | None = None


def verificar(db: Session, lote: int = 5000) -> Verificacion:
    prev, n, ultimo_id = GENESIS, 0, 0
    while True:
        filas = db.scalars(
            select(AuditEvent).where(AuditEvent.id > ultimo_id).order_by(AuditEvent.id).limit(lote)
        ).all()
        if not filas:
            return Verificacion(True, n, prev)
        for e in filas:
            if e.prev_hash != prev:
                return Verificacion(False, n, prev, e.id, "El enlace con el evento anterior no coincide.")
            if calcular_hash(prev, e) != e.hash:
                return Verificacion(False, n, prev, e.id, "El contenido del evento fue alterado.")
            prev, n, ultimo_id = e.hash, n + 1, e.id


def anclar(db: Session, fecha: date, enviado_a: str | None = None) -> AuditAnchor | None:
    """Guarda el último hash del día como ancla (se envía aparte al administrador)."""
    ultimo = db.scalar(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1))
    if ultimo is None:
        return None
    ancla = db.get(AuditAnchor, fecha) or AuditAnchor(fecha=fecha, last_event_id=0, last_hash=GENESIS)
    ancla.last_event_id, ancla.last_hash, ancla.sent_to = ultimo.id, ultimo.hash, enviado_a
    db.merge(ancla)
    return ancla
