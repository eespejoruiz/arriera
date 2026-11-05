"""Secuencias de correo de Arriera para la base de prospectos (nov-2026, versión 3: diseño visual).

v2 (texto): cada correo abre con un dolor real del sector, apoyado en un hecho público con fecha y fuente.
v3 (diseño): mismo mensaje en formato visual tipo boletín (referencia que eligió Enrique: correo de Repsol Más):
  logo · titular grande con resalte · banner con foto y cifra · texto corto · pregunta destacada ·
  bloque visual (pasos numerados, antes/después o respuestas 1-2-3) · banda oscura con la oferta y el botón ·
  pie oscuro con datos legales. Modo «Mixto»: solo el logo y una foto son imágenes; cifras, tarjetas y bandas
  son HTML, así el mensaje se lee aunque el cliente de correo bloquee las imágenes.
Imágenes públicas en https://arriera.tech/correo/ (JPG/PNG livianos).
Ley 28493: el asunto lleva «PUBLICIDAD», el remitente se identifica y hay forma de darse de baja.
Variables: {{saludo}} y {{organizacion}} son campos del contacto; {{unsubscribe_url}} la pone Boost.

Fuentes de los hechos citados (revisadas el 05-nov-2026):
- Caretas, 27-ago-2026: SUSALUD multa con S/ 69,550 a una clínica de Lima por enviar por correo, sin orden judicial ni
  consentimiento, la historia clínica de unos 15 años de una paciente en respuesta a dos oficios fiscales.
- Andina, 02-jul-2025: SUSALUD multa con 125 UIT (S/ 668,750) a la misma clínica por divulgar datos de salud de una
  paciente internada en feb-2025; falta grave.
- LexLatin, 2026: reglamento de la Ley 29733 (vigente 31-mar-2025): incidentes con datos sensibles se notifican en 48 h;
  Oficial de Datos Personales obligatorio sin importar el tamaño si se tratan datos sensibles; 760 fiscalizaciones en
  2025 (+67 %), multas por más de S/ 11 millones, tope 100 UIT; educación entre los 4 sectores más fiscalizados en 2026.
- El Comercio, 22-abr-2024: documentos del AGN (incluido patrimonio notarial) en sótanos del Palacio de Justicia;
  pérdidas por el agua de un incendio (2000) y por una tubería de desagüe rota (2020).
- LP Derecho: dos años después del cese de un notario, sus testimonios los expide el AGN o el archivo regional.
- Diario Correo, 10-ago-2025: notaría de Ica advierte de perfiles falsos que cobraban por Yape «trámites en línea».
- B&B Consultores: art. 177 num. 1 del Código Tributario: 0.6 % de ingresos netos, mín. 10 % UIT, máx. 25 UIT; varias
  multas si las omisiones son distintas (criterio del Tribunal Fiscal).
- SUNAT, Informe 023-2019-SUNAT/7T0000: la Ley 28186 impide destruir originales mientras el tributo no prescriba
  (4, 6 o 10 años).
- El Peruano: Res. SBS 02963-2021 (expediente por siniestro de AFOCAT) y Res. SBS 02164-2026 (publicada a fines de
  ago-2026; cuenta pagadora del Fondo de la AFOCAT con trazabilidad de cada movimiento con documentación sustentatoria;
  vigente 90 días después).
- gob.pe (MINJUSDH): sanción a dos universidades por usar datos personales con fines publicitarios sin consentimiento.
"""

WA = "https://wa.me/51913527489?text=Hola%20Enrique%2C%20quiero%20agendar%20la%20demo%20de%20Arriera"
IMG = "https://arriera.tech/correo/"

# Paleta Arriera
NOCHE, MUSGO, HOJA, LIMA, MARFIL, OXIDO, AMBAR = "#0F110B", "#1B1F13", "#A9B640", "#DCE57A", "#F4F5EE", "#E07A4E", "#E8C25A"
TINTA, GRIS, LINEA = "#1F2318", "#6B705F", "#E2E4D8"
F = "'Hanken Grotesk',Arial,Helvetica,sans-serif"
FM = "'Special Elite','Courier New',Courier,monospace"


# ---------- piezas del diseño ----------

def p(t):
    return f'<p style="margin:0 0 14px;font-family:{F};font-size:16px;line-height:1.6;color:{TINTA}">{t}</p>'


def cabecera():
    return f"""<tr><td style="padding:28px 32px 6px" class="px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td><a href="https://arriera.tech"><img src="{IMG}logo.png" width="150" height="54" alt="Arriera" style="display:block;border:0;width:150px;height:auto"></a></td>
<td align="right" class="hide-m" style="font-family:{F};font-size:12px;color:{GRIS};letter-spacing:.04em;text-transform:uppercase">Gestión documental con IA</td>
</tr></table></td></tr>"""


