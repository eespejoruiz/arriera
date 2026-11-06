// DATOS DEMO · sintéticos. Nombres, DNI y documentos ficticios. Nunca datos reales.

// Demo pública (arriera.tech/demo/): sin login, con un cliente genérico y marca Arriera.
export const demoPublica = process.env.NEXT_PUBLIC_DEMO_PUBLICA === "1";
export const BASE = process.env.NEXT_PUBLIC_BASE_PATH || "";
export const cliente = demoPublica
  ? { nombre: "Organización Demo", corto: "OD", detalle: "DATOS DEMO · todo es ficticio", dominio: "organizacion.demo" }
  : { nombre: "FAMENSSALUD", corto: "FS", detalle: "Licencia de uso · demostración", dominio: "famenssalud.demo" };

export const resumen = {
  capturadas: 48210, estimadas: 112000, hoy: 3912, ayer: 3480, autoAceptados: 91, pendientes: 214,
  tiempoValidacion: "38 s", reescaneo: 2.1, costoMes: 41.2, presupuesto: 120, terminoEstimado: "19/12/2026",
  porDia: [2100, 2650, 2980, 3120, 2870, 3300, 3410, 3050, 3620, 3480, 3912],
  dias: ["20/10", "21/10", "22/10", "23/10", "24/10", "27/10", "28/10", "29/10", "30/10", "31/10", "03/11"],
  porSerie: [
    { serie: "Beneficios", paginas: 21840, validados: 94 },
    { serie: "Asociados", paginas: 12310, validados: 97 },
    { serie: "Préstamos", paginas: 8120, validados: 89 },
    { serie: "Aportes", paginas: 4210, validados: 96 },
    { serie: "Gobierno", paginas: 1730, validados: 99 },
  ],
};

export type EstadoDisp = "on" | "warn" | "off";
export const dispositivos = [
  { id: "est-1", tipo: "escaner", nombre: "Ricoh fi-8170", detalle: "USB en Estación Archivo 1 (Windows 11)", estado: "on" as EstadoDisp, nota: "Escaneando lote L-2026-000187", via: "Agente de captura 1.4.2" },
  { id: "est-2", tipo: "escaner", nombre: "Ricoh fi-8170", detalle: "USB en Estación Archivo 2 (Windows 11)", estado: "on" as EstadoDisp, nota: "Libre", via: "Agente de captura 1.4.2" },
  { id: "mfp-1", tipo: "red", nombre: "Multifuncional Ricoh IM 430", detalle: "Red, 2.º piso · escanea a carpeta SMB", estado: "on" as EstadoDisp, nota: "Último archivo hace 12 min", via: "Carpeta \\\\arriera\\entrada-red" },
  { id: "cel-1", tipo: "celular", nombre: "Samsung Galaxy A54", detalle: "Rosa M. · Captura", estado: "on" as EstadoDisp, nota: "2 lotes hoy · 86 páginas", via: "App web emparejada por QR" },
  { id: "cel-2", tipo: "celular", nombre: "iPhone 13", detalle: "Mesa de partes", estado: "off" as EstadoDisp, nota: "Sin conexión hace 2 h", via: "App web emparejada por QR" },
  { id: "qr-1", tipo: "pistola", nombre: "Lector Honeywell Voyager 1450g", detalle: "USB en Estación Archivo 1", estado: "on" as EstadoDisp, nota: "Última lectura: caja C-0045", via: "Teclado HID" },
];

