"""Evaluación de la IA con un set de referencia DEMO (spec 7.9): documentos ficticios con sus respuestas correctas,
pasados por el mismo flujo de producción (OCR, separación, clasificación y extracción).

Uso:  python -m arriera.eval [--docs 12] [--semilla 7]
Genera un reporte HTML en el almacén (eval/AAAAMMDD-HHMM.html) e imprime el resumen. Las llamadas a la IA cuentan
contra el presupuesto mensual como cualquier otra.
"""

import argparse
import html
import io
import json
import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

from arriera.captura.almacen import almacen
from arriera.db import SessionLocal
from arriera.models import TipoDocumental
from arriera.procesamiento import documentos as proc
from arriera.procesamiento import prompts
from arriera.providers.llm import proveedor_llm
from arriera.providers.ocr import OCRTesseract

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
NOMBRES = ["Rosa", "Pedro", "Lucía", "Jorge", "Carmen", "Luis", "Ana", "Julio", "Elena", "Raúl", "Sofía", "Miguel"]
APELLIDOS = ["Huamán", "Quispe", "Mamani", "Flores", "Rojas", "Salas", "Torres", "Vargas", "Ramos", "Chávez"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre",
         "noviembre", "diciembre"]  # fmt: skip


@dataclass
class DocVerdad:
    tipo: str
    paginas: list[list[str]]
    campos: dict[str, str] = field(default_factory=dict)


@dataclass
class PaginaEval:  # lo mínimo que usan separar, clasificar y extraer
    page_index: int
    ocr_text: str
    palabras: list = field(default_factory=list)


def _fecha(r: random.Random) -> tuple[date, str]:
    f = date(2015, 1, 1) + timedelta(days=r.randint(0, 3650))
    texto = f"{f.day} de {MESES[f.month - 1]} de {f.year}" if r.random() < 0.5 else f"{f:%d/%m/%Y}"
    return f, texto


def _monto(r: random.Random, a: int, b: int) -> tuple[str, str]:
    m = r.randint(a, b) * 10 + r.choice([0, 50])
    return f"{m:.2f}", f"S/ {m:,.2f}"


def generar(r: random.Random) -> DocVerdad:
    nombre = f"{r.choice(NOMBRES)} {r.choice(APELLIDOS)} {r.choice(APELLIDOS)}"
    dni = f"{r.randint(10000000, 79999999)}"
    tipo = r.choice(["solicitud_subsidio", "informe_medico", "boleta_pago", "solicitud_prestamo"])
    f, ft = _fecha(r)
    if tipo == "solicitud_subsidio":
        m, mt = _monto(r, 30, 300)
        exp = f"{f.year}-{r.randint(1, 999):04d}"
        p1 = ["SOLICITUD DE SUBSIDIO POR ENFERMEDAD", f"Expediente {exp}", f"Asociado(a): {nombre}", f"DNI: {dni}",
              f"Fecha de la solicitud: {ft}", f"Monto solicitado: {mt}", "Motivo: descanso médico"]  # fmt: skip
        paginas = [p1]
        if r.random() < 0.6:
            paginas.append(["Página 2 de 2", "Declaro bajo juramento que los datos son verdaderos.",
                            "Firma del asociado(a)", "Sello de mesa de partes"])  # fmt: skip
        return DocVerdad(tipo, paginas, {"nombre_titular": nombre, "dni_titular": dni, "fecha_solicitud": f.isoformat(),
                                         "tipo_subsidio": "enfermedad", "monto_solicitado": m, "numero_expediente": exp})  # fmt: skip
    if tipo == "informe_medico":
        d = r.randint(2, 15)
        medico = f"{r.choice(NOMBRES)} {r.choice(APELLIDOS)}"
        cmp = str(r.randint(10000, 99999))
        return DocVerdad(tipo, [["INFORME MÉDICO", "Clínica Los Andes (ficticia)", f"Paciente: {nombre}",
                                 f"Fecha: {ft}", "Diagnóstico: lumbalgia mecánica",
                                 f"Se indica descanso médico por {d} días", f"Dr(a). {medico} · CMP {cmp}"]],
                         {"nombre_paciente": nombre, "fecha_informe": f.isoformat(), "dias_descanso": str(d),
                          "medico": medico, "cmp": cmp, "diagnostico": "Lumbalgia mecánica"})  # fmt: skip
    if tipo == "boleta_pago":
        neto, nt = _monto(r, 100, 600)
        return DocVerdad(tipo, [["BOLETA DE PAGO", "Empleador: Hospital Regional (ficticio)",
                                 f"Trabajador(a): {nombre} · DNI {dni}", f"Periodo: {MESES[f.month - 1]} {f.year}",
                                 f"Neto a pagar: {nt}"]],
                         {"nombre_trabajador": nombre, "dni_trabajador": dni, "periodo": f"{f.year}-{f.month:02d}",
                          "neto_pagar": neto})  # fmt: skip
    m, mt = _monto(r, 50, 1500)
    cuotas = r.choice([6, 12, 18, 24])
    return DocVerdad(tipo, [["SOLICITUD DE PRÉSTAMO", f"Asociado(a): {nombre}", f"DNI: {dni}", f"Fecha: {ft}",
                             f"Monto solicitado: {mt} en {cuotas} cuotas", "Firma del asociado(a)"]],
                     {"nombre_titular": nombre, "dni_titular": dni, "fecha_solicitud": f.isoformat(),
                      "monto_solicitado": m, "cuotas": str(cuotas)})  # fmt: skip


