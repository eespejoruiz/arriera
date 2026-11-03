"""Lógica de captura: códigos de lote, emparejamiento de celulares, recepción verificada y calidad."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from arriera.audit.cadena import registrar
from arriera.captura import calidad
from arriera.captura.almacen import almacen
from arriera.config import settings
from arriera.models import ArchivoLote, Emparejamiento, Estacion, Lote, Pagina

A4_ANCHO_PULGADAS = 8.27
DPI_MICROFORMAS = 300  # NTP 392.030-2: captura a 300 dpi como mínimo
TIPOS_IMAGEN = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class ErrorCaptura(Exception):
    def __init__(self, estado: int, mensaje: str):
        super().__init__(mensaje)
        self.estado, self.mensaje = estado, mensaje


def _h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def nuevo_codigo_lote(db: Session) -> str:
    n = db.execute(text("SELECT nextval('batch_code_seq')")).scalar_one()
    return f"L-{datetime.now(UTC):%Y}-{n:06d}"


def crear_emparejamiento(db: Session, lote: Lote, usuario_id) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(24)
    vence = datetime.now(UTC) + timedelta(minutes=settings().emparejamiento_min)
    db.add(Emparejamiento(token_hash=_h(token), batch_id=lote.id, created_by=usuario_id, expires_at=vence))
    return token, vence


def canjear_emparejamiento(db: Session, token: str, info: dict, ip: str | None) -> tuple[Estacion, str, Lote]:
    e = db.scalar(select(Emparejamiento).where(Emparejamiento.token_hash == _h(token or "")).with_for_update())
    ahora = datetime.now(UTC)
    if e is None or e.used_at is not None or e.expires_at <= ahora:
        raise ErrorCaptura(410, "El código ya se usó o venció. Genera uno nuevo desde Captura.")
    llave = "est_" + secrets.token_urlsafe(32)
    nombre = (info.get("modelo") or "Celular")[:100]
    est = Estacion(
        name=nombre,
        kind="celular",
        api_key_hash=_h(llave),
        paired_by=e.created_by,
        device_info=info,
        last_heartbeat_at=ahora,
    )
    db.add(est)
    db.flush()
    e.used_at, e.station_id = ahora, est.id
    lote = db.get(Lote, e.batch_id)
    assert lote is not None
    lote.station_id = est.id
    registrar(
        db,
        "estacion.emparejada",
        actor_type="station",
        user_id=e.created_by,
        object_type="station",
        object_id=str(est.id),
        ip=ip,
        details={"lote": lote.code, "tipo": "celular"},
    )
    return est, llave, lote


def estacion_por_llave(db: Session, llave: str | None) -> Estacion | None:
    if not llave:
        return None
    est = db.scalar(select(Estacion).where(Estacion.api_key_hash == _h(llave), Estacion.is_active.is_(True)))
    if est is not None:
        est.last_heartbeat_at = datetime.now(UTC)
    return est


def recibir_pagina(
    db: Session, lote: Lote, est: Estacion, datos: bytes, tipo: str, sha_declarado: str, ip: str | None
) -> Pagina:
    """Guarda el original con su huella verificada y crea la página pendiente de control de calidad."""
    if lote.status == "cerrado":
        raise ErrorCaptura(409, "El lote ya está cerrado.")
    if lote.station_id != est.id:
        raise ErrorCaptura(403, "Este dispositivo no está emparejado con ese lote.")
    if tipo not in TIPOS_IMAGEN:
        raise ErrorCaptura(415, "Formato no admitido. Envía JPG, PNG o WEBP.")
    if len(datos) > settings().max_imagen_mb * 1024 * 1024:
        raise ErrorCaptura(413, "La imagen es demasiado grande.")
    sha = hashlib.sha256(datos).hexdigest()
    if sha != (sha_declarado or "").lower():
        raise ErrorCaptura(422, "La huella SHA-256 no coincide: la imagen llegó incompleta. Se reintentará.")
    previo = db.scalar(select(ArchivoLote).where(ArchivoLote.batch_id == lote.id, ArchivoLote.sha256 == sha))
    if previo is not None:  # reintento idempotente
        pag = db.scalar(select(Pagina).where(Pagina.batch_file_id == previo.id))
        assert pag is not None
        return pag
    clave = f"raw/batches/{lote.code}/{sha}.{TIPOS_IMAGEN[tipo]}"
    almacen().guardar(clave, datos, tipo)
    arch = ArchivoLote(batch_id=lote.id, storage_key=clave, sha256=sha, size_bytes=len(datos), mime=tipo)
    db.add(arch)
    db.flush()
    idx = (db.scalar(select(func.max(Pagina.page_index)).where(Pagina.batch_id == lote.id)) or 0) + 1
    pag = Pagina(batch_id=lote.id, batch_file_id=arch.id, page_index=idx)
    db.add(pag)
    lote.received_pages = idx
    lote.received_at = datetime.now(UTC)
    if lote.status == "creado":
        lote.status = "recibiendo"
    db.flush()
    registrar(
        db,
        "captura.pagina_recibida",
        actor_type="station",
        object_type="batch",
        object_id=lote.code,
        ip=ip,
        details={"pagina": idx, "sha256": sha, "bytes": len(datos), "estacion": str(est.id)},
    )
    return pag


def procesar_calidad(db: Session, pagina_id) -> Pagina:
    """Control de calidad, imagen de trabajo y miniatura. Idempotente."""
    pag = db.get(Pagina, pagina_id)
    assert pag is not None
    arch = db.get(ArchivoLote, pag.batch_file_id)
    lote = db.get(Lote, pag.batch_id)
    assert arch is not None and lote is not None
    r = calidad.evaluar(almacen().leer(arch.storage_key))
    base = f"work/{lote.code}/{pag.page_index:05d}"
    almacen().guardar(base + ".jpg", calidad.a_jpeg(r.imagen), "image/jpeg")
    almacen().guardar(base + ".thumb.webp", calidad.miniatura(r.imagen), "image/webp")
    pag.image_key, pag.thumb_key = base + ".jpg", base + ".thumb.webp"
    pag.width, pag.height = r.imagen.size
    pag.blank_score, pag.blur_score, pag.skew_deg = r.tinta, r.borrosidad, r.inclinacion
    pag.qc_status, pag.qc_reason = r.estado, r.motivo
    pag.dpi = round(min(r.imagen.size) / A4_ANCHO_PULGADAS)
    if lote.microformas and pag.qc_status in ("ok", "corregida") and pag.dpi < DPI_MICROFORMAS:
        pag.qc_status = "reescanear"
        pag.qc_reason = f"Resolución de {pag.dpi} dpi; las microformas piden {DPI_MICROFORMAS} como mínimo"
    db.flush()
    actualizar_estado_lote(db, lote)
    return pag


def actualizar_estado_lote(db: Session, lote: Lote) -> None:
    estados = db.scalars(select(Pagina.qc_status).where(Pagina.batch_id == lote.id)).all()
    if lote.status == "cerrado" or not estados:
        return
    if "pendiente" in estados:
        lote.status = "procesando" if lote.status != "recibiendo" else "recibiendo"
    elif "reescanear" in estados:
        lote.status = "con_rechazos"
    else:
        lote.status = "procesado"
