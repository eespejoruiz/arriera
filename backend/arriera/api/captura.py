from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.api.documentos import ia_en_segundo_plano
from arriera.audit.cadena import registrar
from arriera.captura import servicio
from arriera.captura.almacen import almacen
from arriera.captura.hojas import hoja_de_lote
from arriera.config import settings
from arriera.db import get_db
from arriera.models import Caja, Lote, Pagina, User
from arriera.procesamiento.ocr import leer_resultado
from arriera.procesamiento.pdf import pdf_buscable
from arriera.security.totp import qr_svg

router = APIRouter(prefix="/captura", tags=["captura"])
CAPTURAN = ("admin", "archivero", "operador")


class NuevoLote(BaseModel):
    caja: str = Field(pattern=r"^C-\d{4,6}$")
    origen: str = Field("celular", pattern="^(celular|agente|red|navegador)$")
    esperadas: int | None = Field(None, ge=1, le=5000)
    microformas: bool = False


class PaginaOut(BaseModel):
    id: str
    indice: int
    estado: str
    motivo: str | None
    inclinacion: float | None
    ocr: str = "pendiente"
    idioma: str | None = None


class LoteOut(BaseModel):
    code: str
    caja: str
    origen: str
    estado: str
    recibidas: int
    esperadas: int | None
    creado: datetime
    rechazos: int = 0
    paginas: list[PaginaOut] | None = None
    ia: dict | None = None
    microformas: bool = False


def _lote(db: Session, code: str) -> Lote:
    lote = db.scalar(select(Lote).where(Lote.code == code))
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese lote.")
    return lote


def _out(db: Session, lote: Lote, con_paginas: bool = False) -> LoteOut:
    pags = db.scalars(select(Pagina).where(Pagina.batch_id == lote.id).order_by(Pagina.page_index)).all()
    return LoteOut(
        code=lote.code,
        caja=lote.caja.code,
        origen=lote.origen,
        estado=lote.status,
        recibidas=lote.received_pages,
        esperadas=lote.expected_pages,
        creado=lote.created_at,
        rechazos=sum(1 for p in pags if p.qc_status == "reescanear"),
        ia=(lote.manifest or {}).get("ia"),
        microformas=lote.microformas,
        paginas=[
            PaginaOut(
                id=str(p.id),
                indice=p.page_index,
                estado=p.qc_status,
                motivo=p.qc_reason,
                inclinacion=p.skew_deg,
                ocr=p.ocr_status,
                idioma=p.ocr_lang,
            )
            for p in pags
        ]
        if con_paginas
        else None,
    )


@router.get("/lotes", response_model=list[LoteOut])
def listar(limite: int = 50, _: User = Depends(requiere_roles(*CAPTURAN)), db: Session = Depends(get_db)):
    lotes = db.scalars(select(Lote).order_by(Lote.created_at.desc()).limit(min(limite, 200))).all()
    return [_out(db, lote) for lote in lotes]