def titular(kicker, linea, resalte):
    return f"""<tr><td style="padding:22px 32px 8px" class="px">
<p style="margin:0 0 10px;font-family:{F};font-size:14px;color:{GRIS}">{kicker}</p>
<h1 style="margin:0;font-family:{F};font-size:34px;line-height:1.15;font-weight:800;color:{NOCHE};letter-spacing:-.02em" class="h1">{linea}<br>
<span style="display:inline-block;margin-top:8px;background:{HOJA};background-image:linear-gradient(100deg,{HOJA},{LIMA});color:{NOCHE};padding:4px 14px 6px;border-radius:12px">{resalte}</span></h1>
</td></tr>"""


def banner(foto, alt, cifra, texto, fuente):
    f = f'<p style="margin:12px 0 0;font-family:{F};font-size:12px;color:#9BA18C">Fuente: {fuente}</p>' if fuente else ""
    return f"""<tr><td style="padding:20px 32px 6px" class="px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-radius:22px;overflow:hidden;background:{MUSGO}">
<tr><td><img src="{IMG}{foto}" width="536" alt="{alt}" style="display:block;border:0;width:100%;height:auto"></td></tr>
<tr><td style="padding:22px 26px 24px;background:{MUSGO};background-image:linear-gradient(160deg,{MUSGO},{NOCHE})">
<p style="margin:0;font-family:{F};font-size:46px;line-height:1.05;font-weight:800;color:{LIMA};letter-spacing:-.02em" class="cifra">{cifra}</p>
<p style="margin:10px 0 0;font-family:{F};font-size:17px;line-height:1.45;color:{MARFIL}">{texto}</p>{f}
</td></tr></table></td></tr>"""


def cuerpo(parrafos):
    return f'<tr><td style="padding:22px 32px 4px" class="px">{p("{{saludo}}:")}{"".join(p(x) for x in parrafos)}</td></tr>'


def pregunta(t):
    return f"""<tr><td style="padding:6px 32px 10px" class="px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="background:#FBEDE5;border-left:5px solid {OXIDO};border-radius:14px;padding:18px 20px;font-family:{F};font-size:19px;line-height:1.4;font-weight:700;color:{NOCHE}">{t}</td>
</tr></table></td></tr>"""


def seccion(titulo, filas):
    return f"""<tr><td style="padding:22px 32px 6px" class="px">
<h2 style="margin:0 0 14px;font-family:{F};font-size:24px;line-height:1.2;font-weight:800;color:{NOCHE}">{titulo}</h2>
{filas}</td></tr>"""


def pasos(items, muestra=None):
    """items: [(etiqueta, texto)]. muestra: ejemplo de lo que lee la IA (DATOS DEMO), en Special Elite."""
    filas = ""
    colores = [MUSGO, MUSGO, OXIDO]
    for i, (et, tx) in enumerate(items):
        extra = ""
        if i == 1 and muestra:
            extra = (f'<span style="display:inline-block;margin-top:8px;background:{MARFIL};border:1px dashed {HOJA};'
                     f'border-radius:8px;padding:4px 8px;font-family:{FM};font-size:13px;color:{MUSGO}">{muestra}</span>')
        filas += f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 10px;background:#FFFFFF;border:1px solid {LINEA};border-radius:16px">
<tr><td width="54" valign="top" style="padding:16px 0 16px 16px">
<div style="width:38px;height:38px;line-height:38px;border-radius:50%;background:{LIMA};text-align:center;font-family:{F};font-size:19px;font-weight:800;color:{NOCHE}">{i + 1}</div></td>
<td valign="top" style="padding:14px 18px 16px 10px">
<span style="display:inline-block;background:{colores[i]};color:{MARFIL};font-family:{F};font-size:13px;font-weight:700;padding:4px 12px;border-radius:999px">{et}</span>
<p style="margin:8px 0 0;font-family:{F};font-size:15px;line-height:1.5;color:{TINTA}">{tx}</p>{extra}</td></tr></table>"""
    return filas


def antes_despues(items):
    filas = ""
    for hoy, con in items:
        filas += f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 10px"><tr>
<td class="col" width="48%" valign="top" style="background:#ECEDE5;border-radius:14px;padding:14px 16px;font-family:{F};font-size:14px;line-height:1.45;color:{GRIS}">
<span style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8A8F80">Hoy</span><br>{hoy}</td>
<td class="sep" width="4%" style="font-size:0">&nbsp;</td>
<td class="col" width="48%" valign="top" style="background:{MUSGO};border-radius:14px;padding:14px 16px;font-family:{F};font-size:14px;line-height:1.45;color:{MARFIL}">
<span style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{LIMA}">Con Arriera</span><br>{con}</td>
</tr></table>"""
    return filas


def opciones():
    ops = [("1", "Sí, agendemos la demo con 20 páginas de nuestro archivo.", LIMA),
           ("2", "Ahora no, escríbame en tres meses.", "#ECEDE5"),
           ("3", "No es un tema para nosotros.", "#ECEDE5")]
    filas = ""
    for n, t, c in ops:
        filas += f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 10px;background:#FFFFFF;border:1px solid {LINEA};border-radius:16px">