export type EstadoLote = "recibiendo" | "procesando" | "con_rechazos" | "procesado" | "cerrado";
export const lotes = [
  { codigo: "L-2026-000187", caja: "C-0047", operador: "Julio P.", origen: "Ricoh fi-8170 · Estación 1", paginas: 164, esperadas: 220, estado: "recibiendo" as EstadoLote, hora: "11:42" },
  { codigo: "L-2026-000186", caja: "C-0046", operador: "Rosa M.", origen: "Samsung Galaxy A54", paginas: 41, esperadas: 41, estado: "procesando" as EstadoLote, hora: "11:20" },
  { codigo: "L-2026-000185", caja: "C-0046", operador: "Julio P.", origen: "Ricoh fi-8170 · Estación 2", paginas: 212, esperadas: 212, estado: "con_rechazos" as EstadoLote, hora: "10:55", rechazos: 3 },
  { codigo: "L-2026-000184", caja: "C-0045", operador: "Carmen L.", origen: "Multifuncional IM 430", paginas: 96, esperadas: 96, estado: "procesado" as EstadoLote, hora: "10:12" },
  { codigo: "L-2026-000183", caja: "C-0045", operador: "Julio P.", origen: "Ricoh fi-8170 · Estación 1", paginas: 208, esperadas: 208, estado: "cerrado" as EstadoLote, hora: "09:31" },
  { codigo: "L-2026-000182", caja: "C-0044", operador: "Rosa M.", origen: "Samsung Galaxy A54", paginas: 45, esperadas: 45, estado: "cerrado" as EstadoLote, hora: "09:05" },
];
export const estadoLote: Record<EstadoLote, { t: string; c: string }> = {
  recibiendo: { t: "Recibiendo", c: "info" }, procesando: { t: "Procesando con IA", c: "info" },
  con_rechazos: { t: "Reescanear 3 páginas", c: "duda" }, procesado: { t: "Procesado", c: "ok" }, cerrado: { t: "Cerrado con acta", c: "neutro" },
};
export const rechazos = [
  { pagina: 38, motivo: "Torcida 12°", lote: "L-2026-000185" },
  { pagina: 117, motivo: "Borrosa", lote: "L-2026-000185" },
  { pagina: 164, motivo: "Cortada en el borde", lote: "L-2026-000185" },
];

export const cajas = [
  { codigo: "C-0044", estante: "B-2", anios: "2016–2017", serie: "Beneficios", estimadas: 2300, capturadas: 2300, estado: "Devuelta" },
  { codigo: "C-0045", estante: "B-3", anios: "2017–2018", serie: "Beneficios", estimadas: 2200, capturadas: 2180, estado: "Capturada" },
  { codigo: "C-0046", estante: "B-3", anios: "2018", serie: "Beneficios", estimadas: 2400, capturadas: 1340, estado: "En captura" },
  { codigo: "C-0047", estante: "B-4", anios: "2018–2019", serie: "Préstamos", estimadas: 2100, capturadas: 164, estado: "En captura" },
];

export const tareas = [
  { id: "v-1", tipo: "Campo dudoso", doc: "Solicitud de subsidio", exp: "2018-0412", detalle: "Monto solicitado · 82%", prioridad: "Alta" },
  { id: "v-2", tipo: "Manuscrito crítico", doc: "Informe médico", exp: "2018-0412", detalle: "Diagnóstico · siempre se valida", prioridad: "Alta" },
  { id: "v-3", tipo: "Separación dudosa", doc: "Lote L-2026-000185", exp: "—", detalle: "Páginas 54 y 55 · 64%", prioridad: "Media" },
  { id: "v-4", tipo: "Posible duplicado", doc: "Boleta de pago 03/2019", exp: "2019-0088", detalle: "Huella visual 94% similar", prioridad: "Media" },
  { id: "v-5", tipo: "Asignar a expediente", doc: "Certificado médico", exp: "¿2018-0377?", detalle: "Sin DNI legible · nombre 88%", prioridad: "Baja" },
];

export const campos = [
  { k: "Nombre del titular", v: "Rosa Huamán Quispe", c: 98, ok: true },
  { k: "DNI", v: "4•••••18", c: 99, ok: true },
  { k: "Código de asociada", v: "AS-02231", c: 96, ok: true },
  { k: "Fecha de solicitud", v: "14/03/2018", c: 96, ok: true },
  { k: "Tipo de subsidio", v: "Enfermedad", c: 95, ok: true },
  { k: "Monto solicitado", v: "S/ 1,250.00", c: 82, ok: false },
];

export const expediente = {
  codigo: "2018-0412", titular: "Rosa Huamán Quispe", dni: "4•••••18", tramite: "Subsidio por enfermedad", estado: "Cerrado",
  abierto: "14/03/2018", cerrado: "02/05/2018", caja: "C-0045", estante: "B-3", serie: "Beneficios › Subsidio por enfermedad",
  documentos: [
    { id: "d-1", fecha: "14/03/2018", tipo: "Solicitud de subsidio", paginas: 2, estado: "ok", sens: "N2" },
    { id: "d-2", fecha: "02/03/2018", tipo: "Informe médico", paginas: 3, estado: "ok", sens: "N3", nota: "Página 6 del lote" },
    { id: "d-3", fecha: "02/03/2018", tipo: "Certificado médico (CITT)", paginas: 1, estado: "duda", sens: "N3" },
    { id: "d-4", fecha: "02/05/2018", tipo: "Resolución de aprobación", paginas: 1, estado: "ok", sens: "N2" },
  ],
  requisitos: [
    { t: "Solicitud", ok: true }, { t: "Informe o certificado médico", ok: true }, { t: "Boleta de pago", ok: false }, { t: "Resolución", ok: true },
  ],
};

