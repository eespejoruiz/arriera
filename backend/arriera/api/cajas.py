from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.audit.cadena import registrar
from arriera.captura.hojas import etiqueta_caja
from arriera.db import get_db
from arriera.models import Caja, Lote, Muestreo, User

router = APIRouter(prefix="/cajas", tags=["inventario"])
LEEN = ("admin", "archivero", "operador")


class NuevaCaja(BaseModel):
    code: str = Field(pattern=r"^C-\d{4,6}$")
    shelf_location: str | None = Field(None, max_length=40)
    year_from: int | None = Field(None, ge=1900, le=2100)
    year_to: int | None = Field(None, ge=1900, le=2100)
    series_hint: str | None = Field(None, max_length=120)
    paper_condition: str = Field("bueno", pattern="^(bueno|regular|malo)$")
    estimated_pages: int | None = Field(None, ge=0, le=100000)


class CajaOut(BaseModel):
    code: str
    shelf_location: str | None
    anios: str
    series_hint: str | None
    paper_condition: str
    estimated_pages: int | None
    captured_pages: int
    status: str


class NuevoMuestreo(BaseModel):
    folders_counted: int = Field(ge=1, le=10000)
    pages_counted: int = Field(ge=1, le=100000)


def _anios(c: Caja) -> str:
    if c.year_from and c.year_to and c.year_from != c.year_to:
        return f"{c.year_from}–{c.year_to}"
    return str(c.year_from or c.year_to or "—")


def _out(c: Caja, capturadas: int) -> CajaOut:
    return CajaOut(
        code=c.code,
        shelf_location=c.shelf_location,
        anios=_anios(c),
        series_hint=c.series_hint,
        paper_condition=c.paper_condition,
        estimated_pages=c.estimated_pages,
        captured_pages=capturadas,
        status=c.status,
    )


def _caja(db: Session, code: str) -> Caja:
    c = db.scalar(select(Caja).where(Caja.code == code))
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa caja.")
    return c


@router.get("", response_model=list[CajaOut])
def listar(_: User = Depends(requiere_roles(*LEEN)), db: Session = Depends(get_db)):
    capt = dict(db.execute(select(Lote.box_id, func.sum(Lote.received_pages)).group_by(Lote.box_id)).all())
    return [_out(c, int(capt.get(c.id) or 0)) for c in db.scalars(select(Caja).order_by(Caja.code)).all()]


@router.post("", response_model=CajaOut, status_code=201)
def crear(
    datos: NuevaCaja,
    u: User = Depends(requiere_roles("admin", "archivero")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    if db.scalar(select(Caja).where(Caja.code == datos.code)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una caja con ese código.")
    c = Caja(**datos.model_dump())
    db.add(c)
    db.flush()
    registrar(
        db,
        "caja.registrada",
        user_id=u.id,
        object_type="box",
        object_id=c.code,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
    )
    db.commit()
    return _out(c, 0)


@router.post("/{code}/muestreos", status_code=201)
def muestrear(
    code: str,
    datos: NuevoMuestreo,
    u: User = Depends(requiere_roles("admin", "archivero")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    c = _caja(db, code)
    db.add(
        Muestreo(
            box_id=c.id, folders_counted=datos.folders_counted, pages_counted=datos.pages_counted, sampled_by=u.id
        )
    )
    if c.estimated_pages is None:
        c.estimated_pages = datos.pages_counted
    registrar(
        db,
        "caja.muestreada",
        user_id=u.id,
        object_type="box",
        object_id=c.code,
        ip=ctx.ip,
        details=datos.model_dump(),
    )
    db.commit()
    return {"ok": True}


@router.get("/{code}/etiqueta.pdf")
def etiqueta(code: str, u: User = Depends(requiere_roles(*LEEN)), db: Session = Depends(get_db)):
    c = _caja(db, code)
    pdf = etiqueta_caja(c.code, _anios(c), c.series_hint or "", c.shelf_location or "—")
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="etiqueta-{c.code}.pdf"'},
    )


@router.get("/resumen/inventario")
def resumen(_: User = Depends(requiere_roles(*LEEN)), db: Session = Depends(get_db)):
    cajas = db.scalar(select(func.count(Caja.id))) or 0
    muestras = db.execute(select(func.avg(Muestreo.pages_counted), func.count(Muestreo.id))).one()
    promedio = float(muestras[0] or 0)
    estimadas = (
        round(promedio * cajas) if promedio else int(db.scalar(select(func.sum(Caja.estimated_pages))) or 0)
    )
    capturadas = int(db.scalar(select(func.sum(Lote.received_pages))) or 0)
    return {
        "cajas": cajas,
        "cajas_muestreadas": muestras[1],
        "paginas_por_caja": round(promedio),
        "paginas_estimadas": estimadas,
        "margen": 0.1,
        "paginas_capturadas": capturadas,
    }
