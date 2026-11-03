"""Proveedores de OCR intercambiables (spec 7.5 y 7.11).

- Tesseract: local, sin costo. Se usa con DATOS DEMO y en el modo local. Multilenguaje con los paquetes instalados.
- Azure Document Intelligence `prebuilt-read`: con la cuenta y la llave del cliente. Detecta el idioma y el texto
  manuscrito.

Todas las coordenadas salen normalizadas de 0 a 1 respecto de la imagen, para resaltar en el visor y para la capa de
texto del PDF.
"""

import io
import re
import subprocess
import time
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Protocol

import httpx
from PIL import Image

from arriera.config import settings


@dataclass
class Palabra:
    texto: str
    x0: float
    y0: float
    x1: float
    y1: float
    conf: float | None = None


@dataclass
class ResultadoOCR:
    texto: str
    palabras: list[Palabra] = field(default_factory=list)
    confianza: float | None = None  # 0..1, promedio de palabras
    idioma: str | None = None  # ISO 639-1: es, en, pt...
    manuscrito: float | None = None  # proporción del texto que es manuscrito (si el proveedor lo informa)
    proveedor: str = ""
    modelo: str = ""
    costo_usd: float = 0.0

    def a_dict(self) -> dict:
        return asdict(self)


class ProveedorOCR(Protocol):
    nombre: str

    def analizar(self, imagen: bytes) -> ResultadoOCR: ...


class ErrorOCR(Exception):
    pass


# ---------------------------------------------------------------- idioma
_VACIAS = {
    "es": "de la que el en y a los se del las por un para con no una su al es lo como más o pero sus le ya fue",
    "en": "the of and to in is that for it as was with be by on not he this are or his from at which",
    "pt": "de a o que e do da em um para é com não uma os no se na por mais as dos como mas foi ao",
    "fr": "de la le et les des en un du une que est pour qui dans par sur pas au avec ce il sont",
    "it": "di e il la che in a per un del non è una sono le con da si gli al della come ma",
    "de": "der die und in den von zu das mit sich des auf für ist im dem nicht ein eine als auch",
}
_VACIAS_SETS = {k: set(v.split()) for k, v in _VACIAS.items()}


