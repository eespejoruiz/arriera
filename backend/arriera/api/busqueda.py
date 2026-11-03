"""Primera búsqueda (Sprint 2): texto completo por página, con filtros, fragmentos y resaltado en el visor.

Hasta que existan documentos clasificados con su nivel de sensibilidad (Sprints 3 y 4), la búsqueda sobre el texto
de las páginas queda solo para administración, archivo y validación: el rol de consulta no ve contenido todavía.
"""

import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.audit.cadena import registrar
from arriera.captura.almacen import almacen
from arriera.config import settings
from arriera.db import SessionLocal, get_db
from arriera.models import Lote, Pagina, PasoProceso, User
from arriera.procesamiento.ocr import leer_resultado, procesar_ocr

router = APIRouter(tags=["busqueda"])
BUSCAN = ("admin", "archivero", "validador")
PROCESAN = ("admin", "archivero")
MARCA_INI, MARCA_FIN = "\x02", "\x03"  # el cliente los convierte en <mark>; nunca HTML desde el servidor

# Consulta como tsquery en español (raíces) o "simple" (palabras exactas, nombres, otros idiomas).
TSQ = "(websearch_to_tsquery('es_unaccent', :q) || websearch_to_tsquery('simple_unaccent', :q))"
# Para resaltar, cualquier término sirve: los operadores se vuelven O.
TSQ_O = "regexp_replace(websearch_to_tsquery('{cfg}', :q)::text, '<->|<[0-9]+>|&', '|', 'g')::tsquery"


def _consulta(q: str) -> str:
    q = re.sub(r"\s+", " ", q or "").strip()
    if not q:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Escribe qué quieres buscar.")
    return q[:200]


@router.get("/busqueda")
def buscar(
    q: str,
    caja: str | None = None,
    lote: str | None = None,
    idioma: str | None = None,
    pagina: int = Query(1, ge=1, le=200),
    _: User = Depends(requiere_roles(*BUSCAN)),
    db: Session = Depends(get_db),
):
    q = _consulta(q)
    filtros, params = ["p.tsv @@ " + TSQ], {"q": q}
    if caja:
        filtros.append("c.code = :caja")
        params["caja"] = caja
    if lote:
        filtros.append("b.code = :lote")
        params["lote"] = lote
    base_sin_idioma = " AND ".join(filtros)
    if idioma:
        filtros.append("coalesce(p.ocr_lang, '?') = :idioma")
        params["idioma"] = idioma
    donde = " AND ".join(filtros)
    desde = "FROM batch_pages p JOIN batches b ON b.id = p.batch_id JOIN boxes c ON c.id = b.box_id"
    total = db.execute(text(f"SELECT count(*) {desde} WHERE {donde}"), params).scalar_one()  # noqa: S608
    filas = db.execute(
        text(
            f"""SELECT p.id, b.code AS lote, c.code AS caja, p.page_index, p.ocr_lang, p.ocr_conf,
                   ts_rank_cd(p.tsv, {TSQ}) AS rango,
                   ts_headline('es_unaccent', p.ocr_text, {TSQ_O.format(cfg="es_unaccent")},
                     'StartSel=' || chr(2) || ', StopSel=' || chr(3) ||
                     ', MaxFragments=2, MaxWords=22, MinWords=8, FragmentDelimiter= … ') AS fragmento
                {desde} WHERE {donde}
                ORDER BY rango DESC, b.code, p.page_index
                LIMIT 20 OFFSET :salto"""  # noqa: S608  (filtros armados con parámetros)
        ),
        {**params, "salto": (pagina - 1) * 20},
    ).mappings()
    faceta_caja = db.execute(
        text(f"SELECT c.code, count(*) n {desde} WHERE {donde} GROUP BY c.code ORDER BY n DESC LIMIT 12"),  # noqa: S608
        params,
    ).all()
    faceta_idioma = db.execute(
        text(
            f"SELECT coalesce(p.ocr_lang, '?') idioma, count(*) n {desde} WHERE {base_sin_idioma} "  # noqa: S608
            "GROUP BY 1 ORDER BY n DESC"
        ),
        {k: v for k, v in params.items() if k != "idioma"},
    ).all()
    return {
        "consulta": q,
        "total": total,
        "pagina": pagina,
        "resultados": [
            {
                "pagina_id": str(f["id"]),
                "lote": f["lote"],
                "caja": f["caja"],
                "indice": f["page_index"],
                "idioma": f["ocr_lang"],
                "confianza": f["ocr_conf"],
                "fragmento": f["fragmento"],
                "rango": round(float(f["rango"]), 4),
            }
            for f in filas
        ],
        "facetas": {
            "cajas": [{"valor": c, "n": n} for c, n in faceta_caja],
            "idiomas": [{"valor": i, "n": n} for i, n in faceta_idioma],
        },
        "marcas": [MARCA_INI, MARCA_FIN],
    }


def _pagina(db: Session, pid: str) -> Pagina:
    try:
        p = db.get(Pagina, pid)
    except Exception:  # id mal formado
        p = None
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa página.")
    return p


