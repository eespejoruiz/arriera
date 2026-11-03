"""Paso 4 del flujo (spec 7.5): OCR por página, índice de texto completo y registro de costo."""

import json
import time
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from arriera.captura.almacen import almacen
from arriera.captura.servicio import actualizar_estado_lote
from arriera.config import settings
from arriera.models import Lote, Pagina, PasoProceso
from arriera.providers.ocr import ErrorOCR, ProveedorOCR, ResultadoOCR, proveedor_ocr

LEGIBLES = ("ok", "corregida")
SQL_INDICE = text(
    "UPDATE batch_pages SET tsv = "
    "setweight(to_tsvector('es_unaccent', coalesce(ocr_text, '')), 'A') || "
    "to_tsvector('simple_unaccent', coalesce(ocr_text, '')) WHERE id = :id"
)


def leer_resultado(pag: Pagina) -> dict | None:
    if not pag.ocr_key:
        return None
    return json.loads(almacen().leer(pag.ocr_key))


def procesar_ocr(db: Session, pagina_id, prov: ProveedorOCR | None = None) -> Pagina:
    """Lee la página, guarda el JSON con palabras y cajas, actualiza el índice y registra el paso. Idempotente."""
    pag = db.get(Pagina, pagina_id)
    assert pag is not None
    if pag.qc_status not in LEGIBLES or not pag.image_key:
        pag.ocr_status = "omitida"
        return pag
    prov = prov or proveedor_ocr()
    if prov is None:
        pag.ocr_status = "omitida"
        return pag
    lote = db.get(Lote, pag.batch_id)
    assert lote is not None
    intento = 1 + len(
        db.scalars(
            select(PasoProceso.id).where(PasoProceso.subject_id == str(pag.id), PasoProceso.step == "ocr")
        ).all()
    )
    t0 = time.perf_counter()
    try:
        r: ResultadoOCR = prov.analizar(almacen().leer(pag.image_key))
    except ErrorOCR as e:
        pag.ocr_status = "error"
        db.add(
            PasoProceso(
                subject_type="page",
                subject_id=str(pag.id),
                step="ocr",
                status="error",
                attempt=intento,
                provider=prov.nombre,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                error=str(e)[:2000],
            )
        )
        return pag
    clave = f"work/{lote.code}/{pag.page_index:05d}.ocr.json"
    almacen().guardar(clave, json.dumps(r.a_dict(), ensure_ascii=False).encode(), "application/json")
    pag.ocr_key, pag.ocr_text, pag.ocr_conf, pag.ocr_lang = clave, r.texto, r.confianza, r.idioma
    pag.handwriting_ratio, pag.ocr_at = r.manuscrito, datetime.now(UTC)
    pag.ocr_status = "ok" if r.texto.strip() else "sin_texto"
    # Legibilidad (spec 7.4): con texto suficiente pero confianza baja, la página vuelve a escaneo.
    if len(r.palabras) >= 20 and r.confianza is not None and r.confianza < settings().ocr_confianza_minima:
        pag.qc_status, pag.qc_reason = "reescanear", "Ilegible: el OCR leyó con muy poca confianza"
    db.flush()
    db.execute(SQL_INDICE, {"id": pag.id})
    db.add(
        PasoProceso(
            subject_type="page",
            subject_id=str(pag.id),
            step="ocr",
            status="ok",
            attempt=intento,
            provider=r.proveedor,
            model=r.modelo,
            cost_usd=r.costo_usd,
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )
    )
    actualizar_estado_lote(db, lote)
    return pag
