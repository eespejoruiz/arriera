"""Secuencias de correo de Arriera para la base de prospectos (nov-2026). Una por sector, 3 correos cada una.

Estrategia común (probada en venta B2B en frío):
  Correo 1 · PAS (problema, agitación, solución) con un dolor específico del sector + oferta de bajo riesgo
             (reciprocidad: demo con 20 páginas de su propio archivo, sin costo) + CTA de un solo paso.
  Correo 2 · Antes / después (contraste concreto) + manejo de la objeción principal (seguridad y datos
             sensibles) + autoridad (Ley 29733, servidor propio, auditoría) + recordatorio de la oferta.
  Correo 3 · Aversión a la pérdida (costo de no hacer nada) + cierre «break-up» con micro-compromiso:
             responder 1, 2 o 3.
Ley 28493: el asunto lleva «PUBLICIDAD», el remitente se identifica y hay forma de darse de baja.
Variables: {{saludo}} y {{organizacion}} son campos personalizados del contacto; {{unsubscribe_url}} la pone Boost.
"""

WA = "https://wa.me/51913527489?text=Hola%20Enrique%2C%20quiero%20agendar%20la%20demo%20de%20Arriera"

OFERTA = ("Le propongo una demo de 20 minutos con <b>20 páginas de su propio archivo, sin costo</b>. "
          "Usted elige las páginas (puede ser una muestra sin datos sensibles) y al terminar se borran.")


def boton(texto):
    return (f'<p style="margin:22px 0"><a href="{WA}" style="background:#1B1F13;color:#F4F5EE;text-decoration:none;'
            f'padding:12px 20px;border-radius:999px;font-weight:bold;display:inline-block">{texto}</a></p>')


FIRMA = """<p style="margin:26px 0 0">Enrique Espejo<br>Arriera · gestión documental con IA<br>
WhatsApp +51 913 527 489 · <a href="https://arriera.tech" style="color:#5D6650">arriera.tech</a></p>
<p style="margin:26px 0 0;font-size:12px;color:#8A8F80">Arriera es una marca de Anomaly LA S.A.C., Lima, Perú.
Le escribo porque esta dirección figura como contacto público de {{organizacion}}. Si no desea recibir más correos,
<a href="{{unsubscribe_url}}" style="color:#8A8F80">dese de baja aquí</a> o responda «BAJA».</p>"""