export const resultados = [
  { exp: "2018-0412", titular: "Rosa Huamán Quispe", caja: "C-0045", docs: [["ok", "Solicitud"], ["ok", "Informe médico, pág. 6"], ["falta", "Falta boleta de pago"]], campo: ["Monto solicitado", "S/ 1,250.00", "82% · validar"] },
  { exp: "2018-0377", titular: "Julia Ccori Mamani", caja: "C-0044", docs: [["ok", "Solicitud"], ["ok", "Certificado médico"], ["falta", "Falta boleta de pago"]], campo: ["DNI", "4•••••07", "99%"] },
  { exp: "2018-0519", titular: "Luis Tito Ramos", caja: "C-0047", docs: [["ok", "Solicitud"], ["falta", "Falta boleta de pago"]], campo: ["Fecha de solicitud", "21/06/2018", "96%"] },
];

export const auditoria = [
  { hora: "11:46:02", quien: "Carmen L.", rol: "Consulta", accion: "Vio la página", objeto: "Informe médico · Exp. 2018-0412 · pág. 6", ip: "10.20.1.14", hash: "9f3a…e21c" },
  { hora: "11:45:40", quien: "Asistente", rol: "IA", accion: "Respondió con 3 citas", objeto: "«subsidios 2018 sin boleta»", ip: "—", hash: "41b0…7d9a" },
  { hora: "11:44:13", quien: `Odoo ${cliente.nombre}`, rol: "Integración", accion: "Consultó documentos", objeto: "res.partner/1842", ip: "10.20.1.40", hash: "c27e…0b55" },
  { hora: "11:41:58", quien: "Luis V.", rol: "Validador", accion: "Corrigió un campo", objeto: "Monto: S/ 1,280.00 → S/ 1,250.00", ip: "10.20.1.22", hash: "e8d1…a310" },
  { hora: "11:38:20", quien: "Estación Archivo 1", rol: "Captura", accion: "Subió archivo verificado", objeto: "L-2026-000187 · SHA-256 5c1e…", ip: "10.20.1.31", hash: "07aa…f4c2" },
  { hora: "11:30:05", quien: "Rosa M.", rol: "Operadora", accion: "Emparejó un celular", objeto: "Samsung Galaxy A54", ip: "10.20.1.57", hash: "b9e4…2210" },
  { hora: "11:02:47", quien: "Ana R.", rol: "Archivera", accion: "Exportó con ocultamiento", objeto: "3 documentos · perfil «DNI y diagnóstico»", ip: "10.20.1.12", hash: "5d70…9ce1" },
];

export const depuracion = {
  numero: "Propuesta 2026-11", estado: "En revisión", total: 1240, excluidos: 18,
  grupos: [
    { serie: "Administración › Comprobantes", regla: "10 años desde la fecha · eliminar papel y digital", docs: 812, cajas: "C-0003 a C-0011" },
    { serie: "Correspondencia › Recibida", regla: "5 años · eliminar papel, conservar digital", docs: 410, cajas: "C-0012 a C-0015" },
    { serie: "Préstamos › Cronogramas", regla: "Cancelado + 5 años · eliminar papel", docs: 18, cajas: "C-0021", bloqueo: "18 con bloqueo legal (en litigio)" },
  ],
};

export const integraciones = [
  { nombre: `Odoo ${cliente.nombre}`, sistema: "Odoo 17", estado: "on" as EstadoDisp, llamadas: "4,812 hoy", techo: "Contabilidad, Aportes y Préstamos hasta N2", ultima: "hace 1 min" },
  { nombre: "Starsoft Contabilidad", sistema: "Agente puente · SQL Server", estado: "warn" as EstadoDisp, llamadas: "Sincroniza cada 15 min", techo: "Contabilidad hasta N1", ultima: "hace 14 min" },
];
export const webhooks = [
  { url: `https://erp.${cliente.dominio}/arriera/webhook`, eventos: "documento.indexado, documento.validado, expediente.requisito_faltante", ok: "99.8%", ult: "200 · hace 1 min" },
];
