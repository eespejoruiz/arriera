"""Solicitudes de copia y de acceso a datos (pedidos de personas sobre su propio expediente o historia).

Las atienden administración y archivo. El DNI del solicitante se guarda cifrado y con una huella para cruzarlo
con las personas del archivo; la copia lleva leyenda, huella SHA-256 y queda en la cadena de auditoría.
"""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera import solicitudes as srv
from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.api.documentos import _resumen_doc
from arriera.audit.cadena import registrar
from arriera.captura.almacen import almacen
from arriera.db import get_db
from arriera.models import Documento, ItemSolicitud, Persona, Solicitud, User
from arriera.security.cifrado import cifrar, descifrar, hmac_busqueda

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])
ATIENDEN = ("admin", "archivero")


class NuevaSolicitud(BaseModel):
    tipo: str = Field(pattern="^(copia|copia_hc|acceso_datos|constancia)$")
    solicitante: str = Field(min_length=3, max_length=200)
    documento: str | None = Field(None, max_length=20)
    contacto: str | None = Field(None, max_length=160)
    relacion: str | None = Field(None, max_length=60)
    detalle: str | None = Field(None, max_length=2000)
    recibida: date | None = None


class Agregar(BaseModel):
    documento_id: str


class Copia(BaseModel):
    ocultamiento: str = Field("ninguno", pattern="^(ninguno|sensibles|dni_y_sensibles)$")


class CambioEstado(BaseModel):
    estado: str = Field(pattern="^(en_busqueda|entregada|rechazada)$")
    nota: str | None = Field(None, max_length=500)


def _sol(db: Session, sid: str) -> Solicitud:
    try:
        s = db.get(Solicitud, sid)
    except Exception:
        s = None
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa solicitud.")
    return s


def _enmascarar(doc: str | None) -> str | None:
    return None if not doc else "•" * max(0, len(doc) - 3) + doc[-3:]


def _resumen(db: Session, s: Solicitud) -> dict:
    hoy = datetime.now(UTC).date()
    abierta = s.status not in ("entregada", "rechazada")
    n = db.scalar(select(func.count()).select_from(ItemSolicitud).where(ItemSolicitud.request_id == s.id)) or 0
    return {
        "id": str(s.id),
        "numero": s.number,
        "tipo": s.kind,
        "tipo_nombre": srv.TIPOS[s.kind],
        "estado": s.status,
        "estado_nombre": srv.ESTADOS[s.status],
        "solicitante": s.requester_name,
        "relacion": s.relation,
        "recibida": s.received_on.isoformat(),
        "vence": s.due_on.isoformat(),
        "dias_habiles": srv.habiles_entre(hoy, s.due_on) if abierta else None,
        "documentos": n,
        "entregada": s.delivered_at,
    }


def _detalle(db: Session, s: Solicitud) -> dict:
    doc = descifrar(s.requester_doc_enc, f"solicitud:{s.id}") if s.requester_doc_enc else None
    contacto = (
        descifrar(s.requester_contact_enc, f"solicitud:{s.id}:contacto") if s.requester_contact_enc else None
    )
    docs = srv.documentos(db, s)
    sugeridos = []
    if s.requester_doc_hash:  # documentos de la misma persona (por DNI) que aún no están en la solicitud
        p = db.scalar(select(Persona).where(Persona.dni_hash == s.requester_doc_hash))
        if p is not None:
            ya = {d.id for d in docs}
            q = (
                select(Documento)
                .where(Documento.person_id == p.id)
                .order_by(Documento.doc_date.desc().nullslast())
            )
            sugeridos = [_resumen_doc(db, d) for d in db.scalars(q.limit(50)).all() if d.id not in ya]
    return {
        **_resumen(db, s),
        "documento": _enmascarar(doc),
        "contacto": contacto,
        "detalle": s.detail,
        "plazo_dias": srv.plazo_dias(s.kind),
        "items": [_resumen_doc(db, d) for d in docs],
        "sugeridos": sugeridos,
        "ocultamiento": s.redaction,
        "copia": {"paginas": s.copy_pages, "sha256": s.copy_sha256} if s.copy_key else None,
        "nota_entrega": s.delivery_note,
        "historial": s.history or [],
    }


@router.get("/tipos")
def tipos(_: User = Depends(requiere_roles(*ATIENDEN))):
    return {
        "tipos": [{"key": k, "nombre": v, "plazo_dias": srv.plazo_dias(k)} for k, v in srv.TIPOS.items()],
        "ocultamientos": [{"key": k, "nombre": v} for k, v in srv.OCULTAMIENTOS.items()],
    }


@router.get("")
def listar(estado: str | None = None, _: User = Depends(requiere_roles(*ATIENDEN)), db: Session = Depends(get_db)):
    q = select(Solicitud)
    if estado == "abiertas":
        q = q.where(Solicitud.status.notin_(["entregada", "rechazada"]))
    elif estado:
        q = q.where(Solicitud.status == estado)
    q = q.order_by(Solicitud.due_on, Solicitud.created_at).limit(300)
    return [_resumen(db, s) for s in db.scalars(q).all()]