def detectar_idioma(texto: str) -> str | None:
    """Idioma por palabras vacías. Suficiente para facetas y para elegir el diccionario; Azure trae el suyo."""
    palabras = re.findall(r"[a-záéíóúüñçãõâêôàèìòùäöß]+", texto.lower())
    if len(palabras) < 4:
        return None
    cuenta = Counter()
    for p in palabras:
        for idioma, vacias in _VACIAS_SETS.items():
            if p in vacias:
                cuenta[idioma] += 1
    if not cuenta:
        return None
    idioma, n = cuenta.most_common(1)[0]
    return idioma if n >= 2 else None


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# ---------------------------------------------------------------- Tesseract
class OCRTesseract:
    nombre = "tesseract"

    def __init__(self, idiomas: str | None = None, binario: str = "tesseract"):
        self.idiomas = idiomas or settings().ocr_idiomas
        self.binario = binario

    def analizar(self, imagen: bytes) -> ResultadoOCR:
        with Image.open(io.BytesIO(imagen)) as im:
            ancho, alto = im.size
        try:
            r = subprocess.run(  # noqa: S603  (binario fijo, sin shell)
                [self.binario, "stdin", "stdout", "-l", self.idiomas, "--psm", "3", "tsv"],
                input=imagen,
                capture_output=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ErrorOCR(f"Tesseract no respondió: {e}") from e
        if r.returncode != 0:
            raise ErrorOCR(r.stderr.decode(errors="replace")[-400:])
        palabras: list[Palabra] = []
        lineas: dict[tuple, list[str]] = {}
        orden: list[tuple] = []
        for fila in r.stdout.decode("utf-8", errors="replace").splitlines()[1:]:
            c = fila.split("\t")
            if len(c) < 12 or c[0] != "5":
                continue
            txt = c[11].strip()
            conf = float(c[10])
            if not txt or conf < 0:
                continue
            x, y, w, h = (int(v) for v in c[6:10])
            palabras.append(
                Palabra(txt, x / ancho, y / alto, (x + w) / ancho, (y + h) / alto, round(conf / 100, 3))
            )
            clave = (c[1], c[2], c[3], c[4])  # página, bloque, párrafo, línea
            if clave not in lineas:
                lineas[clave] = []
                orden.append(clave)
            lineas[clave].append(txt)
        texto = "\n".join(" ".join(lineas[k]) for k in orden)
        confs = [p.conf for p in palabras if p.conf is not None]
        return ResultadoOCR(
            texto=texto,
            palabras=palabras,
            confianza=round(sum(confs) / len(confs), 3) if confs else None,
            idioma=detectar_idioma(texto),
            proveedor=self.nombre,
            modelo=f"tesseract:{self.idiomas}",
            costo_usd=0.0,
        )


# ---------------------------------------------------------------- Azure
class OCRAzure:
    """Azure AI Document Intelligence, modelo prebuilt-read, con la cuenta del cliente."""

    nombre = "azure"

    def __init__(self, endpoint: str | None = None, llave: str | None = None, transporte=None):
        c = settings()
        self.endpoint = (endpoint or c.azure_di_endpoint).rstrip("/")
        self.llave = llave or c.azure_di_key
        self.version = c.azure_di_version
        self.usd_pagina = c.azure_di_usd_mil / 1000
        if not self.endpoint or not self.llave:
            raise ErrorOCR("Falta configurar AZURE_DI_ENDPOINT y AZURE_DI_KEY (cuenta del cliente).")
        self.http = httpx.Client(timeout=60, transport=transporte)

    def analizar(self, imagen: bytes) -> ResultadoOCR:
        url = f"{self.endpoint}/documentintelligence/documentModels/prebuilt-read:analyze"
        cab = {"Ocp-Apim-Subscription-Key": self.llave}
        r = self.http.post(
            url,
            params={"api-version": self.version},
            content=imagen,
            headers={**cab, "Content-Type": "application/octet-stream"},
        )
        if r.status_code != 202:
            raise ErrorOCR(f"Azure respondió {r.status_code}: {r.text[:300]}")
        operacion = r.headers["Operation-Location"]
        for intento in range(60):
            res = self.http.get(operacion, headers=cab)
            datos = res.json()
            estado = datos.get("status")
            if estado == "succeeded":
                return self._convertir(datos["analyzeResult"])
            if estado == "failed":
                raise ErrorOCR(f"Azure no pudo leer la página: {datos.get('error')}")
            time.sleep(min(0.5 * (intento + 1), 3))
        raise ErrorOCR("Azure no terminó a tiempo.")

    def _convertir(self, ar: dict) -> ResultadoOCR:
        texto = ar.get("content", "")
        palabras: list[Palabra] = []
        for pag in ar.get("pages", [])[:1]:
            w, h = pag.get("width") or 1, pag.get("height") or 1
            for p in pag.get("words", []):
                pol = p.get("polygon") or []
                if len(pol) < 8:
                    continue
                xs, ys = pol[0::2], pol[1::2]
                palabras.append(
                    Palabra(p["content"], min(xs) / w, min(ys) / h, max(xs) / w, max(ys) / h, p.get("confidence"))
                )
        largo = max(len(texto), 1)
        por_idioma: Counter = Counter()
        for leng in ar.get("languages", []):
            por_idioma[leng["locale"].split("-")[0]] += sum(s["length"] for s in leng.get("spans", []))
        manuscrito = sum(
            s["length"] for st in ar.get("styles", []) if st.get("isHandwritten") for s in st.get("spans", [])
        )
        confs = [p.conf for p in palabras if p.conf is not None]
        return ResultadoOCR(
            texto=texto,
            palabras=palabras,
            confianza=round(sum(confs) / len(confs), 3) if confs else None,
            idioma=por_idioma.most_common(1)[0][0] if por_idioma else detectar_idioma(texto),
            manuscrito=round(manuscrito / largo, 3),
            proveedor=self.nombre,
            modelo=f"prebuilt-read:{self.version}",
            costo_usd=self.usd_pagina,
        )


def proveedor_ocr() -> ProveedorOCR | None:
    nombre = settings().ocr_proveedor
    if nombre == "tesseract":
        return OCRTesseract()
    if nombre == "azure":
        return OCRAzure()
    return None