def dibujar(lineas: list[str]) -> bytes:
    img = Image.new("RGB", (2480, 3508), (246, 245, 238))  # A4 a 300 dpi
    d = ImageDraw.Draw(img)
    t, c = ImageFont.truetype(FUENTE, 84), ImageFont.truetype(FUENTE, 62)
    d.text((220, 260), lineas[0], font=t, fill=(25, 24, 22))
    y = 470
    for linea in lineas[1:]:
        d.text((220, y), linea, font=c, fill=(30, 29, 27))
        y += 118
    d.text((220, 3200), "DATOS DEMO · documento ficticio", font=c, fill=(160, 57, 42))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def _igual(tipo_campo: str, esperado: str, obtenido: str | None) -> bool:
    if obtenido is None:
        return False
    if tipo_campo in ("person_name", "string", "text"):
        from arriera.providers.ocr import normalizar

        return normalizar(esperado).replace(" ", "") == normalizar(obtenido).replace(" ", "")
    return esperado == obtenido


def evaluar(n_docs: int, semilla: int) -> dict:
    r = random.Random(semilla)  # noqa: S311  (datos ficticios, no criptografía)
    docs = [generar(r) for _ in range(n_docs)]
    ocr = OCRTesseract("spa")
    llm = proveedor_llm()
    if llm is None:
        raise SystemExit("Configura LLM_PROVEEDOR=anthropic para evaluar.")
    paginas: list[PaginaEval] = []
    inicios_verdad: set[int] = set()
    for dv in docs:
        for k, lineas in enumerate(dv.paginas):
            idx = len(paginas) + 1
            if k == 0:
                inicios_verdad.add(idx)
            res_ocr = ocr.analizar(dibujar(lineas))
            paginas.append(PaginaEval(idx, res_ocr.texto, [p.__dict__ for p in res_ocr.palabras]))
    with SessionLocal() as db:
        tipos = db.scalars(select(TipoDocumental).where(TipoDocumental.is_active.is_(True))).all()
        defs = {t.key: {c["key"]: c for c in t.fields_schema.get("fields", [])} for t in tipos}
        costo0 = proc.gasto_mes(db)
        lote_ficticio = type("L", (), {"code": f"EVAL-{semilla}"})()
        grupos = proc.separar(db, llm, lote_ficticio, paginas)
        inicios = {g[0][0].page_index for g in grupos}
        filas, clase_ok, auto_total, auto_ok, con_tareas, con_evitables = [], 0, 0, 0, 0, 0
        for g in grupos:
            pags = [p for p, _ in g]
            verdad = next(
                (
                    dv
                    for dv in docs
                    if pags[0].page_index in inicios_verdad and _inicio(docs, dv) == pags[0].page_index
                ),
                None,
            )
            tipo, conf, _ = proc.clasificar(db, llm, list(tipos), pags, f"eval:{pags[0].page_index}")
            campos = proc.extraer(db, llm, tipo, pags, f"eval:{pags[0].page_index}")
            db.commit()
            ok_tipo = verdad is not None and verdad.tipo == tipo.key
            clase_ok += ok_tipo
            tareas = evitables = conf < proc.UMBRAL_CLASE
            detalle = []
            for key, c in defs[tipo.key].items():
                ia = campos.get(key) or {}
                ev = proc.evaluar_campo(c, ia, len(pags), lambda n, pags=pags: pags[n - 1].palabras)
                norm, auto = ev["norm"], ev["estado"] == "auto_aceptado"
                esperado = verdad.campos.get(key) if (verdad and ok_tipo) else None
                correcto = esperado is not None and _igual(c["type"], esperado, norm)
                if esperado is not None and auto:
                    auto_total += 1
                    auto_ok += correcto
                if ev["estado"] == "pendiente":
                    tareas = True
                    if c["auto_accept"] <= 1:
                        evitables = True
                if esperado is not None or norm is not None:
                    detalle.append(
                        {"campo": key, "esperado": esperado, "obtenido": norm, "auto": auto, "ok": correcto}
                    )
            con_tareas += tareas
            con_evitables += evitables
            filas.append({"paginas": [p.page_index for p in pags], "esperado": verdad.tipo if verdad else "—",
                          "obtenido": tipo.key, "confianza": round(conf, 2), "campos": detalle})  # fmt: skip
        costo = proc.gasto_mes(db) - costo0
    vp = len((inicios & inicios_verdad) - {1})
    pred, real = len(inicios - {1}), len(inicios_verdad - {1})
    prec = vp / pred if pred else 1.0
    rec = vp / real if real else 1.0
    return {
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        "version_prompts": prompts.VERSION,
        "documentos": len(docs),
        "paginas": len(paginas),
        "separacion_f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0,
        "clasificacion": round(clase_ok / len(grupos), 3) if grupos else 0.0,
        "precision_autoaceptados": round(auto_ok / auto_total, 3) if auto_total else None,
        "campos_autoaceptados": auto_total,
        "documentos_con_validacion": round(con_tareas / len(grupos), 3) if grupos else 0.0,
        "documentos_con_validacion_sin_sensibles": round(con_evitables / len(grupos), 3) if grupos else 0.0,
        "costo_usd": round(costo, 5),
        "usd_por_mil_paginas": round(costo / len(paginas) * 1000, 2) if paginas else 0.0,
        "detalle": filas,
    }


