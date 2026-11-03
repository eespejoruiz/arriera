"""Validaciones locales después de la IA (spec 7.7): lo que la IA devuelve se revisa aquí antes de aceptarlo."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from arriera.config import settings
from arriera.providers.ocr import normalizar as sin_tildes


def normalizar_valor(
    tipo: str, valor: str | None, opciones: list[str] | None = None
) -> tuple[str | None, str | None]:
    """Devuelve (valor normalizado, nota). La nota explica por qué el dato no pasa la validación local."""
    if valor is None or not str(valor).strip():
        return None, None
    v = str(valor).strip()
    if tipo == "dni":
        d = re.sub(r"\D", "", v)
        return (d, None) if len(d) == 8 else (d or None, "El DNI no tiene 8 dígitos")
    if tipo == "date":
        f = _fecha(v)
        if f is None:
            return None, f"Fecha no reconocida: «{v}»"
        c = settings()
        if not c.archivo_desde <= f.year <= c.archivo_hasta + 1:
            return f.isoformat(), f"Fecha fuera del rango del archivo ({c.archivo_desde}–{c.archivo_hasta})"
        return f.isoformat(), None
    if tipo == "money_pen":
        limpio = re.sub(r"[^\d.,-]", "", v)
        if "," in limpio and "." in limpio:  # el último separador es el decimal: 1,250.00 o 1.250,00
            limpio = (
                limpio.replace(".", "").replace(",", ".")
                if limpio.rfind(",") > limpio.rfind(".")
                else limpio.replace(",", "")
            )
        elif "," in limpio and len(limpio.split(",")[-1]) == 2:
            limpio = limpio.replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
        try:
            m = Decimal(limpio)
        except InvalidOperation:
            return None, f"Monto no reconocido: «{v}»"
        return (f"{m:.2f}", None) if m > 0 else (f"{m:.2f}", "El monto no es positivo")
    if tipo == "integer":
        d = re.sub(r"[^\d-]", "", v)
        try:
            n = int(d)
        except ValueError:
            return None, f"Número no reconocido: «{v}»"
        return (str(n), None) if n >= 0 else (str(n), "El número es negativo")
    if tipo == "enum":
        o = sin_tildes(v)
        for op in opciones or []:
            if sin_tildes(op) == o:
                return op, None
        return v, "Valor fuera de las opciones"
    return re.sub(r"\s+", " ", v), None


def _fecha(v: str) -> date | None:
    v = v.strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", v)
    if m:
        a, mes, d = (int(x) for x in m.groups())
    else:
        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", v)
        if not m:
            return None
        d, mes, a = (int(x) for x in m.groups())
        if a < 100:
            a += 2000 if a <= (settings().archivo_hasta % 100) else 1900
    try:
        return date(a, mes, d)
    except ValueError:
        return None


def ubicar(palabras: list[dict], valor: str | None) -> dict | None:
    """Caja (0..1) que encierra el valor en la página, uniendo palabras consecutivas del OCR cuyo texto, sin
    tildes ni signos, forma el valor buscado («S/ 1,250.00» = «S/» + «1,250.00»). None si no aparece."""
    if not valor or not palabras:
        return None
    meta = re.sub(r"[^a-z0-9]", "", sin_tildes(valor))
    if len(meta) < 2:
        return None
    norm = [re.sub(r"[^a-z0-9]", "", sin_tildes(p["texto"])) for p in palabras]
    for i in range(len(norm)):
        if not norm[i] or not meta.startswith(norm[i][: len(meta)]):
            continue
        acum = ""
        for j in range(i, min(i + 12, len(norm))):
            acum += norm[j]
            if acum.startswith(meta) or acum == meta:
                cajas = [palabras[k] for k in range(i, j + 1) if norm[k]]
                return {
                    "x0": min(c["x0"] for c in cajas),
                    "y0": min(c["y0"] for c in cajas),
                    "x1": max(c["x1"] for c in cajas),
                    "y1": max(c["y1"] for c in cajas),
                }
            if not meta.startswith(acum):
                break
    return None