@router.post("/lotes", response_model=LoteOut, status_code=201)
def crear(
    datos: NuevoLote,
    u: User = Depends(requiere_roles(*CAPTURAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    caja = db.scalar(select(Caja).where(Caja.code == datos.caja))
    if caja is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa caja.")
    lote = Lote(
        code=servicio.nuevo_codigo_lote(db),
        box_id=caja.id,
        operator_id=u.id,
        origen=datos.origen,
        expected_pages=datos.esperadas,
        microformas=datos.microformas,
    )
    db.add(lote)
    if caja.status == "registrada":
        caja.status = "en_captura"
    db.flush()
    registrar(
        db,
        "lote.creado",
        user_id=u.id,
        object_type="batch",
        object_id=lote.code,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"caja": caja.code, "origen": datos.origen, "microformas": datos.microformas},
    )
    db.commit()
    db.refresh(lote)
    return _out(db, lote)


@router.get("/lotes/{code}", response_model=LoteOut)
def detalle(code: str, _: User = Depends(requiere_roles(*CAPTURAN)), db: Session = Depends(get_db)):
    return _out(db, _lote(db, code), con_paginas=True)


@router.get("/lotes/{code}/hoja.pdf")
def hoja(
    code: str,
    u: User = Depends(requiere_roles(*CAPTURAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = _lote(db, code)
    pdf = hoja_de_lote(
        lote.code, lote.caja.code, u.name, datetime.now(UTC), demo=settings().app_env != "production"
    )
    lote.cover_printed_at = datetime.now(UTC)
    registrar(db, "lote.hoja_impresa", user_id=u.id, object_type="batch", object_id=lote.code, ip=ctx.ip)
    db.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="hoja-{lote.code}.pdf"'},
    )


@router.post("/lotes/{code}/emparejar")
def emparejar(
    code: str,
    u: User = Depends(requiere_roles(*CAPTURAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = _lote(db, code)
    if lote.status == "cerrado":
        raise HTTPException(status.HTTP_409_CONFLICT, "El lote ya está cerrado.")
    token, vence = servicio.crear_emparejamiento(db, lote, u.id)
    registrar(
        db, "estacion.codigo_emparejamiento", user_id=u.id, object_type="batch", object_id=lote.code, ip=ctx.ip
    )
    db.commit()
    url = f"{settings().url_publica.rstrip('/')}/m/?t={token}"
    return {"url": url, "qr_svg": qr_svg(url), "vence": vence}


@router.post("/lotes/{code}/cerrar", response_model=LoteOut)
def cerrar(
    code: str,
    tareas: BackgroundTasks,
    u: User = Depends(requiere_roles(*CAPTURAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = _lote(db, code)
    pendientes = db.scalars(
        select(Pagina).where(Pagina.batch_id == lote.id, Pagina.qc_status.in_(["pendiente", "reescanear"]))
    ).all()
    if pendientes:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Hay {len(pendientes)} páginas pendientes o por volver a escanear."
        )
    lote.status = "cerrado"
    tareas.add_task(ia_en_segundo_plano, lote.id)  # separar, clasificar y extraer
    registrar(
        db,
        "lote.cerrado",
        user_id=u.id,
        object_type="batch",
        object_id=lote.code,
        ip=ctx.ip,
        details={"paginas": lote.received_pages},
    )
    db.commit()
    return _out(db, lote)


@router.get("/paginas/{pid}/miniatura")
def miniatura(pid: str, _: User = Depends(requiere_roles(*CAPTURAN)), db: Session = Depends(get_db)):
    p = db.get(Pagina, pid)
    if p is None or not p.thumb_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miniatura no disponible todavía.")
    return Response(
        almacen().leer(p.thumb_key), media_type="image/webp", headers={"Cache-Control": "private, max-age=300"}
    )


@router.get("/lotes/{code}/buscable.pdf")
def pdf_del_lote(
    code: str,
    u: User = Depends(requiere_roles("admin", "archivero")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    """PDF buscable del lote: páginas legibles en orden, con la capa de texto del OCR."""
    lote = _lote(db, code)
    pags = db.scalars(
        select(Pagina)
        .where(Pagina.batch_id == lote.id, Pagina.qc_status.in_(["ok", "corregida"]))
        .order_by(Pagina.page_index)
    ).all()
    if not pags:
        raise HTTPException(status.HTTP_409_CONFLICT, "El lote todavía no tiene páginas legibles.")
    pdf = pdf_buscable(
        [(almacen().leer(p.image_key), leer_resultado(p)) for p in pags if p.image_key],
        titulo=f"Lote {lote.code} · Caja {lote.caja.code}",
    )
    registrar(
        db,
        "lote.pdf_descargado",
        user_id=u.id,
        object_type="batch",
        object_id=lote.code,
        ip=ctx.ip,
        details={"paginas": len(pags)},
    )
    db.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{lote.code}.pdf"'},
    )
