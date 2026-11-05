"""Secuencias de correo de Arriera para la base de prospectos (nov-2026, versión 2). Una por sector, 3 correos cada una.

Versión 2: cada correo abre con un dolor que el decisor vive o teme, apoyado en un hecho público y verificable
(sanción, norma o caso con fecha y fuente). El dolor no es «buscar papeles»: es la responsabilidad personal de quien
firma, entrega o custodia, cuando el archivo en papel no deja registro.

Estructura:
  Correo 1 · Escena + hecho reciente (prueba) + la pregunta incómoda + mecanismo concreto de Arriera + oferta.
  Correo 2 · Segundo ángulo del dolor (regulador, datos sensibles, rotación de personal) + antes/después + objeción
             de seguridad resuelta + oferta.
  Correo 3 · Costo de no hacer nada, propio del sector + cierre «break-up» con micro-compromiso (1, 2 o 3).
Ley 28493: el asunto lleva «PUBLICIDAD», el remitente se identifica y hay forma de darse de baja.
Variables: {{saludo}} y {{organizacion}} son campos personalizados del contacto; {{unsubscribe_url}} la pone Boost.

Fuentes de los hechos citados (revisadas el 05-nov-2026):
- Caretas, 27-ago-2026: SUSALUD multa con S/ 69,550 a la Clínica Delgado por enviar por correo, sin orden judicial ni
  consentimiento, la historia clínica de unos 15 años de una paciente en respuesta a dos oficios fiscales.
- Andina, 02-jul-2025: SUSALUD multa con 125 UIT (S/ 668,750) a la misma clínica por divulgar datos de salud de una
  paciente famosa internada en feb-2025; falta grave.
- LexLatin, 2026: nuevo reglamento de la Ley 29733 (vigente 31-mar-2025): incidentes con datos sensibles se notifican
  en 48 h; Oficial de Datos Personales obligatorio sin importar el tamaño si se tratan datos sensibles; ANPD hizo 760
  fiscalizaciones en 2025 (+67 %), multas por más de S/ 11 millones, tope 100 UIT; educación entre los sectores más
  fiscalizados en 2026.
- El Comercio, 22-abr-2024: documentos del AGN (incluido patrimonio notarial) en los sótanos del Palacio de Justicia;
  pérdidas por el agua de un incendio en 2000 y por la rotura de una tubería de desagüe en 2020.
- LP Derecho: dos años después del cese de un notario, los testimonios de su archivo los expide el AGN o el archivo
  regional.
- Diario Correo, 10-ago-2025: notaría de Ica advierte de perfiles falsos que cobraban por Yape «trámites en línea».
- B&B Consultores: art. 177 num. 1 del Código Tributario, no exhibir libros o documentos: 0.6 % de los ingresos netos,
  mínimo 10 % de la UIT, máximo 25 UIT; varias multas si las omisiones son distintas (criterio del Tribunal Fiscal).
- SUNAT, Informe 023-2019-SUNAT/7T0000: la Ley 28186 impide destruir originales mientras el tributo no haya prescrito
  (4, 6 o 10 años).
- El Peruano: Res. SBS 02963-2021 (expediente por siniestro de AFOCAT, físico o electrónico) y Res. SBS 02164-2026
  (publicada a fines de ago-2026; cuenta pagadora del Fondo de la AFOCAT con trazabilidad: identificar, registrar y verificar cada movimiento con documentación sustentatoria; vigente 90 días después).
- gob.pe (MINJUSDH): sanción a dos universidades por usar datos personales con fines publicitarios sin consentimiento.
"""

WA = "https://wa.me/51913527489?text=Hola%20Enrique%2C%20quiero%20agendar%20la%20demo%20de%20Arriera"

OFERTA = ("Le propongo una demo de 20 minutos con <b>20 páginas de su propio archivo, sin costo</b>. "
          "Usted elige las páginas y al terminar se borran.")
# Con datos de salud, la demo no debe tocar datos reales de pacientes o asociados.
OFERTA_SENSIBLE = ("Le propongo una demo de 20 minutos con <b>20 páginas de su archivo, sin costo</b>. "
                   "Para no exponer datos de pacientes, puede ser una muestra administrativa o con los datos tapados; "
                   "al terminar se borra todo.")


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


