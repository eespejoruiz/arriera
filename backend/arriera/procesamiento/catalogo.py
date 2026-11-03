"""Catálogo inicial de tipos documentales y estructura archivística (spec, anexos A y B).

Es la hipótesis para FAMENSSALUD y se confirma en el inventario. Cada tipo trae sus señales (para clasificar) y
el esquema de campos con su umbral de autoaceptación. Un umbral mayor a 1 significa «siempre lo valida una persona».
"""

from sqlalchemy import select
from sqlalchemy.orm import Session


def F(key: str, nombre: str, tipo: str, req: bool, auto: float, **extra) -> dict:  # noqa: N802
    return {"key": key, "nombre": nombre, "type": tipo, "required": req, "auto_accept": auto, **extra}


NOMBRE = lambda k="nombre_titular", n="Nombre del titular": F(k, n, "person_name", True, 0.95)  # noqa: E731
DNI = lambda k="dni_titular", req=True: F(k, "DNI", "dni", req, 0.97, pii=True)  # noqa: E731

# (código, nombre, nivel, padre)
NODOS = [
    ("FAM", "FAMENSSALUD", "fondo", None),
    ("ASO", "Asociados", "serie", "FAM"),
    ("ASO-INS", "Inscripción y afiliación", "subserie", "ASO"),
    ("APO", "Aportes", "serie", "FAM"),
    ("APO-DES", "Descuentos y aportes", "subserie", "APO"),
    ("BEN", "Beneficios", "serie", "FAM"),
    ("BEN-SUB", "Subsidio por enfermedad", "subserie", "BEN"),
    ("BEN-FAL", "Beneficio por fallecimiento", "subserie", "BEN"),
    ("PRE", "Préstamos", "serie", "FAM"),
    ("PRE-ASO", "Préstamos a asociados", "subserie", "PRE"),
    ("GOB", "Gobierno", "serie", "FAM"),
    ("GOB-ACT", "Actas y acuerdos", "subserie", "GOB"),
    ("ADM", "Administración y contabilidad", "serie", "FAM"),
    ("ADM-CON", "Contabilidad", "subserie", "ADM"),
    ("COR", "Correspondencia", "serie", "FAM"),
    ("COR-RYE", "Recibida y enviada", "subserie", "COR"),
]