@router.post("", status_code=201)
def crear(
    datos: NuevaSolicitud,
    u: User = Depends(requiere_roles(*ATIENDEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    recibida = datos.recibida or datetime.now(UTC).date()
    s = Solicitud(
        number=srv.nuevo_numero(db),
        kind=datos.tipo,
        requester_name=datos.solicitante.strip(),
        relation=(datos.relacion or "").strip() or None,
        detail=(datos.detalle or "").strip() or None,
        received_on=recibida,
        due_on=srv.sumar_habiles(recibida, srv.plazo_dias(datos.tipo)),
        created_by=u.id,
    )
    db.add(s)
    db.flush()
    doc = "".join(ch for ch in (datos.documento or "") if ch.isalnum())
    if doc:
        s.requester_doc_hash = hmac_busqueda(doc)
        s.requester_doc_enc = cifrar(doc, f"solicitud:{s.id}")
    if datos.contacto and datos.contacto.strip():
        s.requester_contact_enc = cifrar(datos.contacto.strip(), f"solicitud:{s.id}:contacto")
    srv.evento(s, "recibida", u.name, srv.TIPOS[s.kind])
    registrar(
        db,
        "solicitud.creada",
        user_id=u.id,
        object_type="request",
        object_id=s.number,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"tipo": s.kind, "vence": s.due_on.isoformat()},
    )
    db.commit()
    return _detalle(db, s)


@router.get("/{sid}")
def detalle(sid: str, _: User = Depends(requiere_roles(*ATIENDEN)), db: Session = Depends(get_db)):
    return _detalle(db, _sol(db, sid))


def _abierta(s: Solicitud) -> None:
    if s.status in ("entregada", "rechazada"):
        raise HTTPException(status.HTTP_409_CONFLICT, "La solicitud ya está cerrada.")


@router.post("/{sid}/documentos")
def agregar(
    sid: str,
    datos: Agregar,
    u: User = Depends(requiere_roles(*ATIENDEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    s = _sol(db, sid)
    _abierta(s)
    try:
        d = db.get(Documento, datos.documento_id)
    except Exception:
        d = None
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese documento.")
    ya = db.scalar(
        select(ItemSolicitud).where(ItemSolicitud.request_id == s.id, ItemSolicitud.document_id == d.id)
    )
    if ya is None:
        orden = (
            db.scalar(select(func.count()).select_from(ItemSolicitud).where(ItemSolicitud.request_id == s.id)) or 0
        )
        db.add(ItemSolicitud(request_id=s.id, document_id=d.id, order=orden + 1, added_by=u.id))
        if s.status == "recibida":
            s.status = "en_busqueda"
        if s.copy_key:  # la copia anterior ya no refleja la selección
            s.copy_key = s.copy_sha256 = s.copy_pages = None
            s.status = "en_busqueda"
        srv.evento(s, "documento_agregado", u.name, d.title)
        registrar(
            db,
            "solicitud.documento_agregado",
            user_id=u.id,
            object_type="request",
            object_id=s.number,
            ip=ctx.ip,
            details={"documento": str(d.id), "sensibilidad": d.sensitivity},
        )
        db.commit()
    return _detalle(db, s)


@router.delete("/{sid}/documentos/{did}")
def quitar(sid: str, did: str, u: User = Depends(requiere_roles(*ATIENDEN)), db: Session = Depends(get_db)):
    s = _sol(db, sid)
    _abierta(s)
    it = db.scalar(select(ItemSolicitud).where(ItemSolicitud.request_id == s.id, ItemSolicitud.document_id == did))
    if it is not None:
        db.delete(it)
        s.copy_key = s.copy_sha256 = s.copy_pages = None
        s.status = "en_busqueda"
        srv.evento(s, "documento_quitado", u.name, None)
        db.commit()
    return _detalle(db, s)


@router.post("/{sid}/copia")
def copia(
    sid: str,
    datos: Copia,
    u: User = Depends(requiere_roles(*ATIENDEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    s = _sol(db, sid)
    _abierta(s)
    try:
        _, total = srv.generar_copia(db, s, datos.ocultamiento, u.name)
    except srv.ErrorSolicitud as e:
        raise HTTPException(e.estado, e.mensaje) from e
    for d in srv.documentos(db, s):  # cada documento copiado cuenta como acceso (panel Ley 29733 si es N3)
        registrar(
            db,
            "documento.copiado",
            user_id=u.id,
            object_type="document",
            object_id=str(d.id),
            ip=ctx.ip,
            details={"solicitud": s.number, "ocultamiento": datos.ocultamiento, "sensibilidad": d.sensitivity},
        )
    registrar(
        db,
        "solicitud.copia_generada",
        user_id=u.id,
        object_type="request",
        object_id=s.number,
        ip=ctx.ip,
        details={"paginas": total, "ocultamiento": datos.ocultamiento, "sha256": s.copy_sha256},
    )
    db.commit()
    return _detalle(db, s)


@router.get("/{sid}/copia.pdf")
def descargar(
    sid: str,
    u: User = Depends(requiere_roles(*ATIENDEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    s = _sol(db, sid)
    if not s.copy_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todavía no se generó la copia.")
    registrar(db, "solicitud.copia_descargada", user_id=u.id, object_type="request", object_id=s.number, ip=ctx.ip)
    db.commit()
    return Response(
        almacen().leer(s.copy_key),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="copia-{s.number}.pdf"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/{sid}/estado")
def cambiar_estado(
    sid: str,
    datos: CambioEstado,
    u: User = Depends(requiere_roles(*ATIENDEN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    s = _sol(db, sid)
    _abierta(s)
    if datos.estado == "entregada":
        if not s.copy_key:
            raise HTTPException(status.HTTP_409_CONFLICT, "Genera la copia antes de marcarla como entregada.")
        s.delivered_at, s.delivered_by = datetime.now(UTC), u.id
    if datos.estado == "rechazada" and not (datos.nota or "").strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Indica el motivo del rechazo.")
    s.status = datos.estado
    s.delivery_note = (datos.nota or "").strip() or s.delivery_note
    srv.evento(s, datos.estado, u.name, datos.nota)
    registrar(
        db,
        f"solicitud.{datos.estado}",
        user_id=u.id,
        object_type="request",
        object_id=s.number,
        ip=ctx.ip,
        details={"nota": (datos.nota or "")[:200]} if datos.nota else {},
    )
    db.commit()
    return _detalle(db, s)
