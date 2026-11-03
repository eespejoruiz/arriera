"""Pasos 5 a 8 del flujo (spec 7.6–7.8): separar el lote en documentos, clasificarlos, extraer sus campos,
validarlos localmente, vincular personas por DNI y crear las tareas de validación para lo dudoso."""

import re
import time
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from arriera.audit.cadena import registrar
from arriera.config import settings
from arriera.models import (
    Documento,
    Extraccion,
    Lote,
    Pagina,
    PaginaDocumento,
    PasoProceso,
    Persona,
    TareaValidacion,
    TipoDocumental,
)
from arriera.procesamiento import prompts
from arriera.procesamiento.normalizar import normalizar_valor, ubicar
from arriera.procesamiento.ocr import leer_resultado
from arriera.providers.llm import ErrorLLM, ProveedorLLM, proveedor_llm
from arriera.security.cifrado import cifrar, hmac_busqueda

VENTANA = 8
MAX_TEXTO = 12000
UMBRAL_CLASE = 0.85
UMBRAL_SEPARACION = 0.7


class PresupuestoAgotado(Exception):
    pass


# ------------------------------------------------------------------ presupuesto (spec 7.10)
def gasto_mes(db: Session) -> float:
    tz = ZoneInfo(settings().app_timezone)
    inicio = datetime.now(tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return float(
        db.scalar(
            select(func.coalesce(func.sum(PasoProceso.cost_usd), 0.0)).where(
                PasoProceso.provider == "anthropic", PasoProceso.created_at >= inicio
            )
        )
        or 0.0
    )


def _llamar(db: Session, llm: ProveedorLLM, paso: str, sujeto: str, *, mensaje: str, esquema: dict) -> dict:
    if gasto_mes(db) >= settings().ia_presupuesto_usd_mes:
        raise PresupuestoAgotado
    t0 = time.perf_counter()
    try:
        r = llm.json(sistema=prompts.SISTEMA, mensaje=mensaje, esquema=esquema, herramienta=paso)
    except ErrorLLM as e:
        db.add(
            PasoProceso(
                subject_type="document" if paso != "separacion" else "batch",
                subject_id=sujeto,
                step=paso,
                status="error",
                provider=llm.nombre,
                error=str(e)[:2000],
                duration_ms=int((time.perf_counter() - t0) * 1000),
                prompt_version=prompts.VERSION,
            )
        )
        db.commit()
        raise
    db.add(
        PasoProceso(
            subject_type="document" if paso != "separacion" else "batch",
            subject_id=sujeto,
            step=paso,
            status="ok",
            provider=r.proveedor,
            model=r.modelo,
            tokens_in=r.tokens_in,
            tokens_out=r.tokens_out,
            cost_usd=r.costo_usd,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            prompt_version=prompts.VERSION,
        )
    )
    return r.datos


# ------------------------------------------------------------------ separación (7.6)
def senales(texto: str) -> str:
    s = []
    if re.search(r"\b1\s*(de|/)\s*\d+\b", texto[:400], re.I):
        s.append("numeración «1 de N»")
    elif re.search(r"\b([2-9]|\d{2})\s*(de|/)\s*\d+\b", texto[:400], re.I):
        s.append("numeración de continuación")
    for linea in texto.splitlines()[:3]:
        if len(linea) > 6 and linea.upper() == linea and re.search(r"[A-ZÁÉÍÓÚÑ]{4}", linea):
            s.append(f"encabezado «{linea[:60]}»")
    if re.search(r"\b\d{8}\b", texto):
        s.append("aparece un número de 8 dígitos (posible DNI)")
    return "; ".join(s) or "ninguna"


def _resumen(p: Pagina) -> str:
    t = (p.ocr_text or "").strip()
    cuerpo = t if len(t) <= 700 else t[:500] + "\n[…]\n" + t[-200:]
    return f"=== Página {p.page_index} ===\nSeñales: {senales(t)}\n{cuerpo or '(sin texto)'}"


ESQ_SEPARACION = {
    "type": "object",
    "properties": {
        "paginas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pagina": {"type": "integer"},
                    "empieza_documento": {"type": "boolean"},
                    "confianza": {"type": "number"},
                    "motivo": {"type": "string"},
                },
                "required": ["pagina", "empieza_documento", "confianza", "motivo"],
            },
        }
    },
    "required": ["paginas"],
}


