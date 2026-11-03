"""Documentos detectados por la IA y cola de validación (Sprint 3).

Ver documentos y validar: administración, archivo y validación. Los valores sensibles (diagnóstico, CIE-10) y el
DNI se devuelven completos solo a quien valida; la búsqueda por sensibilidad para el rol de consulta llega en el
Sprint 4.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.audit.cadena import registrar
from arriera.config import settings
from arriera.db import SessionLocal, get_db
from arriera.models import (
    Documento,
    Extraccion,
    Lote,
    Pagina,
    PaginaDocumento,
    Persona,
    TareaValidacion,
    TipoDocumental,
    User,
)
from arriera.procesamiento.documentos import gasto_mes, procesar_lote_ia, vincular_persona
from arriera.procesamiento.normalizar import normalizar_valor

router = APIRouter(tags=["documentos"])
VEN = ("admin", "archivero", "validador")
PROCESAN = ("admin", "archivero")


def ia_en_segundo_plano(lote_id) -> None:
    with SessionLocal() as db:
        procesar_lote_ia(db, lote_id)


def _doc(db: Session, did: str) -> Documento:
    try:
        d = db.get(Documento, did)
    except Exception:
        d = None
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese documento.")
    return d


def _campos(db: Session, d: Documento) -> list[dict]:
    defs = {c["key"]: c for c in d.tipo.fields_schema.get("fields", [])}
    exs = {e.field_key: e for e in db.scalars(select(Extraccion).where(Extraccion.document_id == d.id)).all()}
    salida = []
    for key, c in defs.items():
        e = exs.get(key)
        salida.append(
            {
                "key": key,
                "nombre": c["nombre"],
                "tipo": c["type"],
                "opciones": c.get("options"),
                "requerido": c["required"],
                "sensible": bool(c.get("sensitive")),
                "id": str(e.id) if e else None,
                "valor": e.value_norm if e else None,
                "original": e.value_raw if e else None,
                "confianza": e.confidence if e else None,
                "estado": e.status if e else "vacio",
                "nota": e.note if e else None,
                "pagina": e.page_no if e else None,
                "caja": e.bbox if e else None,
                "evidencia": e.evidence if e else None,
                "fuente": e.source if e else None,
            }
        )
    return salida


def _resumen_doc(db: Session, d: Documento) -> dict:
    lote = db.get(Lote, d.batch_id)
    pags = db.execute(
        select(Pagina.id, Pagina.page_index, PaginaDocumento.order)
        .join(PaginaDocumento, PaginaDocumento.batch_page_id == Pagina.id)
        .where(PaginaDocumento.document_id == d.id)
        .order_by(PaginaDocumento.order)
    ).all()
    pendientes = db.scalar(
        select(func.count()).where(TareaValidacion.document_id == d.id, TareaValidacion.status == "pendiente")
    )
    return {
        "id": str(d.id),
        "titulo": d.title,
        "tipo": d.tipo.key,
        "tipo_nombre": d.tipo.name,
        "serie": d.tipo.nodo.name,
        "sensibilidad": d.sensitivity,
        "estado": d.status,
        "fecha": d.doc_date.isoformat() if d.doc_date else None,
        "confianza_tipo": d.type_confidence,
        "confianza": d.ai_confidence,
        "lote": lote.code if lote else None,
        "caja": lote.caja.code if lote else None,
        "paginas": [{"id": str(pid), "indice": idx, "orden": o} for pid, idx, o in pags],
        "pendientes": pendientes,
        "persona": bool(d.person_id),
    }


@router.get("/documentos")
def listar(
    lote: str | None = None,
    estado: str | None = None,
    _: User = Depends(requiere_roles(*VEN)),
    db: Session = Depends(get_db),
):
    q = select(Documento).order_by(Documento.created_at.desc()).limit(200)
    if lote:
        q = q.join(Lote, Lote.id == Documento.batch_id).where(Lote.code == lote)
    if estado:
        q = q.where(Documento.status == estado)
    return [_resumen_doc(db, d) for d in db.scalars(q).all()]


@router.get("/documentos/{did}")
def detalle(
    did: str,
    u: User = Depends(requiere_roles(*VEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    d = _doc(db, did)
    registrar(
        db,
        "documento.visto",
        user_id=u.id,
        object_type="document",
        object_id=str(d.id),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"sensibilidad": d.sensitivity},
    )
    db.commit()
    tareas = db.scalars(
        select(TareaValidacion)
        .where(TareaValidacion.document_id == d.id, TareaValidacion.status == "pendiente")
        .order_by(TareaValidacion.priority, TareaValidacion.created_at)
    ).all()
    tipos = db.scalars(select(TipoDocumental).where(TipoDocumental.is_active.is_(True))).all()
    return {
        **_resumen_doc(db, d),
        "evidencia_tipo": d.evidence,
        "campos": _campos(db, d),
        "tareas": [_tarea(t) for t in tareas],
        "tipos": [{"key": t.key, "nombre": t.name} for t in tipos],
    }


def _tarea(t: TareaValidacion) -> dict:
    return {
        "id": str(t.id),
        "tipo": t.kind,
        "documento": str(t.document_id),
        "campo": str(t.extraction_id) if t.extraction_id else None,
        "prioridad": t.priority,
        "motivo": t.reason,
        "creada": t.created_at,
    }


@router.get("/validacion/cola")
def cola(_: User = Depends(requiere_roles(*VEN)), db: Session = Depends(get_db)):
    """Documentos con tareas pendientes, primero los de mayor prioridad y los más antiguos."""
    filas = db.execute(
        select(
            TareaValidacion.document_id,
            func.min(TareaValidacion.priority),
            func.count(),
            func.min(TareaValidacion.created_at),
        )
        .where(TareaValidacion.status == "pendiente")
        .group_by(TareaValidacion.document_id)
        .order_by(func.min(TareaValidacion.priority), func.min(TareaValidacion.created_at))
        .limit(100)
    ).all()
    total_docs = db.scalar(select(func.count()).select_from(Documento))
    auto = db.scalar(select(func.count()).where(Documento.status == "validado"))
    return {
        "documentos": [{**_resumen_doc(db, db.get(Documento, did)), "prioridad": pr} for did, pr, _n, _c in filas],
        "tareas": db.scalar(select(func.count()).where(TareaValidacion.status == "pendiente")),
        "total_documentos": total_docs,
        "validados": auto,
    }


class Resolucion(BaseModel):
    accion: str = Field(pattern="^(aceptar|corregir|vaciar|tipo|separacion_ok)$")
    valor: str | None = Field(None, max_length=2000)
    tipo: str | None = Field(None, max_length=40)


@router.post("/validacion/tareas/{tid}")
def resolver(
    tid: str,
    datos: Resolucion,
    tareas_bg: BackgroundTasks,
    u: User = Depends(requiere_roles(*VEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    try:
        t = db.get(TareaValidacion, tid)
    except Exception:
        t = None
    if t is None or t.status != "pendiente":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La tarea no existe o ya fue resuelta.")
    d = db.get(Documento, t.document_id)
    assert d is not None
    ahora = datetime.now(UTC)
    detalle: dict = {"tarea": t.kind, "accion": datos.accion}
    if t.kind == "campo":
        e = db.get(Extraccion, t.extraction_id)
        assert e is not None
        c = next(c for c in d.tipo.fields_schema["fields"] if c["key"] == e.field_key)
        detalle["campo"] = e.field_key
        if datos.accion == "aceptar":
            if e.value_norm is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No hay un valor que aceptar.")
            e.status = "validado"
        elif datos.accion == "corregir":
            norm, nota = normalizar_valor(c["type"], datos.valor, c.get("options"))
            if norm is None or nota:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, nota or "Escribe un valor.")
            detalle["cambio"] = norm != e.value_norm
            e.value_norm, e.source, e.status, e.note = norm, "human", "validado", None
        elif datos.accion == "vaciar":
            e.value_norm, e.source, e.status = None, "human", "rechazado"
        else:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Acción no válida para un campo.")
        e.validated_by, e.validated_at = u.id, ahora
        if c["type"] == "dni" and e.status == "validado" and e.value_norm:
            nombre = next(
                (
                    x.value_norm
                    for x in db.scalars(select(Extraccion).where(Extraccion.document_id == d.id)).all()
                    for cc in d.tipo.fields_schema["fields"]
                    if cc["key"] == x.field_key and cc["type"] == "person_name" and x.value_norm
                ),
                None,
            )
            d.person_id = vincular_persona(db, e.value_norm, nombre).id
    elif t.kind == "clasificacion":
        if datos.accion == "tipo":
            nuevo = db.scalar(select(TipoDocumental).where(TipoDocumental.key == datos.tipo))
            if nuevo is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ese tipo no existe.")
            detalle["de"], detalle["a"] = d.tipo.key, nuevo.key
            if nuevo.id != d.document_type_id:
                # Cambia el tipo: se vuelve a extraer con el esquema nuevo.
                d.document_type_id, d.sensitivity, d.type_confidence = nuevo.id, nuevo.sensitivity, 1.0
                lote_id = d.batch_id
                t.status, t.resolved_at, t.resolved_by = "resuelta", ahora, u.id
                t.resolution = detalle
                registrar(
                    db,
                    "validacion.tipo_cambiado",
                    user_id=u.id,
                    object_type="document",
                    object_id=str(d.id),
                    ip=ctx.ip,
                    details=detalle,
                )
                db.commit()
                tareas_bg.add_task(reextraer_en_segundo_plano, d.id, lote_id)
                return {"documento": str(d.id), "estado": "reextrayendo"}
        elif datos.accion != "aceptar":
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Acción no válida para la clasificación.")
        d.type_confidence = 1.0
    elif t.kind == "separacion":
        if datos.accion not in ("aceptar", "separacion_ok"):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Cortar o unir páginas llega con la vista de miniaturas."
            )
    t.status, t.resolved_at, t.resolved_by, t.resolution = "resuelta", ahora, u.id, detalle
    db.flush()
    quedan = db.scalar(
        select(func.count()).where(TareaValidacion.document_id == d.id, TareaValidacion.status == "pendiente")
    )
    if not quedan:
        d.status = "validado"
    registrar(
        db,
        "validacion.resuelta",
        user_id=u.id,
        object_type="document",
        object_id=str(d.id),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details=detalle,
    )
    db.commit()
    return {"documento": str(d.id), "estado": d.status, "pendientes": quedan}


def reextraer_en_segundo_plano(did, lote_id) -> None:
    from arriera.procesamiento.documentos import reextraer

    with SessionLocal() as db:
        reextraer(db, did)


@router.post("/procesamiento/lotes/{code}/ia")
def procesar_ia(
    code: str,
    tareas_bg: BackgroundTasks,
    u: User = Depends(requiere_roles(*PROCESAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = db.scalar(select(Lote).where(Lote.code == code))
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese lote.")
    registrar(db, "lote.ia_solicitada", user_id=u.id, object_type="batch", object_id=code, ip=ctx.ip)
    db.commit()
    tareas_bg.add_task(ia_en_segundo_plano, lote.id)
    return {"lote": code, "estado": "en_cola"}


@router.get("/procesamiento/presupuesto")
def presupuesto(_: User = Depends(requiere_roles(*PROCESAN)), db: Session = Depends(get_db)):
    g, tope = gasto_mes(db), settings().ia_presupuesto_usd_mes
    return {
        "proveedor": settings().llm_proveedor,
        "modelo": settings().llm_modelo,
        "gasto_mes_usd": round(g, 4),
        "presupuesto_usd": tope,
        "porcentaje": round(g / tope * 100, 1) if tope else None,
        "alerta": g >= tope * 0.8,
        "pausado": g >= tope,
        "personas": db.scalar(select(func.count()).select_from(Persona)),
    }
