"""Modo microformas por lote: pasos de la NTP con responsable, actas y manifiesto (adenda 02, sección 3)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.audit.cadena import registrar
from arriera.captura import microformas as mf
from arriera.captura.almacen import almacen
from arriera.db import get_db
from arriera.models import Acta, Lote, User

router = APIRouter(prefix="/microformas", tags=["microformas"])
PARTICIPAN = ("admin", "archivero", "operador", "validador")


class Paso(BaseModel):
    notas: str | None = Field(None, max_length=500)


def _lote(db: Session, code: str) -> Lote:
    lote = db.scalar(select(Lote).where(Lote.code == code))
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese lote.")
    return lote


@router.get("/lotes/{code}")
def ver(code: str, _: User = Depends(requiere_roles(*PARTICIPAN)), db: Session = Depends(get_db)):
    return mf.estado(db, _lote(db, code))


@router.post("/lotes/{code}/pasos/{paso}")
def paso(
    code: str,
    paso: str,
    datos: Paso,
    u: User = Depends(requiere_roles(*PARTICIPAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    try:
        return mf.registrar_paso(db, _lote(db, code), paso, u, [r.key for r in u.roles], datos.notas, ctx.ip)
    except mf.ErrorMicroformas as e:
        raise HTTPException(e.estado, e.mensaje) from e


@router.get("/actas/{aid}.pdf")
def acta(
    aid: str,
    u: User = Depends(requiere_roles("admin", "archivero", "auditor")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    try:
        a = db.get(Acta, aid)
    except Exception:
        a = None
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa acta.")
    registrar(db, "acta.descargada", user_id=u.id, object_type="act", object_id=a.number, ip=ctx.ip)
    db.commit()
    return Response(
        almacen().leer(a.pdf_key),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{a.number}.pdf"'},
    )