def separar(db: Session, llm: ProveedorLLM, lote: Lote, pags: list[Pagina]) -> list[list[tuple[Pagina, float]]]:
    """Devuelve los documentos como listas de (página, confianza de que ahí empieza o continúa)."""
    if len(pags) == 1:
        return [[(pags[0], 1.0)]]
    decision: dict[int, tuple[bool, float]] = {}
    for i in range(0, len(pags), VENTANA):
        ventana = pags[i : i + VENTANA]
        contexto = f"Página anterior (solo contexto):\n{_resumen(pags[i - 1])}\n\n" if i else ""
        datos = _llamar(
            db,
            llm,
            "separacion",
            lote.code,
            mensaje=prompts.SEPARACION.format(
                contexto=contexto, paginas="\n\n".join(_resumen(p) for p in ventana)
            ),
            esquema=ESQ_SEPARACION,
        )
        for d in datos.get("paginas", []):
            decision[int(d["pagina"])] = (bool(d["empieza_documento"]), float(d.get("confianza") or 0))
    docs: list[list[tuple[Pagina, float]]] = []
    for k, p in enumerate(pags):
        empieza, conf = decision.get(p.page_index, (False, 0.5))
        if k == 0 or empieza:
            docs.append([(p, 1.0 if k == 0 else conf)])
        else:
            docs[-1].append((p, conf))
    return docs


# ------------------------------------------------------------------ clasificación y extracción (7.7)
def _texto(pags: list[Pagina]) -> str:
    partes, total = [], 0
    for n, p in enumerate(pags, 1):
        t = f"[pág. {n}]\n{(p.ocr_text or '').strip()}"
        if total + len(t) > MAX_TEXTO:
            partes.append(t[: max(0, MAX_TEXTO - total)] + "\n[…]")
            break
        partes.append(t)
        total += len(t)
    return "\n\n".join(partes)


def clasificar(db: Session, llm: ProveedorLLM, tipos: list[TipoDocumental], pags: list[Pagina], sujeto: str):
    catalogo = "\n".join(f"- {t.key}: {t.name} · {t.signals}" for t in tipos)
    esquema = {
        "type": "object",
        "properties": {
            "tipo": {"type": "string", "enum": [t.key for t in tipos]},
            "confianza": {"type": "number"},
            "evidencia": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"frase": {"type": "string"}, "pagina": {"type": "integer"}},
                    "required": ["frase", "pagina"],
                },
            },
        },
        "required": ["tipo", "confianza", "evidencia"],
    }
    d = _llamar(
        db,
        llm,
        "clasificacion",
        sujeto,
        mensaje=prompts.CLASIFICACION.format(catalogo=catalogo, desde=1, hasta=len(pags), texto=_texto(pags)),
        esquema=esquema,
    )
    tipo = next((t for t in tipos if t.key == d.get("tipo")), None) or next(t for t in tipos if t.key == "otro")
    return tipo, float(d.get("confianza") or 0), (d.get("evidencia") or [])[:3]


def extraer(db: Session, llm: ProveedorLLM, tipo: TipoDocumental, pags: list[Pagina], sujeto: str) -> dict:
    campos = tipo.fields_schema.get("fields", [])
    if not campos:
        return {}
    nulo = lambda t: {"type": [t, "null"]}  # noqa: E731
    props = {
        c["key"]: {
            "type": "object",
            "properties": {
                "valor_original": nulo("string"),
                "valor": nulo("string"),
                "confianza": {"type": "number"},
                "pagina": nulo("integer"),
                "frase": nulo("string"),
            },
            "required": ["valor_original", "valor", "confianza", "pagina", "frase"],
        }
        for c in campos
    }
    lista = "\n".join(
        f"- {c['key']} ({c['nombre']}): {prompts.TIPOS_CAMPO.get(c['type'], c['type'])}"
        + (f" [{', '.join(c['options'])}]" if c.get("options") else "")
        for c in campos
    )
    d = _llamar(
        db,
        llm,
        "extraccion",
        sujeto,
        mensaje=prompts.EXTRACCION.format(tipo=tipo.name, campos=lista, texto=_texto(pags)),
        esquema={
            "type": "object",
            "properties": {"campos": {"type": "object", "properties": props, "required": list(props)}},
            "required": ["campos"],
        },
    )
    return d.get("campos") or {}