def pregunta(t):
    """La pregunta incómoda: sola, en negrita, para que se lea aunque se escanee el correo."""
    return f'<p style="margin:0 0 14px"><b>{t}</b></p>'


def fuente(t):
    return f'<p style="margin:-6px 0 14px;font-size:12px;color:#8A8F80">Fuente: {t}</p>'


def lista(items):
    lis = "".join(f'<li style="margin:0 0 8px"><b>Hoy:</b> {a}<br><b>Con Arriera:</b> {b}</li>' for a, b in items)
    return f'<ul style="margin:0 0 16px;padding-left:20px">{lis}</ul>'


def cierre_3(perdida, pregunta_final):
    return (p("{{saludo}}:")
            + p("No quiero llenar su bandeja, así que este es mi último correo sobre este tema.")
            + p(perdida)
            + pregunta(pregunta_final)
            + p("Si le sirve, respóndame solo con un número:")
            + '<p style="margin:0 0 14px">1 — Sí, agendemos la demo con 20 páginas de nuestro archivo.<br>'
              "2 — Ahora no, escríbame en tres meses.<br>3 — No es un tema para nosotros.</p>"
            + p("Con un «1» le escribo hoy mismo por WhatsApp para fijar la hora."))


CTA = p("O responda este correo con el día y la hora que le acomoden.")

