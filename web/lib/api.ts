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
