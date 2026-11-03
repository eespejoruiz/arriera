"""Proveedor de IA de lenguaje (spec 7.11). Salida siempre estructurada (herramienta forzada con JSON Schema).
Los modelos 5.5 ya no aceptan `temperature`; el determinismo viene del esquema y del prompt. Cada llamada devuelve tokens y costo para el registro de pasos y el presupuesto."""

import time
from dataclasses import dataclass
from typing import Protocol

import httpx

from arriera.config import settings

# US$ por millón de tokens (entrada, salida), tramo de prompts de hasta 100K tokens. Verificar el precio vigente.
PRECIOS = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}


@dataclass
class RespuestaLLM:
    datos: dict
    modelo: str
    tokens_in: int
    tokens_out: int
    costo_usd: float
    proveedor: str = "anthropic"


class ErrorLLM(Exception):
    pass


class ProveedorLLM(Protocol):
    nombre: str

    def json(
        self, *, sistema: str, mensaje: str, esquema: dict, herramienta: str, modelo: str | None = None
    ) -> RespuestaLLM: ...


def costo(modelo: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRECIOS.get(modelo, (2.00, 10.00))  # modelo desconocido: se asume el más caro de la tabla
    return round(tokens_in / 1e6 * pin + tokens_out / 1e6 * pout, 6)


class LLMAnthropic:
    nombre = "anthropic"
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, llave: str | None = None, transporte=None):
        self.llave = llave or settings().anthropic_api_key
        if not self.llave:
            raise ErrorLLM("Falta configurar ANTHROPIC_API_KEY.")
        self.http = httpx.Client(timeout=90, transport=transporte)

    def json(
        self, *, sistema: str, mensaje: str, esquema: dict, herramienta: str, modelo: str | None = None
    ) -> RespuestaLLM:
        modelo = modelo or settings().llm_modelo
        cuerpo = {
            "model": modelo,
            "max_tokens": 4000,
            "system": sistema,
            "messages": [{"role": "user", "content": mensaje}],
            "tools": [{"name": herramienta, "description": "Devuelve el resultado.", "input_schema": esquema}],
            "tool_choice": {"type": "tool", "name": herramienta},
        }
        cab = {"x-api-key": self.llave, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        ultimo = ""
        for intento in range(4):
            try:
                r = self.http.post(self.URL, json=cuerpo, headers=cab)
            except httpx.HTTPError as e:
                ultimo = str(e)
            else:
                if r.status_code == 200:
                    d = r.json()
                    bloque = next((b for b in d.get("content", []) if b.get("type") == "tool_use"), None)
                    if bloque is None:
                        raise ErrorLLM("La IA no devolvió el resultado estructurado.")
                    u = d.get("usage", {})
                    tin, tout = u.get("input_tokens", 0), u.get("output_tokens", 0)
                    return RespuestaLLM(bloque["input"], modelo, tin, tout, costo(modelo, tin, tout))
                ultimo = f"{r.status_code}: {r.text[:300]}"
                if r.status_code not in (408, 429, 500, 502, 503, 529):
                    break
            time.sleep(2**intento)
        raise ErrorLLM(f"Anthropic no respondió: {ultimo}")


def proveedor_llm() -> ProveedorLLM | None:
    if settings().llm_proveedor == "anthropic":
        return LLMAnthropic()
    return None