# (clave, nombre, nodo, sensibilidad, señales, campos)
TIPOS = [
    (
        "solicitud_subsidio",
        "Solicitud de subsidio",
        "BEN-SUB",
        "N2",
        "Formulario dirigido al fondo pidiendo un subsidio por enfermedad o fallecimiento; datos del asociado, monto.",
        [
            NOMBRE(),
            DNI(),
            F("codigo_asociado", "Código de asociado", "string", False, 0.95),
            F("fecha_solicitud", "Fecha de solicitud", "date", True, 0.93),
            F(
                "tipo_subsidio",
                "Tipo de subsidio",
                "enum",
                True,
                0.93,
                options=["enfermedad", "fallecimiento", "otro"],
            ),
            F("monto_solicitado", "Monto solicitado", "money_pen", False, 0.90),
            F("numero_expediente", "N.º de expediente", "string", False, 0.95),
        ],
    ),
    (
        "informe_medico",
        "Informe médico",
        "BEN-SUB",
        "N3",
        "Informe de un médico o establecimiento de salud: paciente, diagnóstico, tratamiento, firma y CMP.",
        [
            NOMBRE("nombre_paciente", "Paciente"),
            DNI("dni_paciente", req=False),
            F("fecha_informe", "Fecha del informe", "date", True, 0.93),
            F("establecimiento", "Establecimiento", "string", False, 0.90),
            F("medico", "Médico", "person_name", False, 0.90),
            F("cmp", "CMP", "string", False, 0.95),
            F("diagnostico", "Diagnóstico", "text", False, 1.01, pii=True, sensitive=True),
            F("cie10", "CIE-10", "string", False, 0.95, sensitive=True),
            F("dias_descanso", "Días de descanso", "integer", False, 0.93),
        ],
    ),
    (
        "certificado_medico",
        "Certificado médico o CITT",
        "BEN-SUB",
        "N3",
        "Certificado de incapacidad temporal (CITT) o certificado médico con días de descanso.",
        [
            NOMBRE("nombre_paciente", "Paciente"),
            DNI("dni_paciente", req=False),
            F("fecha_emision", "Fecha de emisión", "date", True, 0.93),
            F("dias_descanso", "Días de descanso", "integer", False, 0.93),
            F("medico", "Médico", "person_name", False, 0.90),
            F("cmp", "CMP", "string", False, 0.95),
            F("diagnostico", "Diagnóstico", "text", False, 1.01, pii=True, sensitive=True),
        ],
    ),
    (
        "boleta_pago",
        "Boleta de pago",
        "APO-DES",
        "N2",
        "Boleta de remuneraciones de un empleador: periodo, ingresos, descuentos, neto a pagar.",
        [
            NOMBRE("nombre_trabajador", "Trabajador"),
            DNI("dni_trabajador"),
            F("periodo", "Periodo (AAAA-MM)", "string", True, 0.93),
            F("empleador", "Empleador", "string", False, 0.90),
            F("neto_pagar", "Neto a pagar", "money_pen", False, 0.90),
            F("descuento_fondo", "Descuento del fondo", "money_pen", False, 0.90),
        ],
    ),
    (
        "resolucion",
        "Resolución o aprobación",
        "BEN-SUB",
        "N2",
        "Resolución o carta de aprobación o denegación de un beneficio, con número y fecha.",
        [
            F("numero_resolucion", "N.º de resolución", "string", False, 0.95),
            F("fecha_resolucion", "Fecha", "date", True, 0.93),
            NOMBRE("nombre_beneficiario", "Beneficiario"),
            DNI("dni_beneficiario", req=False),
            F("decision", "Decisión", "enum", True, 0.93, options=["aprobado", "denegado", "otro"]),
            F("monto_aprobado", "Monto aprobado", "money_pen", False, 0.90),
        ],
    ),
    (
        "solicitud_prestamo",
        "Solicitud de préstamo",
        "PRE-ASO",
        "N2",
        "Solicitud de préstamo de un asociado: monto, número de cuotas, garantías.",
        [
            NOMBRE(),
            DNI(),
            F("fecha_solicitud", "Fecha de solicitud", "date", True, 0.93),
            F("monto_solicitado", "Monto solicitado", "money_pen", True, 0.90),
            F("cuotas", "Cuotas", "integer", False, 0.93),
            F("numero_expediente", "N.º de expediente", "string", False, 0.95),
        ],
    ),
    (
        "ficha_inscripcion",
        "Ficha de inscripción",
        "ASO-INS",
        "N2",
        "Ficha de afiliación o inscripción de un nuevo asociado con sus datos personales y laborales.",
        [
            NOMBRE("nombre_asociado", "Asociado"),
            DNI("dni_asociado"),
            F("fecha_inscripcion", "Fecha de inscripción", "date", True, 0.93),
            F("codigo_asociado", "Código de asociado", "string", False, 0.95),
            F("centro_laboral", "Centro laboral", "string", False, 0.90),
        ],
    ),
    (
        "copia_dni",
        "Copia de documento de identidad",
        "ASO-INS",
        "N2",
        "Fotocopia del DNI o carné de extranjería.",
        [
            NOMBRE("nombre", "Nombre"),
            DNI("dni"),
            F("fecha_nacimiento", "Fecha de nacimiento", "date", False, 0.95, pii=True),
        ],
    ),
    (
        "acta",
        "Acta de asamblea o consejo",
        "GOB-ACT",
        "N1",
        "Acta de asamblea general o de consejo directivo, con acuerdos y firmas.",
        [
            F("tipo_acta", "Tipo de acta", "enum", True, 0.93, options=["asamblea", "consejo", "otro"]),
            F("fecha_acta", "Fecha", "date", True, 0.93),
            F("numero_acta", "N.º de acta", "string", False, 0.95),
        ],
    ),
    (
        "comprobante_pago",
        "Comprobante de pago",
        "ADM-CON",
        "N1",
        "Factura, boleta de venta, recibo por honorarios o comprobante de egreso.",
        [
            F("emisor", "Emisor", "string", True, 0.90),
            F("ruc_emisor", "RUC", "string", False, 0.97),
            F("numero_comprobante", "N.º de comprobante", "string", False, 0.95),
            F("fecha_emision", "Fecha", "date", True, 0.93),
            F("monto_total", "Monto total", "money_pen", True, 0.90),
        ],
    ),
    (
        "carta",
        "Carta u oficio",
        "COR-RYE",
        "N2",
        "Carta, oficio o memorando recibido o enviado.",
        [
            F("remitente", "Remitente", "string", True, 0.90),
            F("destinatario", "Destinatario", "string", False, 0.90),
            F("fecha_carta", "Fecha", "date", True, 0.93),
            F("asunto", "Asunto", "text", False, 0.90),
        ],
    ),
    ("otro", "Otro documento", "FAM", "N2", "Ninguno de los tipos anteriores.", []),
]


def sembrar_catalogo(db: Session) -> int:
    """Crea los nodos y tipos que falten. Idempotente; no pisa los cambios hechos en el sistema."""
    from arriera.models import NodoClasificacion, TipoDocumental

    nodos = {n.code: n for n in db.scalars(select(NodoClasificacion)).all()}
    for orden, (code, nombre, nivel, padre) in enumerate(NODOS):
        if code not in nodos:
            nodos[code] = NodoClasificacion(
                code=code, name=nombre, level=nivel, parent_id=nodos[padre].id if padre else None, sort_order=orden
            )
            db.add(nodos[code])
            db.flush()
    creados = 0
    existentes = {t.key for t in db.scalars(select(TipoDocumental)).all()}
    for key, nombre, nodo, sens, senales, campos in TIPOS:
        if key in existentes:
            continue
        db.add(
            TipoDocumental(
                key=key,
                name=nombre,
                classification_node_id=nodos[nodo].id,
                sensitivity=sens,
                signals=senales,
                fields_schema={"fields": campos},
            )
        )
        creados += 1
    db.flush()
    return creados
