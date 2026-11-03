from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.api.schemas import EventoOut, VerificacionOut
from arriera.audit import cadena
from arriera.db import get_db
from arriera.models import AuditEvent, User

router = APIRouter(prefix="/audit", tags=["auditoría"])


@router.get("", response_model=list[EventoOut])
def listar(
    limite: int = Query(100, ge=1, le=500),
    antes_de: int | None = Query(None, description="id para paginar hacia atrás"),
    accion: str | None = None,
    u: User = Depends(requiere_roles("admin", "auditor")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    q = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limite)
    if antes_de:
        q = q.where(AuditEvent.id < antes_de)
    if accion:
        q = q.where(AuditEvent.action == accion)
    filas = db.scalars(q).all()
    cadena.registrar(
        db,
        "auditoria.consultada",
        user_id=u.id,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"filtros": {"accion": accion, "antes_de": antes_de}},
    )
    db.commit()
    return [
        EventoOut(
            id=e.id,
            ts=e.ts,
            actor_type=e.actor_type,
            user_id=str(e.user_id) if e.user_id else None,
            action=e.action,
            object_type=e.object_type,
            object_id=e.object_id,
            ip=e.ip,
            details=e.details,
            hash=e.hash,
        )
        for e in filas
    ]


@router.get("/verify-chain", response_model=VerificacionOut)
def verificar(
    u: User = Depends(requiere_roles("admin", "auditor")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    v = cadena.verificar(db)
    cadena.registrar(
        db,
        "auditoria.cadena_verificada",
        user_id=u.id,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"integra": v.integra, "eventos": v.eventos},
    )
    db.commit()
    return VerificacionOut(**v.__dict__)