<tr><td width="70" style="padding:14px 0 14px 16px"><div style="width:46px;height:46px;line-height:46px;border-radius:50%;background:{c};text-align:center;font-family:{F};font-size:24px;font-weight:800;color:{NOCHE}">{n}</div></td>
<td style="padding:14px 18px 14px 6px;font-family:{F};font-size:16px;line-height:1.4;color:{TINTA}">{t}</td></tr></table>"""
    return filas + p("Con un «1» le escribo hoy mismo por WhatsApp para fijar la hora.")


def oferta(sensible, boton="Agendar la demo por WhatsApp"):
    detalle = ("Para no exponer datos de pacientes, puede ser una muestra administrativa o con los datos tapados. Al terminar se borra todo."
               if sensible else "Usted elige las páginas y al terminar se borran.")
    return f"""<tr><td style="padding:22px 32px 6px" class="px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-radius:22px;background:{NOCHE};background-image:linear-gradient(135deg,{MUSGO},{NOCHE})">
<tr><td style="padding:26px 26px 28px">
<p style="margin:0;font-family:{F};font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{HOJA}">Demo de 20 minutos · sin costo</p>
<p style="margin:8px 0 0;font-family:{F};font-size:28px;line-height:1.15;font-weight:800;color:{MARFIL}">Véalo con <span style="color:{LIMA}">20 páginas de su archivo</span></p>
<p style="margin:10px 0 20px;font-family:{F};font-size:15px;line-height:1.5;color:#C9CCBC">{detalle}</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="border-radius:999px;background:{LIMA}">
<a href="{WA}" style="display:inline-block;padding:14px 26px;font-family:{F};font-size:16px;font-weight:800;color:{NOCHE};text-decoration:none;border-radius:999px">{boton} &rarr;</a></td></tr></table>
<p style="margin:14px 0 0;font-family:{F};font-size:14px;color:#C9CCBC">O responda este correo con el día y la hora que le acomoden.</p>
</td></tr></table></td></tr>"""


def firma():
    return f"""<tr><td style="padding:22px 32px 26px" class="px">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td width="56" valign="top"><img src="{IMG}isotipo.png" width="42" alt="" style="display:block;border:0;width:42px;height:auto"></td>
<td style="font-family:{F};font-size:15px;line-height:1.5;color:{TINTA}"><b>Enrique Espejo</b><br>
<span style="color:{GRIS}">Arriera · gestión documental con IA</span><br>
<a href="{WA}" style="color:{MUSGO};text-decoration:none">WhatsApp +51 913 527 489</a> · <a href="https://arriera.tech" style="color:{MUSGO}">arriera.tech</a></td>
</tr></table></td></tr>"""


def pie():
    return f"""<tr><td style="background:{NOCHE};padding:26px 32px 30px;border-radius:0 0 24px 24px" class="px">
<img src="{IMG}logo-marfil.png" width="96" alt="Arriera" style="display:block;border:0;width:96px;height:auto;margin:0 0 14px">
<p style="margin:0;font-family:{F};font-size:12px;line-height:1.6;color:#A4A898">Arriera es una marca de Anomaly LA S.A.C., Lima, Perú.
Le escribo porque esta dirección figura como contacto público de {{{{organizacion}}}}. Si no desea recibir más correos,
<a href="{{{{unsubscribe_url}}}}" style="color:{LIMA}">dese de baja aquí</a> o responda «BAJA».</p></td></tr>"""


def html(pre, filas):
    return f"""<!doctype html><html lang="es" xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;700;800&family=Special+Elite&display=swap" rel="stylesheet">