def html(preheader, cuerpo):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">{preheader}</div>
<div style="max-width:580px;padding:24px 20px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#1F2318">
{cuerpo}
{FIRMA}
</div></body></html>"""


def p(t):
    return f'<p style="margin:0 0 14px">{t}</p>'


def lista(items):
    lis = "".join(f'<li style="margin:0 0 8px"><b>Antes:</b> {a}<br><b>Con Arriera:</b> {b}</li>' for a, b in items)
    return f'<ul style="margin:0 0 16px;padding-left:20px">{lis}</ul>'


def cierre_3(perdida):
    return (p("{{saludo}}:")
            + p("No quiero llenar su bandeja, así que este es mi último correo sobre este tema.")
            + p(perdida)
            + p("Si le sirve, respóndame solo con un número:")
            + '<p style="margin:0 0 14px">1 — Sí, agendemos la demo con 20 páginas de nuestro archivo.<br>'
              "2 — Ahora no, escríbame en tres meses.<br>3 — No es un tema para nosotros.</p>"
            + p("Con un «1» le escribo hoy mismo por WhatsApp para fijar la hora."))


SECTORES = {
    "fondos": {
        "nombre": "Fondos, mutuales y cooperativas",
        "segmento": "Fondos de ayuda mutua, mutualidades, derramas y cooperativas de ahorro y crédito",
        "c1": {
            "asuntos": ["PUBLICIDAD | El expediente de un asociado, en segundos",
                        "PUBLICIDAD | ¿Cuánto tarda en armar un expediente de 2018?"],
            "pre": "Sin tipear una sola hoja: la IA lo indexa por usted.",
            "cuerpo": p("{{saludo}}:")
            + p("Cuando un asociado de {{organizacion}} pide un beneficio, alguien tiene que juntar su solicitud, el informe y la boleta, caja por caja. Si el expediente es de hace cinco años, eso puede tomar una mañana entera.")
            + p("<b>Arriera</b> digitaliza ese archivo y su inteligencia artificial lee cada hoja: nombre, DNI, fechas y montos quedan indexados sin tipear. Desde ahí, el expediente completo de cualquier asociado aparece en segundos, y el sistema avisa si a un trámite le falta un requisito antes de pagar.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Antes y después de una caja de archivo",
                        "PUBLICIDAD | Lo que ve su equipo el primer día"],
            "pre": "Tres cambios concretos y una respuesta sobre los datos de salud.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en un fondo como {{organizacion}}:")
            + lista([("se busca por año y apellido, caja por caja.", "escribe un DNI o un nombre y abre la página exacta."),
                     ("alguien tipea cada hoja para indexarla.", "la IA llena la ficha y su equipo solo confirma lo dudoso."),
                     ("el archivo depende de la memoria de una persona.", "cada consulta queda registrada: quién vio qué y cuándo.")])
            + p("Y lo que más suele preocupar: los datos de salud de los asociados. Arriera se instala en un servidor a nombre de su institución, cifra los datos sensibles y trae el panel de accesos que pide la Ley 29733 para el Oficial de Datos Personales.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada mes que el archivo sigue en cajas, crecen la pila y el tiempo de búsqueda. Y el día que falta la persona que sabe dónde está todo, una consulta simple de un asociado se vuelve un problema."),
        },
    },
    "notarias": {
        "nombre": "Notarías",
        "segmento": "Notarías de Lima y provincias",
        "c1": {
            "asuntos": ["PUBLICIDAD | Un testimonio sin número de kardex",
                        "PUBLICIDAD | Su protocolo, buscable por nombre o DNI"],
            "pre": "Encontrar una escritura por DNI en segundos.",
            "cuerpo": p("{{saludo}}:")
            + p("Cuando alguien pide un testimonio en {{organizacion}} y no trae el número de kardex, empieza la búsqueda por DNI, por año, por tomo. Y el protocolo crece cada año.")
            + p("<b>Arriera</b> digitaliza el archivo notarial y su inteligencia artificial lee cada hoja: otorgantes, DNI, fecha y tipo de acto quedan indexados. Encontrar una escritura por nombre o DNI toma segundos, y cada copia emitida queda registrada con quién la pidió. El flujo está listo para microformas, si luego deciden dar valor legal a las copias digitales.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Del tomo a la pantalla en segundos",
                        "PUBLICIDAD | Así se ve una copia certificada con Arriera"],
            "pre": "Tres cambios para el archivo notarial.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en {{organizacion}}:")
            + lista([("sin número de kardex, la búsqueda va tomo por tomo.", "busca por nombre, DNI o fecha del acto en todo el protocolo."),
                     ("cada copia se busca, se fotocopia y se registra a mano.", "la copia sale en PDF con número de solicitud y queda registrada."),
                     ("el orden del archivo depende de una o dos personas.", "una auditoría que nadie puede alterar dice quién consultó qué.")])
            + p("Todo vive en un servidor a nombre de la notaría, con permisos por persona. Y si más adelante quieren microformas, el sistema ya sigue los pasos de la NTP 392.030-2.")
            + p("La demo con 20 páginas de su protocolo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su protocolo"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada año suma tomos al archivo y minutos a cada pedido de copia. Y cuando un usuario espera un testimonio, esos minutos se notan en el mostrador."),
        },
    },
    "salud": {
        "nombre": "Clínicas y laboratorios",
        "segmento": "Clínicas, hospitales privados, policlínicos, laboratorios y centros de diagnóstico",
        "c1": {
            "asuntos": ["PUBLICIDAD | La copia de una historia clínica, en minutos",
                        "PUBLICIDAD | 5 días hábiles para una copia de historia"],
            "pre": "Sin fotocopias, con el diagnóstico protegido.",
            "cuerpo": p("{{saludo}}:")
            + p("En muchas clínicas, la copia de una historia clínica toma cinco días hábiles: alguien la busca en el archivo, la fotocopia y se cobra por hoja. Revisamos las webs de 58 clínicas y laboratorios privados del Perú y ninguna menciona una historia clínica electrónica.")
            + p("<b>Arriera</b> digitaliza las historias en papel de {{organizacion}} y su inteligencia artificial lee cada hoja: paciente, DNI, fechas y tipo de documento quedan indexados. La copia que pide un paciente sale en PDF en minutos, con constancia de entrega y lo sensible oculto cuando corresponde.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Historias en papel, datos protegidos",
                        "PUBLICIDAD | Antes y después del archivo de historias"],
            "pre": "Tres cambios y lo que pide la Ley 29733.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en {{organizacion}}:")
            + lista([("la historia se busca en estantes por número o apellido.", "escribe el nombre o el DNI y abre la página exacta."),
                     ("la copia toma días y se fotocopia hoja por hoja.", "sale en PDF en minutos, con plazo y entrega registrados."),
                     ("no hay registro de quién consultó una historia.", "cada acceso a un dato de salud queda en un panel para el Oficial de Datos Personales.")])
            + p("Los datos de salud son sensibles: por eso Arriera se instala en un servidor a nombre de la clínica, cifra esos datos y cumple lo que pide la Ley 29733. La inteligencia artificial sugiere; quien decide es una persona de su equipo.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre sus historias"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada día que la copia de una historia tarda cinco días, hay un paciente esperando, un reclamo posible y un espacio del archivo que sigue creciendo."),
        },
    },
    "estudios": {
        "nombre": "Estudios jurídicos y contables",
        "segmento": "Estudios de abogados y estudios contables",
        "c1": {
            "asuntos": ["PUBLICIDAD | Papel, WhatsApp y nube en un solo archivo",
                        "PUBLICIDAD | Ese documento de 2021, en segundos"],
            "pre": "Encuentre cualquier documento por cliente o expediente.",
            "cuerpo": p("{{saludo}}:")
            + p("En un estudio, los documentos llegan por todos lados: papel en el escritorio, fotos por WhatsApp y PDF en la nube. Encontrar el escrito de un expediente o el comprobante de un cliente de 2021 depende de quién lo guardó y dónde.")
            + p("<b>Arriera</b> junta el papel y los PDF de {{organizacion}} en un solo archivo, y su inteligencia artificial lee y clasifica cada documento. Lo encuentra por cliente, número de expediente, RUC o fecha en segundos, y se conecta a su sistema por API.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Antes y después de un expediente",
                        "PUBLICIDAD | Lo que cambia en su estudio el primer mes"],
            "pre": "Tres cambios concretos para su equipo.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en {{organizacion}}:")
            + lista([("los PDF viven en carpetas y correos de cada persona.", "todos entran al mismo archivo y la IA los lee igual que el papel."),
                     ("una fiscalización o una audiencia obliga a buscar a última hora.", "el documento aparece en segundos por cliente, expediente o fecha."),
                     ("cualquiera puede ver cualquier carpeta.", "permisos por cliente y un registro de quién consultó qué.")])
            + p("Los documentos de sus clientes quedan en un servidor a nombre del estudio, no en una nube compartida, y Arriera se conecta por API con Odoo, SAP Business One y otros sistemas.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("La próxima fiscalización o audiencia no avisa con tiempo. Cada documento que hoy está en un WhatsApp o en una caja es una búsqueda de última hora."),
        },
    },
    "seguros": {
        "nombre": "Seguros, corredores y AFOCAT",
        "segmento": "Corredores de seguros, ajustadores, AFOCAT y fondos de siniestros",
        "c1": {
            "asuntos": ["PUBLICIDAD | Un expediente de siniestro, completo y foliado",
                        "PUBLICIDAD | Pólizas y siniestros, buscables en segundos"],
            "pre": "La IA separa, clasifica y numera cada documento.",
            "cuerpo": p("{{saludo}}:")
            + p("Un expediente de siniestro junta la póliza, el certificado, informes y comprobantes, y cada hoja tiene que estar foliada y a mano cuando la piden. En las AFOCAT, el reglamento de la SBS pide foliarlo dentro de las 48 horas de recibido el último documento.")
            + p("<b>Arriera</b> digitaliza esos expedientes en {{organizacion}}: su inteligencia artificial separa y clasifica cada documento, extrae póliza, asegurado, fechas y montos, y numera cada página con su huella digital. Todo queda trazable en una auditoría que nadie puede alterar.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Antes y después de un expediente de siniestro",
                        "PUBLICIDAD | Trazabilidad sin foliar a mano"],
            "pre": "Tres cambios concretos para su equipo.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en {{organizacion}}:")
            + lista([("cada documento del siniestro se ordena y folia a mano.", "la IA lo clasifica y numera cada página con su huella."),
                     ("buscar una póliza o un comprobante toma tiempo.", "aparece en segundos por número de póliza, asegurado o fecha."),
                     ("la trazabilidad depende de registros sueltos.", "una auditoría inmutable dice quién hizo qué con cada documento.")])
            + p("Los documentos quedan en un servidor a nombre de su empresa y Arriera se conecta por API con su sistema, para que su equipo no cambie de pantalla.")
            + p("La demo con 20 páginas de sus expedientes sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre sus expedientes"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Un expediente incompleto o difícil de encontrar demora un pago, una respuesta al cliente o un requerimiento del regulador."),
        },
    },
    "educacion": {
        "nombre": "Universidades y colegios profesionales",
        "segmento": "Universidades e institutos privados, colegios profesionales",
        "c1": {
            "asuntos": ["PUBLICIDAD | Un legajo, en segundos",
                        "PUBLICIDAD | Constancias sin bajar al archivo central"],
            "pre": "Legajos de alumnos y colegiados, buscables por DNI.",
            "cuerpo": p("{{saludo}}:")
            + p("Cuando un egresado pide una constancia o un colegiado necesita su legajo, alguien baja al archivo central de {{organizacion}} y busca carpeta por carpeta.")
            + p("<b>Arriera</b> digitaliza esos legajos y su inteligencia artificial lee cada hoja: nombre, código, DNI y fechas quedan indexados. El legajo aparece en segundos, y cada constancia o copia sale con plazo, historial y entrega registrada.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + p("O responda este correo con el día y la hora que le acomoden."),
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Antes y después del archivo central",
                        "PUBLICIDAD | Lo que cambia en secretaría el primer mes"],
            "pre": "Tres cambios concretos y los datos personales protegidos.",
            "cuerpo": p("{{saludo}}:")
            + p("Le resumo lo que cambia con Arriera en {{organizacion}}:")
            + lista([("el legajo se busca carpeta por carpeta.", "escribe nombre, código o DNI y abre el documento exacto."),
                     ("cada constancia se arma a mano y sin plazo visible.", "sale con plazo, historial y entrega registrada."),
                     ("cualquiera con llave del archivo ve todo.", "permisos por área: cada oficina ve solo lo suyo.")])
            + p("Los datos personales quedan en un servidor a nombre de su institución, con el registro de accesos que pide la Ley 29733, y Arriera se conecta por API con su sistema académico o administrativo.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo central"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada promoción suma cajas al archivo central, y cada constancia pedida a última hora depende de que alguien encuentre la carpeta a tiempo."),
        },
    },
}

PERFIL_A_SECTOR = {
    "Fondo / mutual / cooperativa": "fondos",
    "Notaría": "notarias",
    "Clínica / hospital privado": "salud",
    "Laboratorio / diagnóstico": "salud",
    "Estudio de abogados": "estudios",
    "Estudio contable": "estudios",
    "Aseguradora / corredor": "seguros",
    "Universidad / instituto privado": "educacion",
    "Colegio profesional": "educacion",
}

# Días hábiles después del correo anterior; los correos 2 y 3 solo salen si no hubo respuesta.
TIEMPOS = [(0, None), (3, "if_no_reply"), (5, "if_no_reply")]


def secuencias():
    out = []
    for clave, s in SECTORES.items():
        pasos = []
        for i, k in enumerate(("c1", "c2", "c3")):
            c = s[k]
            pasos.append({"orden": i + 1, "asunto": c["asuntos"][0], "asunto_b": c["asuntos"][1], "pre": c["pre"],
                          "html": html(c["pre"], c["cuerpo"]), "dias": TIEMPOS[i][0], "condicion": TIEMPOS[i][1]})
        out.append({"clave": clave, "nombre": f"Arriera · {s['nombre']} · 3 correos", "segmento": s["segmento"], "pasos": pasos})
    return out
