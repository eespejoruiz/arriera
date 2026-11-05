// Cliente de la API de Arriera. Si NEXT_PUBLIC_API_URL no está definida, la web funciona en modo demo (sin servidor).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
export const modoDemo = API_URL === "";

export class ErrorApi extends Error {
  constructor(public estado: number, mensaje: string) { super(mensaje); }
}

export async function api<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const r = await fetch(`${API_URL}${ruta}`, {
    ...opciones,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(opciones.headers ?? {}) },
  });
  if (r.status === 204) return undefined as T;
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new ErrorApi(r.status, typeof datos.detail === "string" ? datos.detail : "No se pudo completar la acción. Intenta de nuevo.");
  return datos as T;
}

export type PasoIngreso = "listo" | "verificar_2fa" | "configurar_2fa";
export const ingresar = (email: string, password: string) =>
  api<{ paso: PasoIngreso; mensaje: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const configurar2fa = () => api<{ uri: string; secreto: string; qr_svg: string }>("/auth/2fa/configurar", { method: "POST" });
export const verificar2fa = (codigo: string) =>
  api<{ paso: PasoIngreso }>("/auth/2fa/verificar", { method: "POST", body: JSON.stringify({ codigo }) });

// ---------- Sesión ----------
export type Yo = { id: string; email: string; name: string; roles: string[]; requiere_2fa: boolean };
export const yo = () => api<Yo>("/auth/me");
export const salir = () => api<void>("/auth/logout", { method: "POST" });

// ---------- Inventario y captura ----------
export type Caja = { code: string; shelf_location: string | null; anios: string; series_hint: string | null; paper_condition: string; estimated_pages: number | null; captured_pages: number; status: string };
export type PaginaLote = { id: string; indice: number; estado: string; motivo: string | null; inclinacion: number | null; ocr?: string; idioma?: string | null };
export type Lote = { code: string; caja: string; origen: string; estado: string; recibidas: number; esperadas: number | null; creado: string; rechazos: number; paginas?: PaginaLote[] | null; ia?: IaLote | null; microformas?: boolean };
export const cajas = () => api<Caja[]>("/cajas");
export const crearCaja = (c: Partial<Caja> & { code: string; year_from?: number; year_to?: number }) => api<Caja>("/cajas", { method: "POST", body: JSON.stringify(c) });
export const lotes = () => api<Lote[]>("/captura/lotes");
export const lote = (code: string) => api<Lote>(`/captura/lotes/${code}`);
export const crearLote = (caja: string, origen = "celular", microformas = false) => api<Lote>("/captura/lotes", { method: "POST", body: JSON.stringify({ caja, origen, microformas }) });
export const emparejar = (code: string) => api<{ url: string; qr_svg: string; vence: string }>(`/captura/lotes/${code}/emparejar`, { method: "POST" });
export const urlHoja = (code: string) => `${API_URL}/captura/lotes/${code}/hoja.pdf`;
export const urlEtiqueta = (code: string) => `${API_URL}/cajas/${code}/etiqueta.pdf`;
export const urlMiniatura = (id: string) => `${API_URL}/captura/paginas/${id}/miniatura`;
export const urlPdfLote = (code: string) => `${API_URL}/captura/lotes/${code}/buscable.pdf`;

// Búsqueda (Sprint 2)
export type ResultadoBusqueda = { pagina_id: string; lote: string; caja: string; indice: number; idioma: string | null; confianza: number | null; fragmento: string | null; rango: number };
export type Faceta = { valor: string; n: number };
export type Busqueda = { consulta: string; total: number; pagina: number; resultados: ResultadoBusqueda[]; facetas: { cajas: Faceta[]; idiomas: Faceta[] }; marcas: [string, string] };
export type Caja01 = { x0: number; y0: number; x1: number; y1: number };
export type PaginaVista = { pagina_id: string; lote: string; caja: string; indice: number; total_paginas: number; ancho: number | null; alto: number | null; idioma: string | null; confianza: number | null; manuscrito: number | null; ocr: string; texto: string; resaltes: Caja01[] };
export type ResumenProceso = { proveedor_activo: string; paginas_por_estado: Record<string, number>; errores: number; proveedores: { proveedor: string; paginas: number; costo_usd: number; usd_por_mil: number; segundos_por_pagina: number }[] };
export const buscar = (p: Record<string, string>) => api<Busqueda>(`/busqueda?${new URLSearchParams(p)}`);
export const verPagina = (id: string, q: string) => api<PaginaVista>(`/busqueda/paginas/${id}?${new URLSearchParams({ q })}`);
export const urlImagenPagina = (id: string) => `${API_URL}/busqueda/paginas/${id}/imagen`;
export const urlMiniaturaBusqueda = (id: string) => `${API_URL}/busqueda/paginas/${id}/miniatura`;
export const resumenProceso = () => api<ResumenProceso>("/procesamiento/resumen");
export const reprocesarOcr = (code: string) => api<{ en_cola: number }>(`/procesamiento/lotes/${code}/ocr`, { method: "POST" });
// Documentos y validación (Sprint 3)
export type IaLote = { estado: string; motivo: string | null; documentos: number; costo_usd: number };
export type PaginaDoc = { id: string; indice: number; orden: number };
export type DocResumen = { id: string; titulo: string; tipo: string; tipo_nombre: string; serie: string; sensibilidad: string; estado: string; fecha: string | null; confianza_tipo: number | null; confianza: number | null; lote: string | null; caja: string | null; paginas: PaginaDoc[]; pendientes: number; persona: boolean; prioridad?: number };
export type CampoDoc = { key: string; nombre: string; tipo: string; opciones: string[] | null; requerido: boolean; sensible: boolean; id: string | null; valor: string | null; original: string | null; confianza: number | null; estado: string; nota: string | null; pagina: number | null; caja: (Caja01 & { pagina: number | null }) | null; evidencia: string | null; fuente: string | null };
export type TareaDoc = { id: string; tipo: "campo" | "clasificacion" | "separacion"; documento: string; campo: string | null; prioridad: number; motivo: string };
export type DocDetalle = DocResumen & { evidencia_tipo: { frase: string; pagina: number }[]; campos: CampoDoc[]; tareas: TareaDoc[]; tipos: { key: string; nombre: string }[] };
export type Cola = { documentos: DocResumen[]; tareas: number; total_documentos: number; validados: number };
export const colaValidacion = () => api<Cola>("/validacion/cola");
export const documento = (id: string) => api<DocDetalle>(`/documentos/${id}`);
export const resolverTarea = (id: string, cuerpo: { accion: string; valor?: string; tipo?: string }) =>
  api<{ documento: string; estado: string; pendientes?: number }>(`/validacion/tareas/${id}`, { method: "POST", body: JSON.stringify(cuerpo) });
// Microformas y cumplimiento (Sprint 3)
export type PasoMf = { paso: string; nombre: string; roles: string[]; hecho: boolean; por: string | null; rol: string | null; fecha: string | null };
export type EstadoMf = { lote: string; microformas: boolean; pasos: PasoMf[]; siguiente: string | null; paginas_bajo_300dpi: number; hash_manifiesto: string | null; actas: { id: string; tipo: string; numero: string; sha256: string }[] };
export const estadoMicroformas = (code: string) => api<EstadoMf>(`/microformas/lotes/${code}`);
export const registrarPaso = (code: string, paso: string, notas?: string) => api<EstadoMf>(`/microformas/lotes/${code}/pasos/${paso}`, { method: "POST", body: JSON.stringify({ notas: notas || null }) });
export const urlActa = (id: string) => `${API_URL}/microformas/actas/${id}.pdf`;
export type AccesoSensible = { fecha: string; usuario: string; correo: string; accion: string; documento: string; lote: string; documento_id: string; ip: string };
export const accesosSensibles = (dias: number) => api<{ dias: number; total: number; por_usuario: { usuario: string; accesos: number }[]; accesos: AccesoSensible[] }>(`/cumplimiento/accesos-sensibles?dias=${dias}`);
export const urlAccesosCsv = (dias: number) => `${API_URL}/cumplimiento/accesos-sensibles?dias=${dias}&formato=csv`;
export type VerifCadena = { integra: boolean; eventos: number; ultimo_hash: string | null; primer_error_id: number | null; motivo: string | null };
export const verificarCadena = () => api<VerifCadena>("/audit/verify-chain");
// ---------- Importación de archivos ya digitales ----------
export async function importarArchivo(code: string, archivo: File): Promise<{ paginas: number[]; duplicado: boolean }> {
  const fd = new FormData();
  fd.append("archivo", archivo);
  const r = await fetch(`${API_URL}/captura/lotes/${code}/importar`, { method: "POST", body: fd, credentials: "include" });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new ErrorApi(r.status, typeof datos.detail === "string" ? datos.detail : "No se pudo importar el archivo.");
  return datos;
}

// ---------- Solicitudes de copia y de acceso ----------
export type SolicitudResumen = { id: string; numero: string; tipo: string; tipo_nombre: string; estado: string; estado_nombre: string; solicitante: string; relacion: string | null; recibida: string; vence: string; dias_habiles: number | null; documentos: number; entregada: string | null };
export type SolicitudDetalle = SolicitudResumen & { documento: string | null; contacto: string | null; detalle: string | null; plazo_dias: number; items: DocResumen[]; sugeridos: DocResumen[]; ocultamiento: string; copia: { paginas: number; sha256: string } | null; nota_entrega: string | null; historial: { fecha: string; accion: string; por: string; detalle: string | null }[] };
export type TiposSolicitud = { tipos: { key: string; nombre: string; plazo_dias: number }[]; ocultamientos: { key: string; nombre: string }[] };
export const tiposSolicitud = () => api<TiposSolicitud>("/solicitudes/tipos");
export const solicitudes = (estado = "") => api<SolicitudResumen[]>(`/solicitudes${estado ? `?estado=${estado}` : ""}`);
export const solicitud = (id: string) => api<SolicitudDetalle>(`/solicitudes/${id}`);
export const crearSolicitud = (c: { tipo: string; solicitante: string; documento?: string; contacto?: string; relacion?: string; detalle?: string }) =>
  api<SolicitudDetalle>("/solicitudes", { method: "POST", body: JSON.stringify(c) });
export const agregarASolicitud = (id: string, documento_id: string) => api<SolicitudDetalle>(`/solicitudes/${id}/documentos`, { method: "POST", body: JSON.stringify({ documento_id }) });
export const quitarDeSolicitud = (id: string, did: string) => api<SolicitudDetalle>(`/solicitudes/${id}/documentos/${did}`, { method: "DELETE" });
export const generarCopia = (id: string, ocultamiento: string) => api<SolicitudDetalle>(`/solicitudes/${id}/copia`, { method: "POST", body: JSON.stringify({ ocultamiento }) });
export const cambiarEstadoSolicitud = (id: string, estado: string, nota?: string) => api<SolicitudDetalle>(`/solicitudes/${id}/estado`, { method: "POST", body: JSON.stringify({ estado, nota: nota || null }) });
export const urlCopiaSolicitud = (id: string) => `${API_URL}/solicitudes/${id}/copia.pdf`;
export const buscarDocumentos = (q: string) => api<DocResumen[]>(`/documentos?${new URLSearchParams({ q })}`);

export const svgComoImagen = (svg: string) => `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;

// ---------- Dispositivo (celular) ----------
export type LoteEstacion = { lote: string; caja: string; estado: string; paginas: { indice: number; estado: string; motivo: string | null }[] };
export async function apiEstacion<T>(ruta: string, llave: string, opciones: RequestInit = {}): Promise<T> {
  const r = await fetch(`${API_URL}${ruta}`, { ...opciones, headers: { "X-Station-Key": llave, ...(opciones.headers ?? {}) } });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new ErrorApi(r.status, typeof datos.detail === "string" ? datos.detail : "No se pudo enviar. Se reintentará.");
  return datos as T;
}
export const canjearCodigo = (token: string, modelo: string) =>
  api<LoteEstacion & { llave: string }>("/estacion/emparejar", { method: "POST", body: JSON.stringify({ token, modelo, plataforma: "web" }) });
