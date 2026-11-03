"""Endpoints para dispositivos de captura (celulares, agente de escáner). Se autentican con X-Station-Key."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto
from arriera.captura import servicio
from arriera.db import SessionLocal, get_db
from arriera.models import Estacion, Lote, Pagina

router = APIRouter(prefix="/estacion", tags=["dispositivos"])


class Canje(BaseModel):
    token: str = Field(min_length=10, max_length=100)
    modelo: str | None = Field(None, max_length=100)
    plataforma: str | None = Field(None, max_length=60)


def estacion(x_station_key: str | None = Header(None), db: Session = Depends(get_db)) -> Estacion:
    est = servicio.estacion_por_llave(db, x_station_key)
    if est is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Este dispositivo no está emparejado. Escanea un código nuevo."
        )
    return est


def _resumen(db: Session, lote: Lote) -> dict:
    pags = db.scalars(select(Pagina).where(Pagina.batch_id == lote.id).order_by(Pagina.page_index)).all()
    return {
        "lote": lote.code,
        "caja": lote.caja.code,
        "estado": lote.status,
        "paginas": [{"indice": p.page_index, "estado": p.qc_status, "motivo": p.qc_reason} for p in pags],
    }


def _procesar(pid) -> None:
    with SessionLocal() as db:
        servicio.procesar_calidad(db, pid)
        db.commit()


@router.post("/emparejar")
def emparejar(datos: Canje, db: Session = Depends(get_db), ctx: Contexto = Depends(contexto)):
    try:
        est, llave, lote = servicio.canjear_emparejamiento(
            db, datos.token, {"modelo": datos.modelo, "plataforma": datos.plataforma}, ctx.ip
        )
    except servicio.ErrorCaptura as e:
        raise HTTPException(e.estado, e.mensaje) from e
    db.commit()
    return {"llave": llave, **_resumen(db, lote)}


@router.get("/lote")
def lote_actual(est: Estacion = Depends(estacion), db: Session = Depends(get_db)):
    lote = db.scalar(select(Lote).where(Lote.station_id == est.id).order_by(Lote.created_at.desc()))
    db.commit()
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay un lote asignado a este dispositivo.")
    return _resumen(db, lote)


@router.post("/lotes/{code}/paginas", status_code=201)
async def subir_pagina(
    code: str,
    tareas: BackgroundTasks,
    archivo: UploadFile = File(...),
    sha256: str = Form(..., min_length=64, max_length=64),
    est: Estacion = Depends(estacion),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = db.scalar(select(Lote).where(Lote.code == code))
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese lote.")
    datos = await archivo.read()
    try:
        pag = servicio.recibir_pagina(db, lote, est, datos, archivo.content_type or "", sha256, ctx.ip)
    except servicio.ErrorCaptura as e:
        db.rollback()
        raise HTTPException(e.estado, e.mensaje) from e
    db.commit()
    if pag.qc_status == "pendiente":
        tareas.add_task(_procesar, pag.id)
    return {"pagina": pag.page_index, "estado": pag.qc_status}
