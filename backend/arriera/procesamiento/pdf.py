"""PDF buscable (spec 7.8): imagen de cada página con la capa de texto invisible armada desde las cajas del OCR.

Se marca con el perfil PDF/A-2b (fuente incrustada, perfil de color sRGB y metadatos XMP). La conformidad formal
se valida con veraPDF antes de usarlo como microforma; aquí solo se arma.
"""

import io
from datetime import UTC, datetime
from pathlib import Path

import pikepdf
from PIL import Image, ImageCms
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FUENTES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
ANCHO_PT = 595.28  # ancho A4; el alto sigue la proporción de la imagen


def _fuente() -> str:
    if "ArrieraOCR" in pdfmetrics.getRegisteredFontNames():
        return "ArrieraOCR"
    for ruta in FUENTES:
        if Path(ruta).exists():
            pdfmetrics.registerFont(TTFont("ArrieraOCR", ruta))
            return "ArrieraOCR"
    return "Helvetica"


def pdf_buscable(paginas: list[tuple[bytes, dict | None]], titulo: str, autor: str = "Arriera") -> bytes:
    """`paginas`: (jpeg, resultado OCR como dict con 'palabras' normalizadas 0..1)."""
    fuente = _fuente()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setTitle(titulo)
    c.setAuthor(autor)
    c.setCreator("Arriera")
    for jpeg, ocr in paginas:
        with Image.open(io.BytesIO(jpeg)) as im:
            w, h = im.size
        ancho, alto = ANCHO_PT, ANCHO_PT * h / w
        c.setPageSize((ancho, alto))
        c.drawImage(ImageReader(io.BytesIO(jpeg)), 0, 0, ancho, alto)
        for p in (ocr or {}).get("palabras", []):
            texto = p["texto"]
            alto_caja = (p["y1"] - p["y0"]) * alto
            ancho_caja = (p["x1"] - p["x0"]) * ancho
            if alto_caja <= 0 or ancho_caja <= 0:
                continue
            tam = max(alto_caja * 0.9, 1)
            natural = pdfmetrics.stringWidth(texto, fuente, tam) or 1
            t = c.beginText()
            t.setTextRenderMode(3)  # invisible: se selecciona y se busca, no se ve
            t.setFont(fuente, tam)
            t.setHorizScale(100 * ancho_caja / natural)
            t.setTextOrigin(p["x0"] * ancho, alto - p["y1"] * alto + alto_caja * 0.15)
            t.textOut(texto)
            c.drawText(t)
        c.showPage()
    c.save()
    return _marcar_pdfa(buf.getvalue(), titulo, autor)


def _marcar_pdfa(datos: bytes, titulo: str, autor: str) -> bytes:
    pdf = pikepdf.open(io.BytesIO(datos))
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    perfil = pdf.make_stream(icc)
    perfil.N = 3
    pdf.Root.OutputIntents = pikepdf.Array(
        [
            pikepdf.Dictionary(
                Type=pikepdf.Name.OutputIntent,
                S=pikepdf.Name.GTS_PDFA1,
                OutputConditionIdentifier=pikepdf.String("sRGB"),
                DestOutputProfile=perfil,
            )
        ]
    )
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["pdfaid:part"] = "2"
        meta["pdfaid:conformance"] = "B"
        meta["dc:title"] = titulo
        meta["dc:creator"] = [autor]
        meta["xmp:CreateDate"] = datetime.now(UTC).isoformat(timespec="seconds")
        meta["xmp:CreatorTool"] = "Arriera"
    salida = io.BytesIO()
    pdf.save(salida, fix_metadata_version=True, deterministic_id=True)
    return salida.getvalue()