def _inicio(docs: list[DocVerdad], dv: DocVerdad) -> int:
    n = 1
    for d in docs:
        if d is dv:
            return n
        n += len(d.paginas)
    return -1


def reporte_html(res: dict) -> str:
    metas = [("Separación (F1 de límites)", res["separacion_f1"], 0.95), ("Clasificación", res["clasificacion"], 0.95),
             ("Precisión de autoaceptados", res["precision_autoaceptados"], 0.98),
             ("Documentos que requieren validación", res["documentos_con_validacion"], None),
             ("… sin contar los datos sensibles que siempre revisa una persona", res["documentos_con_validacion_sin_sensibles"], None)]  # fmt: skip
    fila = lambda n, v, m: (  # noqa: E731
        f"<tr><td>{n}</td><td><b>{'—' if v is None else f'{v * 100:.1f}%'}</b></td>"
        f"<td>{'' if m is None else ('✔ meta ' if v is not None and v >= m else '✘ meta ') + f'{m * 100:.0f}%'}</td></tr>"
    )
    det = "".join(
        f"<tr><td>{f['paginas']}</td><td>{f['esperado']}</td><td>{f['obtenido']} ({f['confianza']})</td><td>"
        + "<br>".join(
            f"{'✔' if c['ok'] else '✘'} {html.escape(c['campo'])}: {html.escape(str(c['obtenido']))}"
            f"{'' if c['ok'] else ' · esperado ' + html.escape(str(c['esperado']))}{' · auto' if c['auto'] else ''}"
            for c in f["campos"]
        )
        + "</td></tr>"
        for f in res["detalle"]
    )
    return f"""<!doctype html><meta charset="utf-8"><title>Arriera · evaluación {res["fecha"]}</title>
<style>body{{font-family:system-ui;background:#0F110B;color:#F4F5EE;padding:24px}}td,th{{padding:6px 10px;
border-bottom:1px solid #333;vertical-align:top;font-size:14px}}table{{border-collapse:collapse;margin:16px 0}}
h1{{font-size:20px}}small{{color:#9a9c8f}}</style>
<h1>Evaluación de la IA · DATOS DEMO</h1><small>{res["fecha"]} · prompts {res["version_prompts"]} ·
{res["documentos"]} documentos · {res["paginas"]} páginas · US$ {res["costo_usd"]} (US$ {res["usd_por_mil_paginas"]} por mil)</small>
<table>{"".join(fila(*m) for m in metas)}</table>
<table><tr><th>Páginas</th><th>Tipo real</th><th>Tipo IA</th><th>Campos</th></tr>{det}</table>"""


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--docs", type=int, default=12)
    a.add_argument("--semilla", type=int, default=7)
    args = a.parse_args()
    res = evaluar(args.docs, args.semilla)
    clave = f"eval/{datetime.now(UTC):%Y%m%d-%H%M}.html"
    almacen().guardar(clave, reporte_html(res).encode(), "text/html")
    print(json.dumps({k: v for k, v in res.items() if k != "detalle"}, ensure_ascii=False, indent=2))
    print(f"Reporte: {clave}")


if __name__ == "__main__":
    main()