# ------------------------------------------------------------------ armado del documento
def _crear_documento(
    db: Session,
    lote: Lote,
    tipo: TipoDocumental,
    conf_tipo: float,
    evidencia: list,
    paginas: list[tuple[Pagina, float]],
    campos_ia: dict,
) -> Documento:
    pags = [p for p, _ in paginas]
    doc = Documento(
        batch_id=lote.id,
        document_type_id=tipo.id,
        title=tipo.name,
        sensitivity=tipo.sensitivity,
        type_confidence=round(conf_tipo, 3),
        evidence=evidencia,
    )
    db.add(doc)
    db.flush()
    for orden, (p, conf) in enumerate(paginas, 1):
        db.add(PaginaDocumento(document_id=doc.id, batch_page_id=p.id, order=orden, start_confidence=conf))
    tareas: list[TareaValidacion] = []
    confs, valores = [], {}
    for c in tipo.fields_schema.get("fields", []):
        ia = campos_ia.get(c["key"]) or {}
        original = ia.get("valor_original")
        norm, nota = normalizar_valor(c["type"], ia.get("valor") or original, c.get("options"))
        conf = float(ia.get("confianza") or 0)
        if nota:
            conf = min(conf, 0.5)
        pag_no = ia.get("pagina") if isinstance(ia.get("pagina"), int) and 1 <= ia["pagina"] <= len(pags) else None
        bbox = None
        if norm is not None:
            pagina_ref = pags[(pag_no or 1) - 1]
            palabras = (leer_resultado(pagina_ref) or {}).get("palabras", [])
            bbox = ubicar(palabras, original) or ubicar(palabras, norm)
            if bbox and pag_no is None:
                pag_no = 1
        if norm is None:
            estado = "pendiente" if c["required"] else "vacio"
            motivo = f"No se encontró «{c['nombre']}»" if c["required"] else None
        elif nota:
            estado, motivo = "pendiente", nota
        elif c["auto_accept"] > 1:
            estado, motivo = "pendiente", "Dato sensible: siempre lo revisa una persona"
        elif conf >= c["auto_accept"]:
            estado, motivo = "auto_aceptado", None
        else:
            estado, motivo = (
                "pendiente",
                f"Confianza {round(conf * 100)}% (umbral {round(c['auto_accept'] * 100)}%)",
            )
        ex = Extraccion(
            document_id=doc.id,
            field_key=c["key"],
            value_raw=original,
            value_norm=norm,
            confidence=round(conf, 3) if norm is not None else None,
            page_no=pag_no,
            evidence=(ia.get("frase") or None),
            bbox={"pagina": pag_no, **bbox} if bbox else None,
            note=nota,
            status=estado,
            prompt_version=prompts.VERSION,
        )
        db.add(ex)
        db.flush()
        valores[c["key"]] = (c, ex)
        if norm is not None and c["required"]:
            confs.append(conf)
        if estado == "pendiente":
            tareas.append(
                TareaValidacion(
                    kind="campo",
                    document_id=doc.id,
                    extraction_id=ex.id,
                    priority=1 if (c["required"] or c.get("sensitive")) else 2,
                    reason=motivo or "Revisar",
                )
            )
    # Título, fecha y persona
    nombre = next(
        (ex.value_norm for c, ex in valores.values() if c["type"] == "person_name" and ex.value_norm), None
    )
    doc.title = f"{tipo.name} · {nombre}" if nombre else tipo.name
    fecha = next((ex.value_norm for c, ex in valores.values() if c["type"] == "date" and ex.value_norm), None)
    doc.doc_date = date.fromisoformat(fecha) if fecha else None
    dni = next(
        (
            ex
            for c, ex in valores.values()
            if c["type"] == "dni" and ex.status == "auto_aceptado" and ex.value_norm
        ),
        None,
    )
    if dni is not None:
        doc.person_id = vincular_persona(db, dni.value_norm, nombre).id
    if conf_tipo < UMBRAL_CLASE or tipo.key == "otro":
        tareas.append(
            TareaValidacion(
                kind="clasificacion",
                document_id=doc.id,
                priority=1,
                reason=f"Tipo «{tipo.name}» con confianza {round(conf_tipo * 100)}%",
            )
        )
    dudosas = [p.page_index for p, conf in paginas[1:] if conf < UMBRAL_SEPARACION]
    if paginas[0][1] < UMBRAL_SEPARACION:
        dudosas.insert(0, paginas[0][0].page_index)
    if dudosas:
        tareas.append(
            TareaValidacion(
                kind="separacion",
                document_id=doc.id,
                priority=2,
                reason="Revisar dónde empieza o termina el documento (págs. " + ", ".join(map(str, dudosas)) + ")",
            )
        )
    for t in tareas:
        db.add(t)
    doc.ai_confidence = round(min([conf_tipo, *confs]), 3)
    doc.status = "por_validar" if tareas else "validado"
    db.flush()
    return doc


