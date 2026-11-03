"""Páginas sintéticas para pruebas (DATOS DEMO): formulario con líneas de texto y variantes de calidad."""

import io
import random

from PIL import Image, ImageDraw, ImageFilter


def pagina(variante: str = "ok", semilla: int = 1) -> bytes:
    rnd = random.Random(semilla)  # noqa: S311  (dibujo de prueba, no criptografía)
    w, h = 1240, 1754  # A4 a 150 dpi
    img = Image.new("RGB", (w, h), (246, 245, 238))
    if variante != "blanco":
        d = ImageDraw.Draw(img)
        d.rectangle([110, 120, w - 110, 150], fill=(30, 28, 24))  # membrete
        y = 230
        while y < h - 220:
            x = 110
            while x < w - 160:
                largo = rnd.randint(30, 120)
                d.rectangle([x, y, min(x + largo, w - 110), y + 16], fill=(35, 33, 30))
                x += largo + rnd.randint(14, 26)
            y += rnd.choice([42, 42, 42, 78])
        d.text((w // 2 - 80, h - 120), "DATOS DEMO", fill=(160, 57, 42))
    if variante == "inclinada":
        img = img.rotate(6, expand=True, fillcolor=(246, 245, 238))
    elif variante == "muy_inclinada":
        img = img.rotate(14, expand=True, fillcolor=(246, 245, 238))
    elif variante == "borrosa":
        img = img.filter(ImageFilter.GaussianBlur(7))
    elif variante == "cortada":
        img = img.crop((300, 0, w, h))
    elif variante == "foto_mesa":  # foto de celular: hoja sobre una mesa oscura
        mesa = Image.new("RGB", (w + 360, h + 420), (58, 46, 34))
        mesa.paste(img, (170, 220))
        img = mesa
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()
