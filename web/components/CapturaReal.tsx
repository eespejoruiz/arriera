"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import PanelMicroformas from "@/components/PanelMicroformas";
import { SkeletonRows } from "./Esqueleto";
import {
  cajas as apiCajas, crearCaja, crearLote, emparejar, ErrorApi, importarArchivo, lote as apiLote, lotes as apiLotes,
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
  const [listo, setListo] = useState(false);
  const [roles, setRoles] = useState<string[]>([]);
  useEffect(() => { yo().then((u) => setRoles(u.roles)).catch(() => {}); }, []);
  const puedePdf = roles.some((r) => r === "admin" || r === "archivero");
  const [cajas, setCajas] = useState<Caja[]>([]);
  const [sel, setSel] = useState<Lote | null>(null);
  const [modal, setModal] = useState<"lote" | "caja" | "importar" | null>(null);
  const [archivos, setArchivos] = useState<File[]>([]);
  const [avance, setAvance] = useState<{ hecho: number; total: number; paginas: number; repetidos: number; errores: string[] } | null>(null);
  const [nuevo, setNuevo] = useState<{ lote: Lote; qr?: string; vence?: string } | null>(null);
  const [mfNuevo, setMfNuevo] = useState(false);
  const [cajaElegida, setCajaElegida] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const [l, c] = await Promise.all([apiLotes(), apiCajas()]);
      setLista(l); setCajas(c);
      setCajaElegida((x) => x || c[0]?.code || "");
      if (sel) setSel(await apiLote(sel.code));
    } catch (e) { if (e instanceof ErrorApi && e.estado === 403) setError("Tu perfil no tiene acceso a Captura."); }
    finally { setListo(true); }
  }, [sel]);
  useEffect(() => { cargar(); const i = setInterval(cargar, 5000); return () => clearInterval(i); }, [cargar]);

  const nuevoLote = async () => {
    setError("");
    try {
      const l = await crearLote(cajaElegida, "celular", mfNuevo);
      const e = await emparejar(l.code);
      setNuevo({ lote: l, qr: svgComoImagen(e.qr_svg), vence: e.vence });
      cargar();
    } catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo crear el lote."); }
  };
  const importar = async () => {
    setError("");
    if (!archivos.length) { setError("Elige al menos un archivo."); return; }
    try {
      const l = await crearLote(cajaElegida, "importacion", false);
      const a = { hecho: 0, total: archivos.length, paginas: 0, repetidos: 0, errores: [] as string[] };
      setAvance({ ...a });
      for (const f of archivos) {
        try { const r = await importarArchivo(l.code, f); a.paginas += r.paginas.length; if (r.duplicado) a.repetidos += 1; }
        catch (e) { a.errores.push(`${f.name}: ${e instanceof ErrorApi ? e.message : "no se pudo subir"}`); }
        a.hecho += 1; setAvance({ ...a });
      }
      setSel(await apiLote(l.code)); cargar();
    } catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo crear el lote de importación."); }
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
        <button className="btn btn-sec" onClick={() => { setError(""); setArchivos([]); setAvance(null); setModal("importar"); }} disabled={!cajas.length}><Icono n="descargar" />Importar PDF</button>
        <button className="btn btn-prim" onClick={() => { setError(""); setNuevo(null); setModal("lote"); }} disabled={!cajas.length}><Icono n="mas" />Nuevo lote</button>
      </Cab>
      {error && !modal && <p className="error-form">{error}</p>}
      {listo && !cajas.length && <div className="aviso"><Icono n="caja" /><span>Primero registra una caja del archivo. Cada lote pertenece a una caja.</span></div>}

      <div className="rejilla r-73">
        <div className="panel">
          <div className="panel-cab"><h2>Lotes</h2><span className="sub">se actualiza cada 5 segundos</span></div>
          {!listo ? <SkeletonRows n={4} /> : lista.length === 0 ? <p className="gris">Todavía no hay lotes. Crea el primero con «Nuevo lote».</p> : (
            <div className="tabla-env"><table className="tabla">
              <thead><tr><th>Lote</th><th>Caja</th><th className="num">Páginas</th><th>Estado</th><th /></tr></thead>
              <tbody>{lista.map((l) => (
                <tr key={l.code} className="fila-link" onClick={async () => setSel(await apiLote(l.code))}>
                  <td><span className="t-princ maq">{l.code}</span><span className="t-sec">{l.origen === "importacion" ? "importación" : l.origen} · {hora(l.creado)}</span></td>
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
              {sel.microformas && <PanelMicroformas code={sel.code} />}
              {sel.ia && (
                <div className="aviso" style={{ marginBottom: 12, fontSize: ".82rem" }}><Icono n="ia" /><span>{
                  sel.ia.estado === "listo" ? <>La IA encontró <b>{sel.ia.documentos} documento{sel.ia.documentos === 1 ? "" : "s"}</b> en este lote. Lo dudoso está en <Link href="/validacion/" className="lima">Validación</Link>.</>
                  : sel.ia.estado === "procesando" ? "La IA está separando, clasificando y leyendo los documentos…"
                  : sel.ia.estado === "pausado_presupuesto" ? "Procesamiento en pausa: se alcanzó el presupuesto mensual de IA."
                  : sel.ia.motivo ?? sel.ia.estado}</span></div>
              )}
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
                <label style={{ display: "flex", gap: 10, alignItems: "flex-start", fontSize: ".86rem" }}><input type="checkbox" checked={mfNuevo} onChange={(e) => setMfNuevo(e.target.checked)} style={{ accentColor: "#DCE57A", marginTop: 3 }} /><span><b style={{ fontWeight: 500, color: "var(--blanco)" }}>Lote para microformas</b><br /><span className="gris2">Sigue los pasos de la NTP 392.030-2, exige 300 dpi y genera actas de apertura y cierre.</span></span></label>
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

      {modal === "importar" && (
        <div className="modal-fondo" onClick={() => setModal(null)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="t-imp" onClick={(e) => e.stopPropagation()} style={{ width: "min(600px,100%)" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-imp">Importar archivos digitales</h2><button className="icono-btn" aria-label="Cerrar" onClick={() => setModal(null)}><Icono n="x" /></button></div>
            <p className="gris" style={{ fontSize: ".88rem" }}>PDF escaneados, exportaciones de otro gestor o fotos sueltas. Cada página pasa por el mismo control de calidad, lectura e IA que una hoja escaneada. El archivo original se guarda con su huella.</p>
            {!avance ? (
              <>
                <div className="campo-f"><label htmlFor="caja-imp">Caja a la que pertenecen</label>
                  <select id="caja-imp" className="inp" value={cajaElegida} onChange={(e) => setCajaElegida(e.target.value)}>{cajas.map((c) => <option key={c.code} value={c.code}>{c.code} · {c.series_hint ?? "sin serie"} · {c.anios}</option>)}</select></div>
                <label className="soltar">
                  <input type="file" multiple accept="application/pdf,image/jpeg,image/png,image/webp" onChange={(e) => setArchivos(Array.from(e.target.files ?? []))} />
                  <Icono n="doc" /><b>{archivos.length ? `${archivos.length} archivo${archivos.length > 1 ? "s" : ""} elegido${archivos.length > 1 ? "s" : ""}` : "Elige PDF o imágenes"}</b>
                  <span className="gris2">Hasta 60 MB y 500 páginas por archivo</span>
                </label>
                {error && <p className="error-form">{error}</p>}
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button className="btn btn-sec" onClick={() => setModal(null)}>Cancelar</button><button className="btn btn-prim" onClick={importar} disabled={!archivos.length}>Importar</button></div>
              </>
            ) : (
              <div style={{ display: "grid", gap: 10 }}>
                <div className="barra-prog"><i style={{ width: `${Math.round((avance.hecho / avance.total) * 100)}%` }} /></div>
                <p>{avance.hecho} de {avance.total} archivos · {avance.paginas} páginas nuevas{avance.repetidos ? ` · ${avance.repetidos} ya estaban` : ""}</p>
                {avance.errores.map((e) => <p key={e} className="error-form">{e}</p>)}
                {avance.hecho === avance.total && <button className="btn btn-prim" onClick={() => setModal(null)}>Ver el lote</button>}
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
