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
export type Lote = { code: string; caja: string; origen: string; estado: string; recibidas: number; esperadas: number | null; creado: string; rechazos: number; paginas?: PaginaLote[] | null };
export const cajas = () => api<Caja[]>("/cajas");
export const crearCaja = (c: Partial<Caja> & { code: string; year_from?: number; year_to?: number }) => api<Caja>("/cajas", { method: "POST", body: JSON.stringify(c) });
export const lotes = () => api<Lote[]>("/captura/lotes");
export const lote = (code: string) => api<Lote>(`/captura/lotes/${code}`);
export const crearLote = (caja: string, origen = "celular") => api<Lote>("/captura/lotes", { method: "POST", body: JSON.stringify({ caja, origen }) });
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
