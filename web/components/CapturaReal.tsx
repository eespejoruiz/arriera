"use client";
import { useCallback, useEffect, useState } from "react";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import {
  cajas as apiCajas, crearCaja, crearLote, emparejar, ErrorApi, lote as apiLote, lotes as apiLotes,
  svgComoImagen, urlEtiqueta, urlHoja, urlMiniatura, urlPdfLote, yo, type Caja, type Lote,
} from "@/lib/api";

const estadoLote: Record<string, [string, string]> = {
  creado: ["Esperando páginas", "neutro"], recibiendo: ["Recibiendo", "info"], procesando: ["Revisando calidad", "info"],
  con_rechazos: ["Hay páginas por repetir", "duda"], procesado: ["Listo", "ok"], cerrado: ["Cerrado", "neutro"],
};
const estadoPagina: Record<string, [string, string]> = {
  pendiente: ["Revisando", "neutro"], ok: ["Bien", "ok"], corregida: ["Enderezada", "ok"], reescanear: ["Repetir", "falta"], en_blanco: ["En blanco", "neutro"],
};
const hora = (iso: string) => new Date(iso).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });

export default function CapturaReal() {
  const [lista, setLista] = useState<Lote[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  useEffect(() => { yo().then((u) => setRoles(u.roles)).catch(() => {}); }, []);
  const puedePdf = roles.some((r) => r === "admin" || r === "archivero");
  const [cajas, setCajas] = useState<Caja[]>([]);
  const [sel, setSel] = useState<Lote | null>(null);
  const [modal, setModal] = useState<"lote" | "caja" | null>(null);
  const [nuevo, setNuevo] = useState<{ lote: Lote; qr?: string; vence?: string } | null>(null);
  const [cajaElegida, setCajaElegida] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const [l, c] = await Promise.all([apiLotes(), apiCajas()]);
      setLista(l); setCajas(c);
      setCajaElegida((x) => x || c[0]?.code || "");
      if (sel) setSel(await apiLote(sel.code));
    } catch (e) { if (e instanceof ErrorApi && e.estado === 403) setError("Tu perfil no tiene acceso a Captura."); }
  }, [sel]);
  useEffect(() => { cargar(); const i = setInterval(cargar, 5000); return () => clearInterval(i); }, [cargar]);

  const nuevoLote = async () => {
    setError("");
    try {
      const l = await crearLote(cajaElegida, "celular");
      const e = await emparejar(l.code);
      setNuevo({ lote: l, qr: svgComoImagen(e.qr_svg), vence: e.vence });
      cargar();
    } catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo crear el lote."); }
  };
  const nuevoQr = async (l: Lote) => {
    const e = await emparejar(l.code);
    setNuevo({ lote: l, qr: svgComoImagen(e.qr_svg), vence: e.vence }); setModal("lote");
  };
  const registrarCaja = async (ev: React.FormEvent<HTMLFormElement>) => {
    ev.preventDefault(); setError("");
    const f = new FormData(ev.currentTarget);
    try {
      await crearCaja({
        code: String(f.get("code")).toUpperCase(), shelf_location: String(f.get("estante") || "") || null,
        year_from: Number(f.get("desde")) || undefined, year_to: Number(f.get("hasta")) || undefined,
        series_hint: String(f.get("serie") || "") || null, estimated_pages: Number(f.get("estimadas")) || null,
      });
      setModal(null); cargar();
    } catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo registrar la caja."); }
  };

  return (
    <>
      <Cab titulo="Captura" maq="cada hoja entra con su caja y su lote" desc="Crea un lote, empareja un celular con el QR y mira llegar las páginas con su control de calidad.">
        <button className="btn btn-sec" onClick={() => { setError(""); setModal("caja"); }}><Icono n="caja" />Registrar caja</button>
        <button className="btn btn-prim" onClick={() => { setError(""); setNuevo(null); setModal("lote"); }} disabled={!cajas.length}><Icono n="mas" />Nuevo lote</button>
      </Cab>
      {error && !modal && <p className="error-form">{error}</p>}
      {!cajas.length && <div className="aviso"><Icono n="caja" /><span>Primero registra una caja del archivo. Cada lote pertenece a una caja.</span></div>}

      <div className="rejilla r-73">
        <div className="panel">
          <div className="panel-cab"><h2>Lotes</h2><span className="sub">se actualiza cada 5 segundos</span></div>
          {lista.length === 0 ? <p className="gris">Todavía no hay lotes. Crea el primero con «Nuevo lote».</p> : (
            <div className="tabla-env"><table className="tabla">
              <thead><tr><th>Lote</th><th>Caja</th><th className="num">Páginas</th><th>Estado</th><th /></tr></thead>
              <tbody>{lista.map((l) => (
                <tr key={l.code} className="fila-link" onClick={async () => setSel(await apiLote(l.code))}>
                  <td><span className="t-princ maq">{l.code}</span><span className="t-sec">{l.origen} · {hora(l.creado)}</span></td>
                  <td className="maq">{l.caja}</td>
                  <td className="num">{l.recibidas}</td>
                  <td><span className={`chip ${estadoLote[l.estado]?.[1] ?? "neutro"}`}>{l.rechazos ? `${l.rechazos} por repetir` : estadoLote[l.estado]?.[0] ?? l.estado}</span></td>
                  <td><button className="btn btn-sec btn-chico">Ver</button></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
        <div className="panel">
          {!sel ? (
            <><div className="panel-cab"><h2>Cajas</h2></div>
              <ul className="lista-l">{cajas.map((c) => (
                <li key={c.code}>
                  <div className="tx"><b className="maq">{c.code}</b><span>{c.series_hint ?? "Sin serie"} · {c.anios} · estante {c.shelf_location ?? "—"}</span>
                    {c.estimated_pages ? <div className="barra-prog" style={{ marginTop: 6 }}><i style={{ width: `${Math.min(100, (c.captured_pages / c.estimated_pages) * 100)}%` }} /></div> : null}</div>
                  <a className="btn btn-sec btn-chico" href={urlEtiqueta(c.code)} target="_blank" rel="noopener">Etiqueta</a>
                </li>))}</ul></>
          ) : (
            <>
              <div className="panel-cab"><div><h2 className="maq">{sel.code}</h2><span className="sub">Caja {sel.caja} · {sel.recibidas} páginas</span></div><button className="icono-btn" aria-label="Cerrar detalle" onClick={() => setSel(null)}><Icono n="x" /></button></div>
              <div className="acciones" style={{ marginBottom: 12 }}>
                <a className="btn btn-sec btn-chico" href={urlHoja(sel.code)} target="_blank" rel="noopener"><Icono n="doc" />Hoja de lote</a>
                {sel.estado !== "cerrado" && <button className="btn btn-sec btn-chico" onClick={() => nuevoQr(sel)}><Icono n="celular" />Emparejar celular</button>}
                {puedePdf && sel.paginas?.some((p) => p.ocr === "ok") && <a className="btn btn-sec btn-chico" href={urlPdfLote(sel.code)} target="_blank" rel="noopener"><Icono n="descargar" />PDF buscable</a>}
              </div>
              {!sel.paginas?.length ? <p className="gris" style={{ fontSize: ".86rem" }}>Esperando la primera página…</p> : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0,1fr))", gap: 10 }}>
                  {sel.paginas.map((p) => (
                    <figure key={p.id} style={{ margin: 0, display: "grid", gap: 5 }}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={urlMiniatura(p.id)} alt={`Página ${p.indice}`} loading="lazy" style={{ width: "100%", aspectRatio: "3/4", objectFit: "cover", borderRadius: 6, background: "#ECEBDF", outline: p.estado === "reescanear" ? "2px solid var(--falta)" : undefined }} onError={(e) => { (e.target as HTMLImageElement).style.visibility = "hidden"; }} />
                      <figcaption style={{ fontSize: ".74rem" }}><b className="maq">pág. {p.indice}</b> <span className={`chip ${estadoPagina[p.estado]?.[1] ?? "neutro"}`}>{estadoPagina[p.estado]?.[0] ?? p.estado}</span>{p.motivo ? <span className="gris2" style={{ display: "block" }}>{p.motivo}</span> : null}{p.ocr === "ok" ? <span className="gris2" style={{ display: "block" }}>Texto leído{p.idioma ? ` · ${p.idioma}` : ""}</span> : p.ocr === "error" ? <span style={{ display: "block", color: "var(--falta)" }}>No se pudo leer</span> : null}</figcaption>
                    </figure>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {modal === "lote" && (
        <div className="modal-fondo" onClick={() => setModal(null)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="t-lote" onClick={(e) => e.stopPropagation()} style={{ width: "min(640px,100%)" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-lote">{nuevo ? `Lote ${nuevo.lote.code}` : "Nuevo lote con celular"}</h2><button className="icono-btn" aria-label="Cerrar" onClick={() => setModal(null)}><Icono n="x" /></button></div>
            {!nuevo ? (
              <>
                <div className="campo-f"><label htmlFor="caja-lote">Caja</label>
                  <select id="caja-lote" className="inp" value={cajaElegida} onChange={(e) => setCajaElegida(e.target.value)}>{cajas.map((c) => <option key={c.code} value={c.code}>{c.code} · {c.series_hint ?? "sin serie"} · {c.anios}</option>)}</select></div>
                {error && <p className="error-form">{error}</p>}
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button className="btn btn-sec" onClick={() => setModal(null)}>Cancelar</button><button className="btn btn-prim" onClick={nuevoLote}>Crear lote</button></div>
              </>
            ) : (
              <div className="rejilla r2" style={{ alignItems: "center" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                {nuevo.qr && <img src={nuevo.qr} alt="Código QR para emparejar el celular" style={{ width: "100%", maxWidth: 240, borderRadius: 12, justifySelf: "center" }} />}
                <div style={{ display: "grid", gap: 10 }}>
                  <p>Abre la cámara del celular y escanea el código. Se abre la app de captura ya ligada a este lote; no hay que instalar nada.</p>
                  <span className="gris2" style={{ fontSize: ".78rem" }}>Vence a las {nuevo.vence ? hora(nuevo.vence) : "—"} y sirve para un solo celular.</span>
                  <a className="btn btn-sec" href={urlHoja(nuevo.lote.code)} target="_blank" rel="noopener"><Icono n="doc" />Imprimir hoja de lote</a>
                  <button className="btn btn-prim" onClick={() => setModal(null)}>Listo</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {modal === "caja" && (
        <div className="modal-fondo" onClick={() => setModal(null)}>
          <form className="modal" role="dialog" aria-modal="true" aria-labelledby="t-caja" onClick={(e) => e.stopPropagation()} onSubmit={registrarCaja} style={{ width: "min(560px,100%)" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-caja">Registrar caja</h2><button type="button" className="icono-btn" aria-label="Cerrar" onClick={() => setModal(null)}><Icono n="x" /></button></div>
            <div className="rejilla r2" style={{ gap: 12 }}>
              <div className="campo-f"><label htmlFor="code">Código</label><input id="code" name="code" className="inp maq" required pattern="C-\d{4,6}" placeholder="C-0045" /></div>
              <div className="campo-f"><label htmlFor="estante">Estante</label><input id="estante" name="estante" className="inp" placeholder="B-3" /></div>
              <div className="campo-f"><label htmlFor="desde">Año desde</label><input id="desde" name="desde" className="inp" inputMode="numeric" placeholder="2017" /></div>
              <div className="campo-f"><label htmlFor="hasta">Año hasta</label><input id="hasta" name="hasta" className="inp" inputMode="numeric" placeholder="2018" /></div>
              <div className="campo-f"><label htmlFor="serie">Serie</label><input id="serie" name="serie" className="inp" placeholder="Beneficios" /></div>
              <div className="campo-f"><label htmlFor="estimadas">Páginas estimadas</label><input id="estimadas" name="estimadas" className="inp" inputMode="numeric" placeholder="2200" /></div>
            </div>
            {error && <p className="error-form">{error}</p>}
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button type="button" className="btn btn-sec" onClick={() => setModal(null)}>Cancelar</button><button className="btn btn-prim" type="submit">Registrar</button></div>
          </form>
        </div>
      )}
    </>
  );
}