def vincular_persona(db: Session, dni: str, nombre: str | None) -> Persona:
    h = hmac_busqueda(dni)
    p = db.scalar(select(Persona).where(Persona.dni_hash == h))
    if p is None:
        p = Persona(dni_hash=h, full_name=nombre or "(sin nombre)", doc_type="DNI")
        db.add(p)
        db.flush()
        p.dni_enc = cifrar(dni, f"dni:{p.id}")
    elif nombre and p.full_name == "(sin nombre)":
        p.full_name = nombre
    return p


# ------------------------------------------------------------------ orquestación
def procesar_lote_ia(db: Session, lote_id, llm: ProveedorLLM | None = None) -> dict:
    """Separa, clasifica y extrae todo el lote. Guarda cada documento apenas termina (avance parcial seguro)."""
    lote = db.get(Lote, lote_id)
    assert lote is not None
    humano = db.scalar(
        select(func.count())
        .select_from(Extraccion)
        .join(Documento, Documento.id == Extraccion.document_id)
        .where(Documento.batch_id == lote.id, Extraccion.source == "human")
    )
    if humano:
        return _estado(db, lote, "con_validaciones", "Ya hay validaciones humanas; no se vuelve a procesar.")
    llm = llm or proveedor_llm()
    if llm is None:
        return _estado(db, lote, "sin_proveedor", "No hay proveedor de IA configurado.")
    pags = db.scalars(
        select(Pagina)
        .where(
            Pagina.batch_id == lote.id,
            Pagina.qc_status.in_(["ok", "corregida"]),
            Pagina.ocr_status.in_(["ok", "sin_texto"]),
        )
        .order_by(Pagina.page_index)
    ).all()
    if not pags:
        return _estado(db, lote, "sin_paginas", "No hay páginas legibles con texto.")
    db.execute(delete(Documento).where(Documento.batch_id == lote.id))
    _estado(db, lote, "procesando", None)
    db.commit()
    tipos = db.scalars(select(TipoDocumental).where(TipoDocumental.is_active.is_(True))).all()
    costo0 = gasto_mes(db)
    hechos = 0
    try:
        for grupo in separar(db, llm, lote, list(pags)):
            solo = [p for p, _ in grupo]
            sujeto = f"{lote.code}:{solo[0].page_index}"
            tipo, conf, evid = clasificar(db, llm, list(tipos), solo, sujeto)
            campos = extraer(db, llm, tipo, solo, sujeto)
            _crear_documento(db, lote, tipo, conf, evid, grupo, campos)
            hechos += 1
            db.commit()
    except PresupuestoAgotado:
        db.rollback()
        return _estado(db, lote, "pausado_presupuesto", "Se alcanzó el presupuesto mensual de IA.", hechos, costo0)
    except ErrorLLM as e:
        db.rollback()
        return _estado(db, lote, "error", str(e)[:300], hechos, costo0)
    registrar(
        db,
        "lote.ia_procesada",
        actor_type="system",
        object_type="batch",
        object_id=lote.code,
        details={"documentos": hechos, "version": prompts.VERSION},
    )
    return _estado(db, lote, "listo", None, hechos, costo0)


def _estado(db: Session, lote: Lote, estado: str, motivo: str | None, docs: int = 0, costo0: float = 0.0) -> dict:
    info = {
        "estado": estado,
        "motivo": motivo,
        "documentos": docs,
        "costo_usd": round(max(gasto_mes(db) - costo0, 0), 6) if costo0 or docs else 0.0,
        "version": prompts.VERSION,
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    lote.manifest = {**(lote.manifest or {}), "ia": info}
    db.commit()
    return info


def reextraer(db: Session, documento_id) -> Documento | None:
    """Tras corregir el tipo a mano: vuelve a extraer con el esquema del tipo nuevo (mismas páginas)."""
    d = db.get(Documento, documento_id)
    if d is None:
        return None
    lote = db.get(Lote, d.batch_id)
    llm = proveedor_llm()
    if lote is None or llm is None:
        return None
    filas = db.execute(
        select(Pagina, PaginaDocumento.start_confidence)
        .join(PaginaDocumento, PaginaDocumento.batch_page_id == Pagina.id)
        .where(PaginaDocumento.document_id == d.id)
        .order_by(PaginaDocumento.order)
    ).all()
    grupo = [(p, c if c is not None else 1.0) for p, c in filas]
    tipo = d.tipo
    try:
        campos = extraer(db, llm, tipo, [p for p, _ in grupo], f"{lote.code}:{grupo[0][0].page_index}")
    except (PresupuestoAgotado, ErrorLLM):
        db.rollback()
        return None
    db.delete(d)
    db.flush()
    nuevo = _crear_documento(db, lote, tipo, 1.0, [], grupo, campos)
    db.commit()
    return nuevo