@router.get("/busqueda/paginas/{pid}")
def ver_pagina(
    pid: str,
    q: str | None = None,
    u: User = Depends(requiere_roles(*BUSCAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    p = _pagina(db, pid)
    lote = db.get(Lote, p.batch_id)
    assert lote is not None
    ocr = leer_resultado(p) or {}
    palabras = ocr.get("palabras", [])
    resaltes = []
    if q and q.strip() and palabras:
        coinciden = db.execute(
            text(
                f"""SELECT i FROM unnest(CAST(:ws AS text[])) WITH ORDINALITY AS w(t, i)
                    WHERE to_tsvector('es_unaccent', t) @@ {TSQ_O.format(cfg="es_unaccent")}
                       OR to_tsvector('simple_unaccent', t) @@ {TSQ_O.format(cfg="simple_unaccent")}"""  # noqa: S608
            ),
            {"ws": [w["texto"] for w in palabras], "q": _consulta(q)},
        ).scalars()
        for i in coinciden:
            w = palabras[i - 1]
            resaltes.append({k: round(w[k], 4) for k in ("x0", "y0", "x1", "y1")})
    registrar(
        db,
        "pagina.vista",
        user_id=u.id,
        object_type="page",
        object_id=str(p.id),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"lote": lote.code, "pagina": p.page_index},
    )
    db.commit()
    return {
        "pagina_id": str(p.id),
        "lote": lote.code,
        "caja": lote.caja.code,
        "indice": p.page_index,
        "total_paginas": lote.received_pages,
        "ancho": p.width,
        "alto": p.height,
        "idioma": p.ocr_lang,
        "confianza": p.ocr_conf,
        "manuscrito": p.handwriting_ratio,
        "ocr": p.ocr_status,
        "texto": p.ocr_text or "",
        "resaltes": resaltes,
    }


@router.get("/busqueda/paginas/{pid}/imagen")
def imagen(pid: str, _: User = Depends(requiere_roles(*BUSCAN)), db: Session = Depends(get_db)):
    p = _pagina(db, pid)
    if not p.image_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no disponible todavía.")
    return Response(
        almacen().leer(p.image_key), media_type="image/jpeg", headers={"Cache-Control": "private, max-age=300"}
    )


@router.get("/busqueda/paginas/{pid}/miniatura")
def miniatura(pid: str, _: User = Depends(requiere_roles(*BUSCAN)), db: Session = Depends(get_db)):
    p = _pagina(db, pid)
    if not p.thumb_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miniatura no disponible todavía.")
    return Response(
        almacen().leer(p.thumb_key), media_type="image/webp", headers={"Cache-Control": "private, max-age=300"}
    )


# ------------------------------------------------------------------ procesamiento
def _ocr_en_cola(ids: list) -> None:
    for pid in ids:
        with SessionLocal() as db:
            procesar_ocr(db, pid)
            db.commit()


@router.post("/procesamiento/lotes/{code}/ocr")
def reprocesar_ocr(
    code: str,
    tareas: BackgroundTasks,
    u: User = Depends(requiere_roles(*PROCESAN)),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    lote = db.scalar(select(Lote).where(Lote.code == code))
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese lote.")
    ids = db.scalars(
        select(Pagina.id).where(
            Pagina.batch_id == lote.id,
            Pagina.qc_status.in_(["ok", "corregida"]),
            Pagina.ocr_status.in_(["pendiente", "error", "omitida"]),
        )
    ).all()
    registrar(
        db,
        "lote.ocr_solicitado",
        user_id=u.id,
        object_type="batch",
        object_id=code,
        ip=ctx.ip,
        details={"paginas": len(ids)},
    )
    db.commit()
    tareas.add_task(_ocr_en_cola, list(ids))
    return {"lote": code, "en_cola": len(ids)}


@router.get("/procesamiento/resumen")
def resumen(_: User = Depends(requiere_roles(*PROCESAN)), db: Session = Depends(get_db)):
    """Costo y velocidad medidos del OCR (criterio del Sprint 2)."""
    filas = db.execute(
        select(
            PasoProceso.provider,
            func.count(),
            func.coalesce(func.sum(PasoProceso.cost_usd), 0.0),
            func.coalesce(func.avg(PasoProceso.duration_ms), 0.0),
        )
        .where(PasoProceso.step == "ocr", PasoProceso.status == "ok")
        .group_by(PasoProceso.provider)
    ).all()
    errores = db.scalar(select(func.count()).where(PasoProceso.step == "ocr", PasoProceso.status == "error"))
    por_estado = dict(db.execute(select(Pagina.ocr_status, func.count()).group_by(Pagina.ocr_status)).all())
    return {
        "proveedor_activo": settings().ocr_proveedor,
        "paginas_por_estado": por_estado,
        "errores": errores,
        "proveedores": [
            {
                "proveedor": prov,
                "paginas": n,
                "costo_usd": round(costo, 4),
                "usd_por_mil": round(costo / n * 1000, 2) if n else 0,
                "segundos_por_pagina": round(ms / 1000, 2),
            }
            for prov, n, costo, ms in filas
        ],
    }
