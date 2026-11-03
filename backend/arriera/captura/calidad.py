"""Control de calidad local de cada página (sin IA externa): en blanco, borrosa, inclinada o cortada.

Usa solo numpy y Pillow para que la imagen del servidor sea liviana.
"""

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

UMBRAL_TINTA_BLANCO = 0.004  # proporción de píxeles con tinta
UMBRAL_BORROSO = 45.0  # varianza del laplaciano (sobre 1000 px de ancho)
INCLINACION_CORREGIR = 3.0  # grados
INCLINACION_RECHAZAR = 10.0
BORDE_TINTA_CORTADA = 0.18


@dataclass
class ResultadoCalidad:
    estado: str  # ok | corregida | reescanear | en_blanco
    motivo: str | None
    tinta: float
    borrosidad: float
    inclinacion: float
    imagen: Image.Image  # ya corregida si hizo falta


def _gris(img: Image.Image, ancho: int) -> np.ndarray:
    g = ImageOps.grayscale(img)
    if g.width > ancho:
        g = g.resize((ancho, max(1, round(g.height * ancho / g.width))), Image.Resampling.BILINEAR)
    return np.asarray(g, dtype=np.float32)


def _laplaciano_var(a: np.ndarray) -> float:
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def _tinta(a: np.ndarray) -> np.ndarray:
    # Umbral adaptado al fondo: tinta = bastante más oscuro que el papel.
    fondo = np.percentile(a, 90)
    return a < min(fondo - 60, 170)


def _inclinacion(tinta: np.ndarray) -> float:
    """Ángulo por perfil de proyección: el que deja las líneas de texto más «nítidas» en filas."""
    img = Image.fromarray((tinta * 255).astype(np.uint8))
    mejor, mejor_puntaje = 0.0, -1.0
    for paso, rango, centro in ((1.0, 15, 0.0), (0.25, 1.0, None)):
        c = mejor if centro is None else centro
        for ang in np.arange(c - rango, c + rango + 1e-9, paso):
            filas = np.asarray(img.rotate(float(ang), resample=Image.Resampling.NEAREST, fillcolor=0)).sum(axis=1)
            puntaje = float(np.var(filas))
            if puntaje > mejor_puntaje:
                mejor, mejor_puntaje = float(ang), puntaje
    return -mejor  # grados que el documento está girado


def recortar_papel(img: Image.Image) -> Image.Image:
    """En fotos de celular, recorta la hoja (zona clara) y descarta la mesa o el fondo alrededor."""
    a = _gris(img, 600)
    claro = a > max(np.percentile(a, 70) - 45, 120)
    filas = np.where(claro.mean(axis=1) > 0.45)[0]
    cols = np.where(claro.mean(axis=0) > 0.45)[0]
    if len(filas) < 10 or len(cols) < 10:
        return img
    esc = img.width / a.shape[1]
    y0, y1, x0, x1 = filas[0], filas[-1] + 1, cols[0], cols[-1] + 1
    area = (y1 - y0) * (x1 - x0) / (a.shape[0] * a.shape[1])
    if area > 0.97 or area < 0.25:
        return img  # ya es solo la hoja, o no se reconoce una hoja
    m = 2  # pequeño margen hacia adentro para no arrastrar sombra del borde
    caja = (int((x0 + m) * esc), int((y0 + m) * esc), int((x1 - m) * esc), int((y1 - m) * esc))
    return img.crop(caja)


def evaluar(datos: bytes) -> ResultadoCalidad:
    img = recortar_papel(ImageOps.exif_transpose(Image.open(io.BytesIO(datos))).convert("RGB"))
    a = _gris(img, 1000)
    tinta = _tinta(a)
    prop = float(tinta.mean())
    blur = _laplaciano_var(a)
    if prop < UMBRAL_TINTA_BLANCO:
        return ResultadoCalidad("en_blanco", "Página en blanco", prop, blur, 0.0, img)

    inc = _inclinacion(_tinta(_gris(img, 500)))
    h, w = tinta.shape
    m = max(2, round(min(h, w) * 0.02))
    borde = max(tinta[:m].mean(), tinta[-m:].mean(), tinta[:, :m].mean(), tinta[:, -m:].mean())

    motivos = []
    if blur < UMBRAL_BORROSO:
        motivos.append("Borrosa")
    if abs(inc) > INCLINACION_RECHAZAR:
        motivos.append(f"Torcida {abs(inc):.0f}°")
    if borde > BORDE_TINTA_CORTADA:
        motivos.append("Cortada en el borde")
    if motivos:
        return ResultadoCalidad("reescanear", " · ".join(motivos), prop, blur, inc, img)
    if abs(inc) > INCLINACION_CORREGIR:
        corregida = img.rotate(-inc, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        return ResultadoCalidad("corregida", f"Enderezada {abs(inc):.1f}°", prop, blur, inc, corregida)
    return ResultadoCalidad("ok", None, prop, blur, inc, img)


def a_jpeg(img: Image.Image, max_lado: int = 2400, calidad: int = 85) -> bytes:
    im = img.copy()
    im.thumbnail((max_lado, max_lado), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=calidad, optimize=True)
    return buf.getvalue()


def miniatura(img: Image.Image, lado: int = 360) -> bytes:
    im = img.copy()
    im.thumbnail((lado, lado), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=72)
    return buf.getvalue()
