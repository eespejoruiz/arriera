"""Modo microformas (adenda 02, sección 3): el lote sigue los pasos de la NTP 392.030-2 con responsable y rol por
paso, separación de funciones, control de 300 dpi, manifiesto con huellas y actas de apertura y cierre.

La conformidad legal la da el fedatario sobre una línea certificada; aquí se arma la evidencia del proceso.
"""

import hashlib
import io
import json
from datetime import UTC, datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.audit.cadena import registrar
from arriera.captura.almacen import almacen
from arriera.config import settings
from arriera.models import (
    Acta,
    ArchivoLote,
    Documento,
    Lote,
    Pagina,
    PaginaDocumento,
    PasoLote,
    TareaValidacion,
    User,
)

# (clave, nombre, roles que pueden registrarlo)
PASOS = [
    ("recepcion", "Recepción", ("archivero", "operador", "admin")),
    ("preparacion", "Preparación", ("archivero", "operador", "admin")),
    ("digitalizacion", "Digitalización", ("operador", "archivero", "admin")),
    ("control_calidad", "Control de calidad", ("archivero", "validador", "admin")),
    ("indizacion", "Indización", ("validador", "archivero", "admin")),
    ("grabacion", "Grabación y cierre", ("archivero", "admin")),
]
NOMBRES = {k: n for k, n, _ in PASOS}
# Separación de funciones: quien digitalizó no controla ni indiza su propio trabajo.
INCOMPATIBLES = {"control_calidad": "digitalizacion", "indizacion": "digitalizacion"}


class ErrorMicroformas(Exception):
    def __init__(self, mensaje: str, estado: int = 409):
        super().__init__(mensaje)
        self.mensaje, self.estado = mensaje, estado


def estado(db: Session, lote: Lote) -> dict:
    hechos = {p.step: p for p in db.scalars(select(PasoLote).where(PasoLote.batch_id == lote.id)).all()}
    usuarios = {
        u.id: u.name for u in db.scalars(select(User).where(User.id.in_([p.user_id for p in hechos.values()])))
    }
    siguiente = next((k for k, _, _ in PASOS if k not in hechos), None)
    actas = db.scalars(select(Acta).where(Acta.batch_id == lote.id).order_by(Acta.created_at)).all()
    bajos = db.scalar(
        select(func.count()).where(Pagina.batch_id == lote.id, Pagina.dpi.is_not(None), Pagina.dpi < 300)
    )
    return {
        "lote": lote.code,
        "microformas": lote.microformas,
        "pasos": [
            {
                "paso": k,
                "nombre": n,
                "roles": list(roles),
                "hecho": k in hechos,
                "por": usuarios.get(hechos[k].user_id) if k in hechos else None,
                "rol": hechos[k].role if k in hechos else None,
                "fecha": hechos[k].done_at if k in hechos else None,
            }
            for k, n, roles in PASOS
        ],
        "siguiente": siguiente,
        "paginas_bajo_300dpi": bajos,
        "hash_manifiesto": (lote.manifest or {}).get("microformas", {}).get("hash"),
        "actas": [{"id": str(a.id), "tipo": a.kind, "numero": a.number, "sha256": a.sha256} for a in actas],
    }


