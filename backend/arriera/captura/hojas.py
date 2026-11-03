"""Hojas imprimibles con QR: hoja de lote (A4) y etiqueta de caja (10 × 6 cm)."""

import hashlib
import io
from datetime import datetime

import segno
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from arriera.config import settings


def carga_qr(*partes: str) -> str:
    """Contenido del QR con checksum: ARR1|B|L-2026-000123|C-0045|a1b2c3."""
    base = "|".join(("ARR1", *partes))
    return f"{base}|{hashlib.sha256(base.encode()).hexdigest()[:6]}"


def leer_qr(texto: str) -> list[str] | None:
    partes = (texto or "").strip().split("|")
    if len(partes) < 3 or partes[0] != "ARR1":
        return None
    base, suma = "|".join(partes[:-1]), partes[-1]
    return partes[1:-1] if hashlib.sha256(base.encode()).hexdigest()[:6] == suma else None


def _qr_png(texto: str) -> ImageReader:
    buf = io.BytesIO()
    segno.make(texto, error="q").save(buf, kind="png", scale=12, border=0)
    buf.seek(0)
    return ImageReader(buf)


def _pie_demo(c: canvas.Canvas, ancho: float) -> None:
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0.63, 0.22, 0.16)
    c.drawCentredString(ancho / 2, 1.2 * cm, "DATOS DEMO · NO VÁLIDO")
    c.setFillColorRGB(0, 0, 0)


def hoja_de_lote(lote: str, caja: str, operador: str, fecha: datetime, demo: bool = True) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setTitle(f"Hoja de lote {lote}")
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 3.2 * cm, "HOJA DE LOTE")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 4.1 * cm, settings().institucion)
    lado = 6 * cm
    c.drawImage(_qr_png(carga_qr("B", lote, caja)), (w - lado) / 2, h / 2 - lado / 2 + 1.5 * cm, lado, lado)
    c.setFont("Courier-Bold", 30)
    c.drawCentredString(w / 2, h / 2 - 3.2 * cm, lote)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h / 2 - 4.4 * cm, f"Caja {caja} · {operador} · {fecha:%d/%m/%Y %H:%M}")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, 4.2 * cm, "Poner como primera hoja del lote")
    c.setFont("Helvetica", 9)
    c.drawCentredString(w / 2, 3.4 * cm, "Arriera · gestión documental con IA")
    if demo:
        _pie_demo(c, w)
    c.showPage()
    c.save()
    return buf.getvalue()


def etiqueta_caja(caja: str, anios: str, serie: str, estante: str) -> bytes:
    buf = io.BytesIO()
    tam = (10 * cm, 6 * cm)
    c = canvas.Canvas(buf, pagesize=tam)
    c.setTitle(f"Etiqueta {caja}")
    c.drawImage(_qr_png(carga_qr("C", caja)), 0.5 * cm, 0.9 * cm, 4.2 * cm, 4.2 * cm)
    c.setFont("Courier-Bold", 20)
    c.drawString(5.1 * cm, 4.2 * cm, caja)
    c.setFont("Helvetica", 10)
    c.drawString(5.1 * cm, 3.3 * cm, anios)
    c.drawString(5.1 * cm, 2.6 * cm, serie[:26])
    c.drawString(5.1 * cm, 1.9 * cm, f"Estante {estante}")
    c.setFont("Helvetica", 6)
    c.drawString(5.1 * cm, 0.9 * cm, settings().institucion[:40])
    c.showPage()
    c.save()
    return buf.getvalue()