SECTORES = {
    "salud": {
        "nombre": "Clínicas y laboratorios",
        "segmento": "Clínicas, hospitales privados, policlínicos, laboratorios y centros de diagnóstico",
        "c1": {
            "asuntos": ["PUBLICIDAD | El oficio llegó y la historia salió por correo",
                        "PUBLICIDAD | ¿Quién decide qué sale de su archivo de historias?"],
            "pre": "S/ 69,550 de multa por responder un oficio de buena fe.",
            "cuerpo": p("{{saludo}}:")
            + p("En agosto, SUSALUD multó con S/ 69,550 a una de las clínicas más conocidas de Lima. ¿La falta? Responder dos oficios de la Fiscalía enviando por correo la historia clínica completa de una paciente, unos 15 años de atención, sin orden judicial ni su consentimiento. Quien la envió creyó que cumplía la ley.")
            + fuente("Caretas, 27 de agosto de 2026.")
            + p("Lo incómodo es que eso puede pasar en cualquier clínica con historias en papel. Llega el pedido con apuro, alguien busca la carpeta, escanea todo y lo manda. Nadie revisa qué páginas debían salir y no queda escrito quién lo decidió.")
            + pregunta("En {{organizacion}}, ¿quién toma hoy esa decisión y dónde queda registrada?")
            + p("<b>Arriera</b> digitaliza sus historias y su inteligencia artificial lee cada hoja: paciente, DNI, fechas y tipo de documento. Cuando llega un pedido del paciente, de un familiar o de una autoridad, el sistema registra quién lo hizo y en calidad de qué, qué documentos salen y quién los entrega. Lo que no corresponde se oculta con un tachado real, que no se puede quitar del PDF. Y la copia sale en minutos, no en cinco días hábiles.")
            + p(OFERTA_SENSIBLE) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Si hoy se filtra una historia, ¿sabría quién la vio?",
                        "PUBLICIDAD | 125 UIT por un dato de salud"],
            "pre": "La primera pregunta del regulador es la que el papel no responde.",
            "cuerpo": p("{{saludo}}:")
            + p("En febrero de 2025 se filtró el estado de salud de una paciente famosa internada en Lima. SUSALUD lo calificó como falta grave y multó a la clínica con 125 UIT, más de S/ 668 mil.")
            + fuente("Andina, 2 de julio de 2025.")
            + p("Ante una filtración, lo primero que pregunta el regulador es quién tuvo acceso a esa historia. Con un archivo en papel, la respuesta suele ser un cuaderno en el mostrador, o nada. Y entonces la clínica responde por todo su personal.")
            + p("Además, la vara subió. El nuevo reglamento de la Ley 29733 obliga a notificar en 48 horas un incidente con datos sensibles. Y quien trata datos de salud debe tener un Oficial de Datos Personales, sin importar su tamaño.")
            + lista([("la historia se presta en carpeta y vuelve (o no) al estante.", "se consulta en pantalla, con permisos por persona y por área."),
                     ("nadie puede decir quién abrió una historia la semana pasada.", "cada acceso a un dato de salud queda en un registro que nadie puede borrar."),
                     ("el Oficial de Datos Personales arma su reporte a mano.", "tiene un panel con los accesos a datos sensibles, listo para mostrar.")])
            + p("Todo vive en un servidor a nombre de {{organizacion}}, con los datos sensibles cifrados. La inteligencia artificial sugiere; decide su equipo.")
            + p("La demo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre sus historias"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("El próximo pedido de historia ya está en camino: un paciente que quiere su copia hoy, un familiar con una carta poder o un oficio con plazo. La diferencia está en cómo lo atiende su equipo: con un registro que lo respalda, o con una fotocopiadora y buena fe.",
                               "Si ese pedido llega mañana, ¿su equipo está cubierto?"),
        },
    },
    "notarias": {
        "nombre": "Notarías",
        "segmento": "Notarías de Lima y provincias",
        "c1": {
            "asuntos": ["PUBLICIDAD | Una escritura matriz no tiene segunda copia",
                        "PUBLICIDAD | Una tubería rota y un archivo menos"],
            "pre": "El protocolo no tiene respaldo hasta que alguien se lo da.",
            "cuerpo": p("{{saludo}}:")
            + p("En 2020 se rompió una tubería de desagüe en los sótanos del Palacio de Justicia, donde el Archivo General de la Nación guarda documentos, incluido patrimonio notarial. El agua destruyó parte de ese archivo. No era la primera vez: en el 2000 ya había llegado ahí el agua con la que se apagó un incendio.")
            + fuente("El Comercio, 22 de abril de 2024.")
            + p("Una escritura matriz no tiene segunda copia. Si el tomo se moja, se quema o se pierde, desaparece la prueba de una compraventa, un poder o un testamento. Y quien responde es el notario que lo custodia.")
            + pregunta("Si mañana se pierde un tomo del protocolo de {{organizacion}}, ¿con qué lo reconstruye?")
            + p("<b>Arriera</b> digitaliza el protocolo y su inteligencia artificial lee cada hoja: otorgantes, DNI, fecha y tipo de acto. Así tiene un respaldo fiel de cada folio, con su huella digital, en un servidor a nombre de la notaría. Y gana algo que el papel no da: encontrar una escritura por nombre o DNI en segundos, aunque el usuario no traiga el número de kardex.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | ¿Quién pidió esa copia, y con qué derecho?",
                        "PUBLICIDAD | El testimonio que se entregó a quien no debía"],
            "pre": "Cada copia emitida, con nombre, calidad y fecha.",
            "cuerpo": p("{{saludo}}:")
            + p("Un testimonio solo se entrega a quien tiene legitimidad e interés. Pero la suplantación ya llegó a las notarías: en 2025, una notaría de Ica tuvo que advertir que perfiles falsos en WhatsApp y Facebook cobraban por Yape «trámites en línea» en su nombre.")
            + fuente("Diario Correo, 10 de agosto de 2025.")
            + pregunta("Si alguien reclama que se entregó una copia a quien no correspondía, ¿qué registro muestra la notaría?")
            + lista([("sin número de kardex, se busca tomo por tomo mientras el usuario espera.", "se busca por nombre, DNI o fecha del acto en todo el protocolo."),
                     ("la copia se registra a mano, si se registra.", "cada solicitud guarda quién pidió, en calidad de qué, qué se entregó y quién lo entregó."),
                     ("el orden del archivo vive en la cabeza de una o dos personas.", "cualquier persona autorizada encuentra lo que busca, y cada consulta queda en una auditoría que nadie puede alterar.")])
            + p("Si más adelante quieren dar valor legal a las copias digitales, el flujo de Arriera ya sigue los pasos de la NTP 392.030-2 para microformas.")
            + p("La demo con 20 páginas de su protocolo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Su protocolo le va a sobrevivir"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("El protocolo de {{organizacion}} va a sobrevivir a la notaría. Dos años después del cese de un notario, los testimonios de su archivo ya los expide el Archivo General de la Nación o el archivo regional. Lo que se entregue ese día, ordenado y respaldado o en cajas, también es parte de su trabajo.",
                               "¿En qué estado quiere entregar ese archivo?"),
        },
    },
    "fondos": {
        "nombre": "Fondos, mutuales y cooperativas",
        "segmento": "Fondos de ayuda mutua, mutualidades, derramas y cooperativas de ahorro y crédito",
        "c1": {
            "asuntos": ["PUBLICIDAD | Cuando la familia de un asociado viene por el beneficio",
                        "PUBLICIDAD | ¿Ese beneficio se pagó con todos los requisitos?"],
            "pre": "El expediente que nadie encuentra siempre es el de alguien que espera.",
            "cuerpo": p("{{saludo}}:")
            + p("En un fondo como {{organizacion}}, el expediente más difícil de encontrar suele ser el más urgente: el de un asociado que falleció y cuya familia viene a pedir el beneficio. Mientras alguien busca la solicitud, el informe médico y las boletas, caja por caja, la familia espera.")
            + p("Hay un segundo momento, menos visible. La auditoría o la asamblea pregunta por qué se pagó un subsidio, y la respuesta está en una carpeta. Si a esa carpeta le falta una hoja, el problema deja de ser del archivo: es de quien firmó el pago.")
            + pregunta("¿Podría hoy mostrar, en cinco minutos, el sustento completo de cualquier beneficio pagado en 2019?")
            + p("<b>Arriera</b> digitaliza el archivo del fondo y su inteligencia artificial lee cada hoja: nombre, DNI, fechas y montos, sin tipear nada. El expediente completo de un asociado aparece en segundos. Y antes de pagar, el sistema avisa si al trámite le falta un requisito.")
            + p(OFERTA_SENSIBLE) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Los informes médicos de sus asociados son datos sensibles",
                        "PUBLICIDAD | Su fondo ya necesita un Oficial de Datos Personales"],
            "pre": "760 fiscalizaciones en 2025 y una obligación que no depende del tamaño.",
            "cuerpo": p("{{saludo}}:")
            + p("Un detalle que muchos fondos pasan por alto: si guardan informes médicos para pagar subsidios, tratan datos de salud. Para la Ley 29733, eso los obliga a tener un Oficial de Datos Personales sin importar su tamaño, y a notificar en 48 horas cualquier incidente con esos datos.")
            + p("Y la autoridad sí está mirando: en 2025 hizo 760 fiscalizaciones, 67 % más que el año anterior, y puso multas por más de S/ 11 millones. Cada infracción puede llegar a 100 UIT.")
            + fuente("LexLatin, reforma de protección de datos personales en el Perú, 2026.")
            + lista([("los informes médicos están en cajas que abre cualquiera con la llave.", "se ven en pantalla, solo quien tiene permiso, y cada acceso queda registrado."),
                     ("alguien tipea cada hoja para indexarla.", "la inteligencia artificial llena la ficha y su equipo solo confirma lo dudoso."),
                     ("cuando cambia la directiva, se va la memoria del archivo.", "el archivo se encuentra solo y guarda el historial de quién hizo qué.")])
            + p("Arriera se instala en un servidor a nombre de su institución, cifra los datos sensibles y trae el panel de accesos que necesita el Oficial de Datos Personales.")
            + p("La demo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada mes el archivo suma cajas, y la directiva que hoy decide puede no ser la que responda mañana. El día que falte la persona que sabe dónde está todo, la pregunta simple de un asociado, o de un auditor, se vuelve un problema.",
                               "¿Quién responde por el archivo cuando esa persona no está?"),
        },
    },
    "estudios": {
        "nombre": "Estudios jurídicos y contables",
        "segmento": "Estudios de abogados y estudios contables",
        "c1": {
            "asuntos": ["PUBLICIDAD | El requerimiento tiene plazo. Su archivo, no",
                        "PUBLICIDAD | Hasta 25 UIT por cada documento que no aparece"],
            "pre": "Cuando el documento está en un WhatsApp, la multa la paga su cliente.",
            "cuerpo": p("{{saludo}}:")
            + p("Cuando SUNAT notifica un requerimiento, da un plazo. Si en ese plazo no se exhibe un libro o un comprobante, la multa es del 0.6 % de los ingresos netos del año anterior, con un tope de 25 UIT. Y el Tribunal Fiscal ha admitido una multa distinta por cada omisión.")
            + fuente("art. 177, numeral 1, del Código Tributario (B&B Consultores).")
            + p("La multa la paga el cliente. Pero explicar por qué ese comprobante estaba en el WhatsApp de un asistente que ya no trabaja con ustedes le toca al estudio. En un caso judicial pasa lo mismo: un escrito que no aparece a tiempo no tiene segunda oportunidad.")
            + pregunta("Si hoy llega un requerimiento para un cliente de {{organizacion}}, ¿cuánto tarda en reunir todo?")
            + p("<b>Arriera</b> junta en un solo archivo el papel, los PDF y las fotos que hoy llegan por WhatsApp o por correo. Su inteligencia artificial lee y clasifica cada documento, y usted lo encuentra en segundos por cliente, RUC, número de expediente o fecha. Además, se conecta por API con su sistema.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Cuando un asociado se va, ¿qué se lleva?",
                        "PUBLICIDAD | Parte de su archivo vive en celulares ajenos"],
            "pre": "El orden del archivo, y a veces una copia, sale por la puerta.",
            "cuerpo": p("{{saludo}}:")
            + p("En casi todos los estudios, una parte del archivo vive fuera del estudio: en el celular de quien recibió las fotos del cliente, en el correo de quien llevó el caso, en una carpeta de nube a nombre de una persona. Cuando esa persona se va, se lleva el orden, y a veces una copia, de documentos que el estudio está obligado a proteger.")
            + p("Y el papel no se puede botar. La Ley 28186 impide destruir los originales mientras el tributo no haya prescrito, y la prescripción puede llegar a 10 años. Las cajas solo crecen.")
            + fuente("SUNAT, Informe N.º 023-2019-SUNAT/7T0000.")
            + lista([("cada persona guarda los PDF a su manera.", "todo entra al mismo archivo, y la inteligencia artificial lee los PDF igual que el papel."),
                     ("una fiscalización o una audiencia obliga a buscar a última hora.", "el documento aparece en segundos por cliente, expediente, RUC o fecha."),
                     ("cualquiera abre cualquier carpeta y nadie sabe quién la abrió.", "permisos por cliente y un registro de quién consultó qué.")])
            + p("Los documentos de sus clientes quedan en un servidor a nombre del estudio, no en una nube compartida. Y Arriera se conecta por API con Odoo, SAP Business One y otros sistemas.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("La próxima fiscalización o audiencia no avisa con tiempo. Cada documento que hoy está en una caja, en un correo personal o en un WhatsApp será una búsqueda de última hora, con el plazo corriendo.",
                               "¿Cuál de sus clientes sería el primero en sufrir esa búsqueda?"),
        },
    },
    "seguros": {
        "nombre": "Seguros, corredores y AFOCAT",
        "segmento": "Corredores de seguros, ajustadores, AFOCAT y fondos de siniestros",
        "c1": {
            "asuntos": ["PUBLICIDAD | Fines de noviembre: trazabilidad con documentos",
                        "PUBLICIDAD | La SBS ya pide rastrear cada operación con su sustento"],
            "pre": "La Res. SBS 02164-2026 entra en vigencia en semanas.",
            "cuerpo": p("{{saludo}}:")
            + p("A fines de agosto, la SBS publicó la Resolución 02164-2026. Desde fines de noviembre, cada movimiento del Fondo de una AFOCAT debe poder identificarse, registrarse y verificarse con su documentación sustentatoria. A eso se suma el expediente por siniestro que ya exigía la Resolución 02963-2021.")
            + fuente("El Peruano, normas legales.")
            + p("Para un corredor o un ajustador, la pregunta es la misma cada vez que un cliente reclama o el regulador pide un caso: ¿dónde está el documento que sustenta esa decisión, y desde cuándo está ahí?")
            + pregunta("Si hoy le piden el expediente completo de un siniestro de 2023, ¿cuánto tarda {{organizacion}} en entregarlo?")
            + p("<b>Arriera</b> digitaliza esos expedientes. Su inteligencia artificial separa y clasifica cada documento, extrae póliza, asegurado, fechas y montos, y numera cada página con su huella digital. Todo queda en una auditoría que nadie puede alterar.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | El siniestro que se paga tarde por una hoja",
                        "PUBLICIDAD | Trazabilidad sin foliar a mano"],
            "pre": "Un documento que falta demora el pago y el cliente se lo cobra a usted.",
            "cuerpo": p("{{saludo}}:")
            + p("Cuando a un expediente de siniestro le falta una hoja, el pago se demora. El asegurado no culpa a la norma, culpa a quien le vendió o le atiende el seguro, y ese reclamo puede terminar en el regulador.")
            + lista([("cada documento del siniestro se ordena y se folia a mano.", "la inteligencia artificial lo clasifica y numera cada página con su huella."),
                     ("buscar una póliza o un comprobante toma tiempo.", "aparece en segundos por número de póliza, asegurado o fecha."),
                     ("la trazabilidad depende de registros sueltos.", "una auditoría inmutable dice quién hizo qué con cada documento.")])
            + p("Los documentos quedan en un servidor a nombre de su empresa, y Arriera se conecta por API con su sistema para que su equipo no cambie de pantalla.")
            + p("La demo con 20 páginas de sus expedientes sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre sus expedientes"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Un expediente incompleto o difícil de encontrar demora un pago, una respuesta al cliente o un requerimiento de la SBS. Y desde fines de noviembre, la trazabilidad con documentos ya no es opcional para las AFOCAT.",
                               "¿Su archivo está listo para el primer requerimiento?"),
        },
    },
    "educacion": {
        "nombre": "Universidades y colegios profesionales",
        "segmento": "Universidades e institutos privados, colegios profesionales",
        "c1": {
            "asuntos": ["PUBLICIDAD | El egresado que necesita su certificado para el viernes",
                        "PUBLICIDAD | Un legajo de 2009, en segundos"],
            "pre": "La urgencia es del egresado; la queja, de la institución.",
            "cuerpo": p("{{saludo}}:")
            + p("Un egresado de 2009 consigue un trabajo en el extranjero y le piden su certificado de estudios para el viernes. En muchas instituciones eso significa bajar al archivo central, buscar las actas de ese año y armar el documento a mano. Si el acta está incompleta o dañada, la urgencia es del egresado. La queja, y a veces el reclamo formal, es para la institución.")
            + pregunta("En {{organizacion}}, ¿cuántos días tarda hoy una constancia de hace quince años?")
            + p("<b>Arriera</b> digitaliza actas, legajos y expedientes, y su inteligencia artificial lee cada hoja: nombre, código, DNI y fechas. El legajo aparece en segundos. Cada constancia o copia sale con plazo, historial y entrega registrada, para que secretaría sepa qué está pendiente y desde cuándo.")
            + p(OFERTA) + boton("Agendar la demo por WhatsApp") + CTA,
        },
        "c2": {
            "asuntos": ["PUBLICIDAD | Educación, entre los sectores que más fiscaliza la ANPD",
                        "PUBLICIDAD | Los legajos de sus alumnos también son datos personales"],
            "pre": "Dos universidades ya fueron sancionadas por el uso de datos personales.",
            "cuerpo": p("{{saludo}}:")
            + p("En 2026, educación está entre los cuatro sectores que más fiscaliza la Autoridad de Protección de Datos Personales, junto con finanzas, telecomunicaciones y retail. Cada infracción puede llegar a 100 UIT, y el Ministerio de Justicia ya sancionó a dos universidades por usar datos personales sin consentimiento.")
            + fuente("LexLatin, 2026, y gob.pe (MINJUSDH).")
            + p("Un archivo central en papel es difícil de defender ante una fiscalización: cualquiera con la llave ve todo y nadie puede decir quién consultó qué.")
            + lista([("el legajo se busca carpeta por carpeta.", "se escribe el nombre, el código o el DNI y se abre el documento exacto."),
                     ("cada constancia se arma a mano, sin plazo visible.", "sale con plazo, historial y entrega registrada."),
                     ("cualquiera con la llave del archivo ve todo.", "permisos por área: cada oficina ve solo lo suyo y cada acceso queda registrado.")])
            + p("Los datos quedan en un servidor a nombre de su institución, y Arriera se conecta por API con su sistema académico o administrativo.")
            + p("La demo con 20 páginas de su archivo sigue en pie.") + boton("Quiero ver la demo"),
        },
        "c3": {
            "asuntos": ["PUBLICIDAD | ¿Cierro este tema?", "PUBLICIDAD | Última nota sobre su archivo central"],
            "pre": "Responda con un número y listo.",
            "cuerpo": cierre_3("Cada promoción suma cajas al archivo central, y cada constancia urgente depende de que alguien encuentre la carpeta a tiempo. Mientras tanto, los datos de miles de alumnos siguen en estantes sin registro de acceso.",
                               "¿Cuánto tiempo más puede sostener eso su archivo central?"),
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