def registrar_paso(
    db: Session, lote: Lote, paso: str, u: User, roles: list[str], notas: str | None, ip=None
) -> dict:
    if not lote.microformas:
        raise ErrorMicroformas("Este lote no se creó en modo microformas.")
    claves = [k for k, _, _ in PASOS]
    if paso not in claves:
        raise ErrorMicroformas("Paso desconocido.", 404)
    hechos = {p.step: p for p in db.scalars(select(PasoLote).where(PasoLote.batch_id == lote.id)).all()}
    siguiente = next((k for k in claves if k not in hechos), None)
    if paso != siguiente:
        raise ErrorMicroformas(f"Corresponde registrar «{NOMBRES.get(siguiente or '', 'nada')}» antes.")
    permitidos = dict((k, r) for k, _, r in PASOS)[paso]
    rol = next((r for r in roles if r in permitidos), None)
    if rol is None:
        raise ErrorMicroformas(f"Tu rol no puede registrar «{NOMBRES[paso]}».", 403)
    previo = INCOMPATIBLES.get(paso)
    if previo and hechos[previo].user_id == u.id:
        raise ErrorMicroformas(
            f"Separación de funciones: quien hizo «{NOMBRES[previo]}» no puede registrar «{NOMBRES[paso]}».", 403
        )
    _requisitos(db, lote, paso)
    db.add(PasoLote(batch_id=lote.id, step=paso, user_id=u.id, role=rol, notes=(notas or None)))
    db.flush()
    if paso == "recepcion":
        _acta(db, lote, "apertura_lote", u, _pdf_apertura(db, lote, u, notas))
    if paso == "grabacion":
        manifiesto = _manifiesto(db, lote)
        crudo = json.dumps(manifiesto, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        h = hashlib.sha256(crudo).hexdigest()
        almacen().guardar(f"microformas/{lote.code}/manifiesto.json", crudo, "application/json")
        lote.manifest = {**(lote.manifest or {}), "microformas": {"hash": h, "fecha": manifiesto["generado"]}}
        _acta(db, lote, "cierre_lote", u, _pdf_cierre(db, lote, manifiesto, h), {"hash_manifiesto": h})
    registrar(
        db,
        "microformas.paso",
        user_id=u.id,
        object_type="batch",
        object_id=lote.code,
        ip=ip,
        details={"paso": paso, "rol": rol},
    )
    db.commit()
    return estado(db, lote)


def _requisitos(db: Session, lote: Lote, paso: str) -> None:
    pags = db.scalars(select(Pagina).where(Pagina.batch_id == lote.id)).all()
    if paso == "digitalizacion":
        if not pags:
            raise ErrorMicroformas("Todavía no hay páginas digitalizadas.")
        malas = [p.page_index for p in pags if p.qc_status in ("pendiente", "reescanear")]
        if malas:
            raise ErrorMicroformas(f"Hay páginas pendientes o por volver a escanear: {malas[:10]}.")
    if paso == "control_calidad":
        bajas = [p.page_index for p in pags if (p.dpi or 0) < 300 and p.qc_status != "en_blanco"]
        if bajas:
            raise ErrorMicroformas(f"Páginas por debajo de 300 dpi: {bajas[:10]}.")
    if paso == "indizacion":
        ia = (lote.manifest or {}).get("ia", {})
        if ia.get("estado") != "listo":
            raise ErrorMicroformas("La IA todavía no termina de indexar el lote. Ciérralo para que lo procese.")
        pendientes = db.scalar(
            select(func.count())
            .select_from(TareaValidacion)
            .join(Documento, Documento.id == TareaValidacion.document_id)
            .where(Documento.batch_id == lote.id, TareaValidacion.status == "pendiente")
        )
        if pendientes:
            raise ErrorMicroformas(f"Quedan {pendientes} datos por validar en este lote.")
    if paso == "grabacion" and lote.status != "cerrado":
        raise ErrorMicroformas("El lote debe estar cerrado.")


def _manifiesto(db: Session, lote: Lote) -> dict:
    pags = db.scalars(select(Pagina).where(Pagina.batch_id == lote.id).order_by(Pagina.page_index)).all()
    archivos = {a.id: a for a in db.scalars(select(ArchivoLote).where(ArchivoLote.batch_id == lote.id)).all()}
    docs = db.scalars(select(Documento).where(Documento.batch_id == lote.id).order_by(Documento.created_at)).all()
    pasos = db.scalars(select(PasoLote).where(PasoLote.batch_id == lote.id).order_by(PasoLote.done_at)).all()

    def h(clave):
        return hashlib.sha256(almacen().leer(clave)).hexdigest() if clave else None

    return {
        "version": 1,
        "institucion": settings().institucion,
        "lote": lote.code,
        "caja": lote.caja.code,
        "generado": datetime.now(UTC).isoformat(timespec="seconds"),
        "paginas": [
            {
                "indice": p.page_index,
                "sha256_original": archivos[p.batch_file_id].sha256,
                "sha256_imagen": h(p.image_key),
                "sha256_ocr": h(p.ocr_key),
                "dpi": p.dpi,
                "calidad": p.qc_status,
            }
            for p in pags
        ],
        "documentos": [
            {
                "id": str(d.id),
                "tipo": d.tipo.key,
                "estado": d.status,
                "paginas": [
                    i
                    for (i,) in db.execute(
                        select(Pagina.page_index)
                        .join(PaginaDocumento, PaginaDocumento.batch_page_id == Pagina.id)
                        .where(PaginaDocumento.document_id == d.id)
                        .order_by(PaginaDocumento.order)
                    ).all()
                ],
            }
            for d in docs
        ],
        "pasos": [
            {"paso": p.step, "usuario": str(p.user_id), "rol": p.role, "fecha": p.done_at.isoformat()}
            for p in pasos
        ],
    }


def _acta(db: Session, lote: Lote, tipo: str, u: User, pdf: bytes, payload: dict | None = None) -> Acta:
    n = db.scalar(select(func.count()).select_from(Acta).where(Acta.kind == tipo)) + 1
    numero = f"{'AP' if tipo == 'apertura_lote' else 'CI'}-{datetime.now(UTC):%Y}-{n:05d}"
    clave = f"actas/{numero}.pdf"
    almacen().guardar(clave, pdf, "application/pdf")
    a = Acta(
        kind=tipo,
        number=numero,
        batch_id=lote.id,
        pdf_key=clave,
        sha256=hashlib.sha256(pdf).hexdigest(),
        payload={"lote": lote.code, **(payload or {})},
        created_by=u.id,
    )
    db.add(a)
    db.flush()
    return a


def _lienzo(titulo: str):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(titulo)
    w, h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2.5 * cm, titulo)
    c.setFont("Helvetica", 10)
    c.drawString(
        2 * cm, h - 3.2 * cm, f"{settings().institucion} · Arriera · sistema de producción de microformas"
    )
    return buf, c, w, h


