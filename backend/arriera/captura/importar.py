"""Importación de archivos que ya son digitales (PDF escaneados, exportaciones de otro gestor, fotos sueltas).

Cada página entra al mismo flujo que una hoja escaneada: control de calidad, OCR, separación, clasificación y
extracción. El PDF original se guarda tal cual, con su huella, junto a las imágenes de sus páginas.
"""

import hashlib
import io
from datetime import UTC, datetime

import pypdfium2 as pdfium
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.audit.cadena import registrar
from arriera.captura.almacen import almacen
from arriera.captura.servicio import TIPOS_IMAGEN, ErrorCaptura
from arriera.config import settings
from arriera.models import ArchivoLote, Lote, Pagina

PDF = "application/pdf"
DPI_RENDER = 300  # el mínimo de las microformas; también rinde bien en el OCR
MAX_PAGINAS_PDF = 500


def _paginas_pdf(datos: bytes) -> list[bytes]:
    try:
        doc = pdfium.PdfDocument(datos)
    except pdfium.PdfiumError as e:
        raise ErrorCaptura(422, "El PDF está dañado o protegido con contraseña.") from e
    try:
        if len(doc) > MAX_PAGINAS_PDF:
            raise ErrorCaptura(
                413, f"El PDF tiene {len(doc)} páginas; el máximo por archivo es {MAX_PAGINAS_PDF}."
            )
        salida = []
        for i in range(len(doc)):
            img = doc[i].render(scale=DPI_RENDER / 72).to_pil().convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            salida.append(buf.getvalue())
        return salida
    finally:
        doc.close()


def _guardar(
    db: Session, lote: Lote, datos: bytes, mime: str, ext: str, paginas: int = 1
) -> tuple[ArchivoLote, bool]:
    sha = hashlib.sha256(datos).hexdigest()
    previo = db.scalar(select(ArchivoLote).where(ArchivoLote.batch_id == lote.id, ArchivoLote.sha256 == sha))
    if previo is not None:
        return previo, False
    clave = f"raw/batches/{lote.code}/{sha}.{ext}"
    almacen().guardar(clave, datos, mime)
    arch = ArchivoLote(
        batch_id=lote.id, storage_key=clave, sha256=sha, size_bytes=len(datos), mime=mime, page_count=paginas
    )
    db.add(arch)
    db.flush()
    return arch, True


def importar_archivo(
    db: Session, lote: Lote, usuario_id, datos: bytes, tipo: str, nombre: str, ip: str | None
) -> list[Pagina]:
    """Agrega al lote las páginas de un PDF o una imagen. Idempotente: el mismo archivo no se duplica."""
    if lote.status == "cerrado":
        raise ErrorCaptura(409, "El lote ya está cerrado.")
    limite = settings().max_importacion_mb
    if len(datos) > limite * 1024 * 1024:
        raise ErrorCaptura(413, f"El archivo pesa más de {limite} MB.")
    if tipo == PDF or datos[:5] == b"%PDF-":
        imagenes = _paginas_pdf(datos)
        if not imagenes:
            raise ErrorCaptura(422, "El PDF no tiene páginas.")
        original, nuevo = _guardar(db, lote, datos, PDF, "pdf", len(imagenes))
        if not nuevo:
            return []
        partes = [(img, "image/png", "png") for img in imagenes]
    elif tipo in TIPOS_IMAGEN:
        partes = [(datos, tipo, TIPOS_IMAGEN[tipo])]
        original = None
    else:
        raise ErrorCaptura(415, "Formato no admitido. Sube PDF, JPG, PNG o WEBP.")

    nuevas: list[Pagina] = []
    idx = db.scalar(select(func.max(Pagina.page_index)).where(Pagina.batch_id == lote.id)) or 0
    for img, mime, ext in partes:
        arch, es_nuevo = _guardar(db, lote, img, mime, ext)
        if not es_nuevo:
            continue
        idx += 1
        pag = Pagina(batch_id=lote.id, batch_file_id=arch.id, page_index=idx)
        db.add(pag)
        nuevas.append(pag)
    if not nuevas:
        return []
    lote.received_pages = idx
    lote.received_at = datetime.now(UTC)
    if lote.status == "creado":
        lote.status = "recibiendo"
    db.flush()
    registrar(
        db,
        "captura.archivo_importado",
        user_id=usuario_id,
        object_type="batch",
        object_id=lote.code,
        ip=ip,
        details={
            "archivo": nombre[:120],
            "tipo": PDF if original else tipo,
            "sha256": original.sha256 if original else hashlib.sha256(datos).hexdigest(),
            "paginas": [p.page_index for p in nuevas],
        },
    )
    return nuevas