<title>Arriera</title>
<style>
body{{margin:0;padding:0;background:#E7E9DD}} img{{-ms-interpolation-mode:bicubic}} a{{text-decoration:none}}
@media (max-width:620px){{
 .px{{padding-left:18px!important;padding-right:18px!important}}
 .h1{{font-size:28px!important}} .hide-m{{display:none!important}} .cifra{{font-size:38px!important}}
 .col{{display:block!important;width:auto!important}} .sep{{display:block!important;height:6px!important;width:auto!important}}
}}
</style></head>
<body style="margin:0;padding:0;background:#E7E9DD">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">{pre}&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#E7E9DD"><tr><td align="center" style="padding:24px 10px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:{MARFIL};border-radius:24px">
{"".join(filas)}
</table></td></tr></table></body></html>"""


# ---------- contenido ----------
# Cada correo: asuntos [A, B], pre, kicker, titular (línea, resalte), banner (foto, alt, cifra, texto, fuente),
# parrafos, pregunta, bloque: ("pasos", titulo, items, muestra) | ("antes", titulo, items) | ("opciones", titulo).

def c3(kicker, foto, cifra, texto, fuente, parrafo, preg):
    return {"asuntos": ["PUBLICIDAD | ¿Cierro este tema?", None], "pre": "Responda con un número y listo.",
            "kicker": kicker, "titular": ("Último correo:", "¿cierro este tema?"),
            "banner": (foto, "Equipo revisando su archivo digital en una laptop", cifra, texto, fuente),
            "parrafos": ["No quiero llenar su bandeja, así que este es mi último correo sobre este tema.", parrafo],
            "pregunta": preg, "bloque": ("opciones", "Respóndame solo con un número")}


SECTORES = {
    "salud": {
        "nombre": "Clínicas y laboratorios", "sensible": True,
        "segmento": "Clínicas, hospitales privados, policlínicos, laboratorios y centros de diagnóstico",
        "c1": {"asuntos": ["PUBLICIDAD | El oficio llegó y la historia salió por correo",
                           "PUBLICIDAD | ¿Quién decide qué sale de su archivo de historias?"],
               "pre": "S/ 69,550 de multa por responder un oficio de buena fe.",
               "kicker": "Para clínicas con historias en papel",
               "titular": ("¿Quién decide qué sale", "de su archivo?"),
               "banner": ("clinica.jpg", "Recepción de una clínica entregando información a una paciente", "S/ 69,550",
                          "de multa de SUSALUD a una clínica de Lima por enviar por correo una historia clínica de 15 años, sin orden judicial ni consentimiento.",
                          "Caretas, 27 de agosto de 2026."),
               "parrafos": ["Quien la envió respondía dos oficios de la Fiscalía y creyó que cumplía la ley. Eso puede pasar en cualquier clínica con historias en papel: llega un pedido con apuro, alguien busca la carpeta, escanea todo y lo manda. Nadie revisa qué páginas debían salir, y no queda escrito quién lo decidió."],
               "pregunta": "En {{organizacion}}, ¿quién toma hoy esa decisión y dónde queda registrada?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Digitaliza", "Escaneamos sus historias en papel, caja por caja, en un servidor a nombre de la clínica."),
                   ("La IA lee", "Paciente, DNI, fechas y tipo de documento quedan indexados sin tipear."),
                   ("Entrega con registro", "Quién pidió y en calidad de qué, qué salió y quién lo entregó. Lo que no corresponde se tacha de verdad en el PDF, y la copia sale en minutos, no en 5 días hábiles.")],
                   "HC-0412 · DNI ····4518 · 14/03/2019")},
        "c2": {"asuntos": ["PUBLICIDAD | Si hoy se filtra una historia, ¿sabría quién la vio?",
                           "PUBLICIDAD | 125 UIT por un dato de salud"],
               "pre": "La primera pregunta del regulador es la que el papel no responde.",
               "kicker": "Datos de salud y Ley 29733",
               "titular": ("Si se filtra una historia,", "¿sabría quién la vio?"),
               "banner": ("validando.jpg", "Persona revisando un documento digital en pantalla", "125 UIT",
                          "más de S/ 668 mil de multa por la filtración del estado de salud de una paciente internada en Lima. SUSALUD la calificó como falta grave.",
                          "Andina, 2 de julio de 2025."),
               "parrafos": ["Ante una filtración, lo primero que pregunta el regulador es quién tuvo acceso a esa historia. Con un archivo en papel, la respuesta suele ser un cuaderno en el mostrador, o nada.",
                            "Y la vara subió: el reglamento de la Ley 29733 obliga a notificar en <b>48 horas</b> un incidente con datos sensibles, y quien trata datos de salud debe tener un Oficial de Datos Personales, sin importar su tamaño."],
               "pregunta": "¿Podría {{organizacion}} decir hoy quién abrió una historia la semana pasada?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("La historia se presta en carpeta y vuelve, o no, al estante.", "Se consulta en pantalla, con permisos por persona y por área."),
                   ("Nadie sabe quién abrió qué historia.", "Cada acceso a un dato de salud queda en un registro que nadie puede borrar."),
                   ("El Oficial de Datos Personales arma su reporte a mano.", "Tiene un panel de accesos a datos sensibles, listo para mostrar.")])},
        "c3": c3("Clínicas · historias clínicas", "reunion.jpg", "Mañana",
                 "llega el próximo pedido de historia: un paciente que la quiere hoy, un familiar con carta poder o un oficio con plazo.", None,
                 "La diferencia está en cómo lo atiende su equipo: con un registro que lo respalda, o con una fotocopiadora y buena fe.",
                 "Si ese pedido llega mañana, ¿su equipo está cubierto?"),
    },
    "notarias": {
        "nombre": "Notarías", "sensible": False, "segmento": "Notarías de Lima y provincias",
        "c1": {"asuntos": ["PUBLICIDAD | Una escritura matriz no tiene segunda copia",
                           "PUBLICIDAD | Una tubería rota y un archivo menos"],
               "pre": "El protocolo no tiene respaldo hasta que alguien se lo da.",
               "kicker": "Para notarías con protocolo en papel",
               "titular": ("Una escritura matriz", "no tiene segunda copia"),
               "banner": ("notaria.jpg", "Notaria consultando un tomo antiguo del protocolo junto a una tablet", "2020",
                          "una tubería de desagüe rota en los sótanos del Palacio de Justicia destruyó documentos del Archivo General de la Nación, donde también hay patrimonio notarial.",
                          "El Comercio, 22 de abril de 2024."),
               "parrafos": ["No era la primera vez: en el 2000 ya había llegado ahí el agua con la que se apagó un incendio. Si un tomo se moja, se quema o se pierde, desaparece la prueba de una compraventa, un poder o un testamento. Y quien responde es el notario que lo custodia."],
               "pregunta": "Si mañana se pierde un tomo del protocolo de {{organizacion}}, ¿con qué lo reconstruye?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Digitaliza", "Un respaldo fiel de cada folio, con su huella digital, en un servidor a nombre de la notaría."),
                   ("La IA lee", "Otorgantes, DNI, fecha y tipo de acto quedan indexados sin tipear."),
                   ("Encuentra en segundos", "Una escritura por nombre o DNI, aunque el usuario no traiga el número de kardex.")],
                   "K-18233 · COMPRAVENTA · 07/06/1999")},
        "c2": {"asuntos": ["PUBLICIDAD | ¿Quién pidió esa copia, y con qué derecho?",
                           "PUBLICIDAD | El testimonio que se entregó a quien no debía"],
               "pre": "Cada copia emitida, con nombre, calidad y fecha.",
               "kicker": "Testimonios y copias certificadas",
               "titular": ("¿Quién pidió esa copia,", "y con qué derecho?"),
               "banner": ("escaner.jpg", "Persona digitalizando documentos con un escáner", "Ica, 2025",
                          "una notaría tuvo que advertir que perfiles falsos en WhatsApp y Facebook cobraban por Yape «trámites en línea» a su nombre.",
                          "Diario Correo, 10 de agosto de 2025."),
               "parrafos": ["Un testimonio solo se entrega a quien tiene legitimidad e interés. Con la suplantación llegando a las notarías, ese control ya no puede depender de la memoria de quien atiende el mostrador."],
               "pregunta": "Si alguien reclama que se entregó una copia a quien no correspondía, ¿qué registro muestra la notaría?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("Sin kardex, se busca tomo por tomo mientras el usuario espera.", "Se busca por nombre, DNI o fecha del acto en todo el protocolo."),
                   ("La copia se registra a mano, si se registra.", "Cada solicitud guarda quién pidió, en calidad de qué, qué se entregó y quién lo entregó."),
                   ("El orden del archivo vive en una o dos personas.", "Cada consulta queda en una auditoría que nadie puede alterar. Y el flujo ya sigue la NTP 392.030-2 si luego quieren microformas.")])},
        "c3": c3("Notarías · protocolo", "reunion.jpg", "2 años",
                 "después del cese de un notario, los testimonios de su archivo ya los expide el Archivo General de la Nación o el archivo regional.",
                 "LP Derecho.",
                 "El protocolo de {{organizacion}} va a sobrevivir a la notaría. Lo que se entregue ese día, ordenado y respaldado o en cajas, también es parte de su trabajo.",
                 "¿En qué estado quiere entregar ese archivo?"),
    },
    "fondos": {
        "nombre": "Fondos, mutuales y cooperativas", "sensible": True,
        "segmento": "Fondos de ayuda mutua, mutualidades, derramas y cooperativas de ahorro y crédito",
        "c1": {"asuntos": ["PUBLICIDAD | Cuando la familia de un asociado viene por el beneficio",
                           "PUBLICIDAD | ¿Ese beneficio se pagó con todos los requisitos?"],
               "pre": "El expediente que nadie encuentra siempre es el de alguien que espera.",
               "kicker": "Para fondos y mutuales con archivo en papel",
               "titular": ("El expediente que falta", "siempre es el urgente"),
               "banner": ("archivera.jpg", "Archivera buscando expedientes en una caja de archivo", "1 hoja",
                          "basta que falte en un expediente para que un pago observado lo responda quien lo firmó.", None),
               "parrafos": ["En un fondo como {{organizacion}}, el expediente más difícil de encontrar suele ser el de un asociado que falleció y cuya familia viene a pedir el beneficio. Mientras alguien busca la solicitud, el informe médico y las boletas caja por caja, la familia espera.",
                            "Y cuando la auditoría o la asamblea pregunta por qué se pagó un subsidio, la respuesta está en esa misma carpeta."],
               "pregunta": "¿Podría mostrar hoy, en cinco minutos, el sustento completo de un beneficio pagado en 2019?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Digitaliza", "Escaneamos el archivo del fondo, caja por caja, en un servidor a nombre de su institución."),
                   ("La IA lee", "Nombre, DNI, fechas y montos quedan indexados sin tipear."),
                   ("Paga con respaldo", "El expediente completo aparece en segundos y, antes de pagar, el sistema avisa si al trámite le falta un requisito.")],
                   "SUBSIDIO · DNI ····4518 · S/ 1,200.00")},
        "c2": {"asuntos": ["PUBLICIDAD | Los informes médicos de sus asociados son datos sensibles",
                           "PUBLICIDAD | Su fondo ya necesita un Oficial de Datos Personales"],
               "pre": "760 fiscalizaciones en 2025 y una obligación que no depende del tamaño.",
               "kicker": "Datos de salud de los asociados",
               "titular": ("Sus informes médicos", "ya son datos sensibles"),
               "banner": ("validando.jpg", "Persona revisando un expediente digital en pantalla", "760",
                          "fiscalizaciones de la autoridad de datos personales en 2025, 67 % más que el año anterior, con multas por más de S/ 11 millones.",
                          "LexLatin, 2026."),
               "parrafos": ["Si guardan informes médicos para pagar subsidios, tratan datos de salud. Para la Ley 29733, eso los obliga a tener un Oficial de Datos Personales sin importar su tamaño, y a notificar en 48 horas cualquier incidente. Cada infracción puede llegar a 100 UIT."],
               "pregunta": "Hoy, ¿quién puede abrir la caja donde están los informes médicos de sus asociados?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("Los informes están en cajas que abre cualquiera con la llave.", "Se ven en pantalla, solo quien tiene permiso, y cada acceso queda registrado."),
                   ("Alguien tipea cada hoja para indexarla.", "La IA llena la ficha y su equipo solo confirma lo dudoso."),
                   ("Cuando cambia la directiva, se va la memoria del archivo.", "El archivo se encuentra solo y guarda quién hizo qué. Con panel para el Oficial de Datos Personales.")])},
        "c3": c3("Fondos · archivo de asociados", "reunion.jpg", "1 persona",
                 "suele saber dónde está todo el archivo de un fondo. ¿Y el día que no está?", None,
                 "Cada mes el archivo suma cajas, y la directiva que hoy decide puede no ser la que responda mañana ante un asociado o un auditor.",
                 "¿Quién responde por el archivo cuando esa persona no está?"),
    },
    "estudios": {
        "nombre": "Estudios jurídicos y contables", "sensible": False,
        "segmento": "Estudios de abogados y estudios contables",
        "c1": {"asuntos": ["PUBLICIDAD | El requerimiento tiene plazo. Su archivo, no",
                           "PUBLICIDAD | Hasta 25 UIT por cada documento que no aparece"],
               "pre": "Cuando el documento está en un WhatsApp, la multa la paga su cliente.",
               "kicker": "Para estudios contables y de abogados",
               "titular": ("El requerimiento tiene plazo.", "Su archivo, no."),
               "banner": ("contadora.jpg", "Contadora trabajando con archivadores y una laptop", "25 UIT",
                          "es el tope de la multa por no exhibir un libro o comprobante en el plazo de un requerimiento de SUNAT. Y puede haber una por cada omisión.",
                          "art. 177, numeral 1, del Código Tributario (B&amp;B Consultores)."),
               "parrafos": ["La multa la paga el cliente. Pero explicar por qué ese comprobante estaba en el WhatsApp de un asistente que ya no trabaja con ustedes le toca al estudio. En un caso judicial pasa lo mismo: un escrito que no aparece a tiempo no tiene segunda oportunidad."],
               "pregunta": "Si hoy llega un requerimiento para un cliente de {{organizacion}}, ¿cuánto tarda en reunir todo?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Junta todo", "Papel, PDF y las fotos que hoy llegan por WhatsApp o correo, en un solo archivo del estudio."),
                   ("La IA lee", "Clasifica cada documento y extrae cliente, RUC, expediente y fechas."),
                   ("Encuentra en segundos", "Por cliente, RUC, número de expediente o fecha. Y se conecta por API con su sistema.")],
                   "RUC 20······533 · FACTURA F001-2041 · 03/2021")},
        "c2": {"asuntos": ["PUBLICIDAD | Cuando un asociado se va, ¿qué se lleva?",
                           "PUBLICIDAD | Parte de su archivo vive en celulares ajenos"],
               "pre": "El orden del archivo, y a veces una copia, sale por la puerta.",
               "kicker": "El archivo del estudio",
               "titular": ("Cuando alguien se va,", "¿qué se lleva?"),
               "banner": ("celular.jpg", "Documento fotografiado con un celular", "10 años",
                          "puede tardar en prescribir un tributo. Hasta entonces, la Ley 28186 no deja destruir los originales: las cajas solo crecen.",
                          "SUNAT, Informe N.º 023-2019-SUNAT/7T0000."),
               "parrafos": ["En casi todos los estudios, parte del archivo vive fuera del estudio: en el celular de quien recibió las fotos del cliente, en el correo de quien llevó el caso, en una carpeta de nube a nombre de una persona. Cuando esa persona se va, se lleva el orden, y a veces una copia."],
               "pregunta": "¿Cuántos documentos de sus clientes están hoy en celulares y correos personales?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("Cada persona guarda los PDF a su manera.", "Todo entra al mismo archivo, y la IA lee los PDF igual que el papel."),
                   ("Una fiscalización o audiencia obliga a buscar a última hora.", "El documento aparece en segundos por cliente, expediente, RUC o fecha."),
                   ("Cualquiera abre cualquier carpeta.", "Permisos por cliente y registro de quién consultó qué, en un servidor a nombre del estudio.")])},
        "c3": c3("Estudios · archivo de clientes", "reunion.jpg", "Sin aviso",
                 "llegan la próxima fiscalización y la próxima audiencia.", None,
                 "Cada documento que hoy está en una caja, en un correo personal o en un WhatsApp será una búsqueda de última hora, con el plazo corriendo.",
                 "¿Cuál de sus clientes sería el primero en sufrir esa búsqueda?"),
    },
    "seguros": {
        "nombre": "Seguros, corredores y AFOCAT", "sensible": False,
        "segmento": "Corredores de seguros, ajustadores, AFOCAT y fondos de siniestros",
        "c1": {"asuntos": ["PUBLICIDAD | Fines de noviembre: trazabilidad con documentos",
                           "PUBLICIDAD | La SBS ya pide rastrear cada operación con su sustento"],
               "pre": "La Res. SBS 02164-2026 entra en vigencia en semanas.",
               "kicker": "Para AFOCAT, corredores y ajustadores",
               "titular": ("Cada movimiento,", "con su documento"),
               "banner": ("escaner-2.jpg", "Persona digitalizando expedientes con un escáner", "Fin de nov.",
                          "entra en vigencia la Res. SBS 02164-2026: cada movimiento del Fondo de una AFOCAT debe poder identificarse, registrarse y verificarse con su documentación.",
                          "El Peruano, normas legales."),
               "parrafos": ["A eso se suma el expediente por siniestro que ya exigía la Res. SBS 02963-2021. Y para un corredor o un ajustador la pregunta es la misma cada vez que un cliente reclama: ¿dónde está el documento que sustenta esa decisión?"],
               "pregunta": "Si hoy le piden el expediente completo de un siniestro de 2023, ¿cuánto tarda {{organizacion}}?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Digitaliza", "Sus expedientes de siniestro, en un servidor a nombre de su empresa."),
                   ("La IA lee", "Separa y clasifica cada documento, y extrae póliza, asegurado, fechas y montos."),
                   ("Folia y registra", "Numera cada página con su huella digital y deja todo en una auditoría que nadie puede alterar.")],
                   "CAT 0045-2023 · SINIESTRO · 12/08/2023")},
        "c2": {"asuntos": ["PUBLICIDAD | El siniestro que se paga tarde por una hoja",
                           "PUBLICIDAD | Trazabilidad sin foliar a mano"],
               "pre": "Un documento que falta demora el pago y el cliente se lo cobra a usted.",
               "kicker": "Expedientes de siniestro",
               "titular": ("El siniestro que se paga", "tarde por una hoja"),
               "banner": ("validando.jpg", "Persona revisando un expediente digital en pantalla", "1 hoja",
                          "que falta en un expediente de siniestro demora el pago. Y el asegurado no culpa a la norma: culpa a quien le atiende el seguro.", None),
               "parrafos": ["Ese reclamo puede terminar en el regulador. Y una respuesta tardía cuesta más que el tiempo de buscar el documento."],
               "pregunta": "¿Cuántos expedientes de {{organizacion}} están hoy incompletos sin que nadie lo sepa?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("Cada documento del siniestro se ordena y folia a mano.", "La IA lo clasifica y numera cada página con su huella."),
                   ("Buscar una póliza o un comprobante toma tiempo.", "Aparece en segundos por póliza, asegurado o fecha."),
                   ("La trazabilidad depende de registros sueltos.", "Una auditoría inmutable dice quién hizo qué. Y se conecta por API con su sistema.")])},
        "c3": c3("Seguros · expedientes", "reunion.jpg", "Nov. 2026",
                 "la trazabilidad con documentos deja de ser opcional para las AFOCAT.", None,
                 "Un expediente incompleto o difícil de encontrar demora un pago, una respuesta al cliente o un requerimiento de la SBS.",
                 "¿Su archivo está listo para el primer requerimiento?"),
    },
    "educacion": {
        "nombre": "Universidades y colegios profesionales", "sensible": False,
        "segmento": "Universidades e institutos privados, colegios profesionales",
        "c1": {"asuntos": ["PUBLICIDAD | El egresado que necesita su certificado para el viernes",
                           "PUBLICIDAD | Un legajo de 2009, en segundos"],
               "pre": "La urgencia es del egresado; la queja, de la institución.",
               "kicker": "Para universidades y colegios profesionales",
               "titular": ("Un certificado de 2009,", "para el viernes"),
               "banner": ("archivera.jpg", "Archivera buscando legajos en una caja de archivo", "Viernes",
                          "es el plazo que le dan a un egresado de 2009 para presentar su certificado de estudios en un nuevo trabajo.", None),
               "parrafos": ["En muchas instituciones eso significa bajar al archivo central, buscar las actas de ese año y armar el documento a mano. Si el acta está incompleta o dañada, la urgencia es del egresado. La queja, y a veces el reclamo formal, es para la institución."],
               "pregunta": "En {{organizacion}}, ¿cuántos días tarda hoy una constancia de hace quince años?",
               "bloque": ("pasos", "Así lo resuelve Arriera", [
                   ("Digitaliza", "Actas, legajos y expedientes del archivo central, en un servidor a nombre de su institución."),
                   ("La IA lee", "Nombre, código, DNI y fechas quedan indexados sin tipear."),
                   ("Atiende con plazo", "El legajo aparece en segundos, y cada constancia sale con plazo, historial y entrega registrada.")],
                   "COD 2009-1043 · ACTA · CICLO 2009-II")},
        "c2": {"asuntos": ["PUBLICIDAD | Educación, entre los sectores que más fiscaliza la ANPD",
                           "PUBLICIDAD | Los legajos de sus alumnos también son datos personales"],
               "pre": "Dos universidades ya fueron sancionadas por el uso de datos personales.",
               "kicker": "Datos personales de alumnos y colegiados",
               "titular": ("Educación está en la mira", "de la ANPD"),
               "banner": ("escaner-2.jpg", "Persona digitalizando legajos con un escáner", "Top 4",
                          "educación está entre los cuatro sectores que más fiscaliza en 2026 la autoridad de datos personales. Cada infracción puede llegar a 100 UIT.",
                          "LexLatin, 2026, y gob.pe (MINJUSDH)."),
               "parrafos": ["El Ministerio de Justicia ya sancionó a dos universidades por usar datos personales sin consentimiento. Y un archivo central en papel es difícil de defender ante una fiscalización: cualquiera con la llave ve todo, y nadie puede decir quién consultó qué."],
               "pregunta": "¿Quién puede entrar hoy al archivo central de {{organizacion}}, y queda registro?",
               "bloque": ("antes", "Lo que cambia con Arriera", [
                   ("El legajo se busca carpeta por carpeta.", "Se escribe el nombre, el código o el DNI y se abre el documento exacto."),
                   ("Cada constancia se arma a mano, sin plazo visible.", "Sale con plazo, historial y entrega registrada."),
                   ("Cualquiera con la llave del archivo ve todo.", "Permisos por área y registro de cada acceso. Y se conecta por API con su sistema académico.")])},
        "c3": c3("Universidades · archivo central", "reunion.jpg", "+1 promoción",
                 "suma cajas al archivo central cada año.", None,
                 "Y cada constancia urgente depende de que alguien encuentre la carpeta a tiempo, mientras los datos de miles de alumnos siguen en estantes sin registro de acceso.",
                 "¿Cuánto tiempo más puede sostener eso su archivo central?"),
    },
}

ASUNTO_B_C3 = {"salud": "PUBLICIDAD | Última nota sobre sus historias", "notarias": "PUBLICIDAD | Su protocolo le va a sobrevivir",
               "fondos": "PUBLICIDAD | Última nota sobre su archivo", "estudios": "PUBLICIDAD | Última nota sobre su archivo",
               "seguros": "PUBLICIDAD | Última nota sobre sus expedientes", "educacion": "PUBLICIDAD | Última nota sobre su archivo central"}
for _k, _s in SECTORES.items():
    _s["c3"]["asuntos"][1] = ASUNTO_B_C3[_k]

PERFIL_A_SECTOR = {
    "Fondo / mutual / cooperativa": "fondos", "Notaría": "notarias", "Clínica / hospital privado": "salud",
    "Laboratorio / diagnóstico": "salud", "Estudio de abogados": "estudios", "Estudio contable": "estudios",
    "Aseguradora / corredor": "seguros", "Universidad / instituto privado": "educacion", "Colegio profesional": "educacion",
}

# Días hábiles después del correo anterior; los correos 2 y 3 solo salen si no hubo respuesta.
TIEMPOS = [(0, None), (3, "if_no_reply"), (5, "if_no_reply")]


def armar(c, sensible):
    filas = [cabecera(), titular(c["kicker"], *c["titular"]), banner(*c["banner"]), cuerpo(c["parrafos"]), pregunta(c["pregunta"])]
    b = c["bloque"]
    if b[0] == "pasos":
        filas.append(seccion(b[1], pasos(b[2], b[3])))
    elif b[0] == "antes":
        filas.append(seccion(b[1], antes_despues(b[2])))
    else:
        filas.append(seccion(b[1], opciones()))
    filas += [oferta(sensible, "Agendar la demo" if b[0] == "opciones" else "Agendar la demo por WhatsApp"), firma(), pie()]
    return html(c["pre"], filas)


def secuencias():
    out = []
    for clave, s in SECTORES.items():
        pasos_ = []
        for i, k in enumerate(("c1", "c2", "c3")):
            c = s[k]
            pasos_.append({"orden": i + 1, "asunto": c["asuntos"][0], "asunto_b": c["asuntos"][1], "pre": c["pre"],
                           "html": armar(c, s["sensible"]), "dias": TIEMPOS[i][0], "condicion": TIEMPOS[i][1]})
        out.append({"clave": clave, "nombre": f"Arriera · {s['nombre']} · 3 correos", "segmento": s["segmento"], "pasos": pasos_})
    return out