def _cerrar(buf, c, w) -> bytes:
    if settings().app_env != "production":
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w / 2, 1.2 * cm, "DATOS DEMO · NO VÁLIDO")
    c.setFont("Helvetica", 8)
    c.drawString(
        2 * cm,
        1.8 * cm,
        "Firma del fedatario: ______________________________   Firma del supervisor: ____________________",
    )
    c.showPage()
    c.save()
    return buf.getvalue()


def _lineas(c, x, y, filas: list[tuple[str, str]]) -> float:
    for k, v in filas:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, k)
        c.setFont("Helvetica", 10)
        c.drawString(x + 5.2 * cm, y, v[:80])
        y -= 0.6 * cm
    return y


def _pdf_apertura(db: Session, lote: Lote, u: User, notas: str | None) -> bytes:
    buf, c, w, h = _lienzo("ACTA DE APERTURA DE LOTE")
    _lineas(
        c,
        2 * cm,
        h - 4.6 * cm,
        [
            ("Lote", lote.code),
            (
                "Caja",
                f"{lote.caja.code} · {lote.caja.series_hint or 'sin serie'} · estante {lote.caja.shelf_location or '—'}",
            ),
            ("Fecha y hora", datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC")),
            ("Recibido por", u.name),
            ("Norma de referencia", "NTP 392.030-2:2015 · DL 681 · DL 827"),
            ("Observaciones", notas or "—"),
        ],
    )
    return _cerrar(buf, c, w)


def _pdf_cierre(db: Session, lote: Lote, m: dict, h: str) -> bytes:
    buf, c, w, alto = _lienzo("ACTA DE CIERRE DE LOTE")
    y = _lineas(
        c,
        2 * cm,
        alto - 4.6 * cm,
        [
            ("Lote", f"{lote.code} · caja {lote.caja.code}"),
            (
                "Páginas",
                f"{len(m['paginas'])} (resolución mínima {min((p['dpi'] or 0) for p in m['paginas'])} dpi)",
            ),
            ("Documentos", str(len(m["documentos"]))),
            ("Generado", m["generado"]),
        ],
    )
    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Pasos registrados")
    y -= 0.6 * cm
    usuarios = {str(u.id): u.name for u in db.scalars(select(User)).all()}
    for p in m["pasos"]:
        c.setFont("Helvetica", 9)
        c.drawString(
            2.4 * cm,
            y,
            f"{NOMBRES[p['paso']]} · {usuarios.get(p['usuario'], '—')} ({p['rol']}) · {p['fecha'][:16]}",
        )
        y -= 0.5 * cm
    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Huella SHA-256 del manifiesto")
    c.setFont("Courier", 8.5)
    c.drawString(2 * cm, y - 0.6 * cm, h)
    c.setFont("Helvetica", 8)
    c.drawString(
        2 * cm,
        y - 1.3 * cm,
        "El manifiesto lista la huella de cada imagen original, de la imagen de trabajo y del texto leído.",
    )
    return _cerrar(buf, c, w)
