"""Anthropic simulado para pruebas: responde como lo haría la IA, a partir del texto que recibe. Sin red."""

import json
import re

import httpx

TITULOS = ("solicitud de", "informe médico", "boleta de pago")


def _paginas_a_decidir(texto: str) -> list[tuple[int, str]]:
    parte = texto.split("Decide solo para estas páginas:", 1)[-1]
    bloques = re.split(r"=== Página (\d+) ===", parte)
    return [(int(bloques[i]), bloques[i + 1]) for i in range(1, len(bloques) - 1, 2)]


def _campo(orig, valor, conf, pagina=1):
    return {"valor_original": orig, "valor": valor, "confianza": conf, "pagina": pagina, "frase": orig}


def responder(herramienta: str, texto: str) -> dict:
    t = texto.lower()
    if herramienta == "separacion":
        salida = []
        for n, cuerpo in _paginas_a_decidir(texto):
            primera = cuerpo.split("\n", 2)[-1].strip().lower()
            empieza = any(primera.startswith(x) for x in TITULOS)
            salida.append({"pagina": n, "empieza_documento": empieza, "confianza": 0.95, "motivo": "título"})
        return {"paginas": salida}
    if herramienta == "clasificacion":
        doc = t.split("texto ocr del documento", 1)[-1]
        if "solicitud de subsidio" in doc:
            return {
                "tipo": "solicitud_subsidio",
                "confianza": 0.97,
                "evidencia": [{"frase": "Solicitud de subsidio", "pagina": 1}],
            }
        if "informe médico" in doc:
            return {
                "tipo": "informe_medico",
                "confianza": 0.96,
                "evidencia": [{"frase": "Informe médico", "pagina": 1}],
            }
        if "boleta de pago" in doc:
            return {
                "tipo": "boleta_pago",
                "confianza": 0.6,
                "evidencia": [{"frase": "Boleta de pago", "pagina": 1}],
            }
        return {"tipo": "otro", "confianza": 0.5, "evidencia": []}
    if herramienta == "extraccion":
        if "solicitud de subsidio" in texto.lower().split("campos:", 1)[0]:
            return {
                "campos": {
                    "nombre_titular": _campo("Rosa Huamán Quispe", "Rosa Huamán Quispe", 0.97),
                    "dni_titular": _campo("41234518", "41234518", 0.99),
                    "codigo_asociado": _campo(None, None, 0.0, None),
                    "fecha_solicitud": _campo("14 de marzo de 2018", "2018-03-14", 0.95),
                    "tipo_subsidio": _campo("enfermedad", "enfermedad", 0.96),
                    "monto_solicitado": _campo(
                        "mil doscientos cincuenta soles", "1250.00", 0.80
                    ),  # no está literal: no se corrobora
                    "numero_expediente": _campo("2018-0412", "2018-0412", 0.97),
                }
            }
        if "informe médico" in texto.lower().split("campos:", 1)[0]:
            return {
                "campos": {
                    "nombre_paciente": _campo("Rosa Huamán Quispe", "Rosa Huamán Quispe", 0.96),
                    "dni_paciente": _campo(None, None, 0.0, None),
                    "fecha_informe": _campo("10/03/2018", "2018-03-10", 0.95),
                    "establecimiento": _campo(None, None, 0.0, None),
                    "medico": _campo("Dra. L. Salas", "L. Salas", 0.92),
                    "cmp": _campo("00000", "00000", 0.97),
                    "diagnostico": _campo("lumbalgia mecánica", "lumbalgia mecánica", 0.9),
                    "cie10": _campo(None, None, 0.0, None),
                    "dias_descanso": _campo("siete", "7", 0.94),
                }
            }
        return {"campos": {}}
    raise AssertionError(herramienta)


def transporte(llamadas: list | None = None) -> httpx.MockTransport:
    def manejar(req: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(req.content)
        h = cuerpo["tool_choice"]["name"]
        if llamadas is not None:
            llamadas.append(h)
        datos = responder(h, cuerpo["messages"][0]["content"])
        return httpx.Response(
            200,
            json={
                "content": [{"type": "tool_use", "id": "t1", "name": h, "input": datos}],
                "usage": {"input_tokens": 1200, "output_tokens": 180},
            },
        )

    return httpx.MockTransport(manejar)
