"""Prompts versionados (spec, anexo C). Cambiar una versión exige correr `make eval` antes."""

VERSION = "v1"

SISTEMA = (
    "Eres un archivero experto en documentos administrativos y médicos del Perú. "
    "Respondes solo con la herramienta indicada. Nunca inventas ni deduces datos que no estén en el texto."
)

SEPARACION = """Recibes páginas consecutivas de un lote escaneado, con su texto OCR resumido y señales.
Indica en qué páginas EMPIEZA un documento nuevo. Señales de inicio: encabezados de formulario, títulos
("SOLICITUD", "INFORME MÉDICO", "BOLETA DE PAGO"), numeración "1 de N", cambio de persona o DNI, cambio de formato.
Una página de continuación suele tener "2 de N", texto que sigue de la anterior o solo firmas.
{contexto}Decide solo para estas páginas:
{paginas}"""

CLASIFICACION = """Clasifica el documento en UNO de los tipos del catálogo. Si ninguno aplica, usa "otro".

Catálogo (clave: nombre · señales típicas):
{catalogo}

Texto OCR del documento (páginas {desde}-{hasta}):
<<<
{texto}
>>>

Devuelve: tipo, confianza (0 a 1) y evidencia (máximo 3 frases cortas copiadas del texto, con su página)."""

EXTRACCION = """Extrae los campos del tipo "{tipo}". Reglas:
1) Copia el valor tal como aparece (valor_original) y devuelve también el valor normalizado (valor).
2) Si el dato no está o no es legible, devuelve null. Está prohibido inventar o deducir datos.
3) Indica la página y la frase exacta de donde sale cada dato.
4) Confianza de 0 a 1: baja si la letra es manuscrita, borrosa o hay más de un candidato.
Normalización: DNI de 8 dígitos; fechas en ISO (AAAA-MM-DD); montos en soles con punto decimal y sin separador
de miles (1250.00); enteros sin texto; nombres con mayúscula inicial, sin agregar tildes que no estén.

Campos:
{campos}

Texto OCR con páginas:
<<<
{texto}
>>>"""

TIPOS_CAMPO = {
    "dni": "DNI, 8 dígitos",
    "date": "fecha ISO AAAA-MM-DD",
    "money_pen": "monto en soles, decimal con punto",
    "integer": "número entero",
    "person_name": "nombre de persona",
    "string": "texto corto",
    "text": "texto",
    "enum": "una de las opciones",
}
