"""Solicitudes de copia y de acceso a datos: plazo, documentos, copia con ocultamiento real y entrega auditada.

Ocultamiento real (spec 4.9): las cajas negras se queman sobre la imagen de la página y el PDF se arma solo con
imágenes, sin capa de texto, así que lo oculto no se puede recuperar copiando ni buscando dentro del PDF.
"""

import hashlib
import io
from datetime import UTC, date, datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.captura.almacen import almacen
from arriera.config import settings
from arriera.models import Documento, Extraccion, ItemSolicitud, Pagina, PaginaDocumento, Solicitud

TIPOS = {
    "copia": "Copia de documento o expediente",
    "copia_hc": "Copia de historia clínica",
    "acceso_datos": "Acceso a datos personales (Ley 29733)",
    "constancia": "Constancia o certificado",
}
ESTADOS = {
    "recibida": "Recibida",
    "en_busqueda": "En búsqueda",
    "lista": "Copia lista",
    "entregada": "Entregada",
    "rechazada": "Rechazada",
}
OCULTAMIENTOS = {
    "ninguno": "Sin ocultar",
    "sensibles": "Ocultar datos sensibles (diagnóstico, CIE-10…)",
    "dni_y_sensibles": "Ocultar DNI y datos sensibles",
}
FUENTES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"]


class ErrorSolicitud(Exception):
    def __init__(self, estado: int, mensaje: str):
        self.estado, self.mensaje = estado, mensaje


def plazo_dias(tipo: str) -> int:
    return int(getattr(settings(), f"plazo_{tipo}"))


def sumar_habiles(desde: date, dias: int) -> date:
    d = desde
    while dias > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            dias -= 1
    return d


def habiles_entre(desde: date, hasta: date) -> int:
    """Días hábiles que faltan (positivo) o que pasaron desde el vencimiento (negativo)."""
    if hasta == desde:
        return 0
    paso = 1 if hasta > desde else -1
    n, d = 0, desde
    while d != hasta:
        d += timedelta(days=paso)
        if d.weekday() < 5:
            n += paso
    return n


def nuevo_numero(db: Session) -> str:
    anio = datetime.now(UTC).year
    n = db.scalar(select(func.count()).select_from(Solicitud).where(Solicitud.number.like(f"S-{anio}-%"))) or 0
    return f"S-{anio}-{n + 1:05d}"


def evento(s: Solicitud, accion: str, usuario: str, detalle: str | None = None) -> None:
    s.history = [
        *(s.history or []),
        {"fecha": datetime.now(UTC).isoformat(), "accion": accion, "por": usuario, "detalle": detalle},
    ]


def documentos(db: Session, s: Solicitud) -> list[Documento]:
    ids = db.scalars(
        select(ItemSolicitud.document_id).where(ItemSolicitud.request_id == s.id).order_by(ItemSolicitud.order)
    ).all()
    return [d for d in (db.get(Documento, i) for i in ids) if d is not None]


def _cajas_a_ocultar(db: Session, d: Documento, perfil: str) -> dict[int, list[dict]]:
    """Cajas (0..1) por número de página del documento, según el perfil de ocultamiento."""
    if perfil == "ninguno":
        return {}
    defs = {c["key"]: c for c in d.tipo.fields_schema.get("fields", [])}
    salida: dict[int, list[dict]] = {}
    for e in db.scalars(select(Extraccion).where(Extraccion.document_id == d.id)).all():
        c = defs.get(e.field_key, {})
        ocultar = bool(c.get("sensitive")) or (perfil == "dni_y_sensibles" and c.get("type") == "dni")
        if ocultar and e.bbox:
            salida.setdefault(e.page_no or 1, []).append(e.bbox)
    return salida


def _fuente(tam: int):
    for ruta in FUENTES:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _pagina_copia(jpeg: bytes, cajas: list[dict], leyenda: str) -> Image.Image:
    im = Image.open(io.BytesIO(jpeg)).convert("RGB")
    w, h = im.size
    dib = ImageDraw.Draw(im)
    for c in cajas:  # margen pequeño para que no asomen bordes de letras
        mx, my = 0.006 * w, 0.004 * h
        dib.rectangle([c["x0"] * w - mx, c["y0"] * h - my, c["x1"] * w + mx, c["y1"] * h + my], fill=(0, 0, 0))
    banda = max(28, round(h * 0.022))
    lienzo = Image.new("RGB", (w, h + banda), (255, 255, 255))
    lienzo.paste(im, (0, 0))
    d2 = ImageDraw.Draw(lienzo)
    d2.rectangle([0, h, w, h + banda], fill=(27, 31, 19))
    d2.text(
        (round(banda * 0.5), h + round(banda * 0.22)),
        leyenda,
        fill=(244, 245, 238),
        font=_fuente(round(banda * 0.5)),
    )
    return lienzo


def generar_copia(db: Session, s: Solicitud, perfil: str, emitida_por: str) -> tuple[bytes, int]:
    docs = documentos(db, s)
    if not docs:
        raise ErrorSolicitud(409, "Agrega al menos un documento a la solicitud.")
    hoy = datetime.now(UTC).strftime("%d/%m/%Y")
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setTitle(f"Copia · solicitud {s.number}")
    c.setAuthor("Arriera")
    c.setCreator("Arriera")
    total = 0
    for d in docs:
        ocultar = _cajas_a_ocultar(db, d, perfil)
        pags = db.execute(
            select(Pagina, PaginaDocumento.order)
            .join(PaginaDocumento, PaginaDocumento.batch_page_id == Pagina.id)
            .where(PaginaDocumento.document_id == d.id)
            .order_by(PaginaDocumento.order)
        ).all()
        for n, (p, _orden) in enumerate(pags, 1):
            if not p.image_key:
                continue
            total += 1
            leyenda = f"Copia · solicitud {s.number} · emitida el {hoy} para {s.requester_name[:60]} · no reemplaza al original"
            img = _pagina_copia(almacen().leer(p.image_key), ocultar.get(n, []), leyenda)
            ancho = 595.28
            alto = ancho * img.height / img.width
            c.setPageSize((ancho, alto))
            jb = io.BytesIO()
            img.save(jb, "JPEG", quality=82, optimize=True)
            c.drawImage(ImageReader(io.BytesIO(jb.getvalue())), 0, 0, ancho, alto)
            c.showPage()
    if total == 0:
        raise ErrorSolicitud(409, "Los documentos todavía no tienen imágenes procesadas.")
    c.save()
    pdf = buf.getvalue()
    sha = hashlib.sha256(pdf).hexdigest()
    clave = f"solicitudes/{s.number}/copia-{sha[:12]}.pdf"
    almacen().guardar(clave, pdf, "application/pdf")
    s.copy_key, s.copy_sha256, s.copy_pages, s.redaction = clave, sha, total, perfil
    s.status = "lista"
    evento(s, "copia_generada", emitida_por, f"{total} páginas · {OCULTAMIENTOS[perfil]} · SHA-256 {sha[:16]}…")
    return pdf, total
