"use client";
import { useCallback, useEffect, useState } from "react";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import {
  buscar, verPagina, resumenProceso, urlImagenPagina, urlMiniaturaBusqueda, urlPdfLote, ErrorApi,
  type Busqueda, type PaginaVista, type ResumenProceso,
} from "@/lib/api";

// Primera búsqueda real (Sprint 2): texto completo por página, con filtros por caja e idioma y visor con resaltado.

const IDIOMAS: Record<string, string> = { es: "Español", en: "Inglés", pt: "Portugués", fr: "Francés", it: "Italiano", de: "Alemán", "?": "Sin detectar" };
const ejemplos = ["subsidio", "Huamán", "informe médico", "boleta de pago"];

function Fragmento({ texto, marcas }: { texto: string | null; marcas: [string, string] }) {
  if (!texto) return <span className="gris2">Sin texto leído.</span>;
  const partes: React.ReactNode[] = [];
  texto.split(marcas[0]).forEach((trozo, i) => {
    if (i === 0) { partes.push(trozo); return; }
    const [res, resto = ""] = trozo.split(marcas[1]);
    partes.push(<mark key={i}>{res}</mark>, resto);
  });
  return <>{partes}</>;
}

function Visor({ id, q, onCerrar, puedePdf }: { id: string; q: string; onCerrar: () => void; puedePdf: boolean }) {
  const [v, setV] = useState<PaginaVista | null>(null);
  const [error, setError] = useState("");
  const [verTexto, setVerTexto] = useState(false);
  useEffect(() => { verPagina(id, q).then(setV).catch((e) => setError(e instanceof ErrorApi ? e.message : "No se pudo abrir la página.")); }, [id, q]);
  useEffect(() => { const k = (e: KeyboardEvent) => e.key === "Escape" && onCerrar(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onCerrar]);
  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal" style={{ width: "min(880px, 100%)" }} role="dialog" aria-modal="true" aria-label="Página encontrada" onClick={(e) => e.stopPropagation()}>
        <div className="panel-cab" style={{ marginBottom: 0 }}>
          <div>
            <h3 style={{ fontSize: "1.05rem" }}>{v ? <>Lote <span className="maq lima">{v.lote}</span> · pág. {v.indice} de {v.total_paginas}</> : "Abriendo página…"}</h3>
            {v && <span className="sub">Caja <span className="maq">{v.caja}</span> · {IDIOMAS[v.idioma ?? "?"] ?? v.idioma}{v.confianza != null ? ` · lectura ${Math.round(v.confianza * 100)}%` : ""}{v.resaltes.length ? ` · ${v.resaltes.length} coincidencia${v.resaltes.length > 1 ? "s" : ""}` : ""}</span>}
          </div>
          <button className="icono-btn" onClick={onCerrar} aria-label="Cerrar"><Icono n="x" /></button>
        </div>
        {error && <div className="aviso"><Icono n="alerta" /><span>{error}</span></div>}
        {v && (
          <>
            <div className="visor-pag">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={urlImagenPagina(v.pagina_id)} alt={`Página ${v.indice} del lote ${v.lote}`} width={v.ancho ?? undefined} height={v.alto ?? undefined} />
              {v.resaltes.map((r, i) => (
                <span key={i} className="resalte" style={{ left: `${r.x0 * 100}%`, top: `${r.y0 * 100}%`, width: `${(r.x1 - r.x0) * 100}%`, height: `${(r.y1 - r.y0) * 100}%` }} />
              ))}
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn btn-sec btn-chico" onClick={() => setVerTexto((x) => !x)}><Icono n="ia" />{verTexto ? "Ocultar texto leído" : "Ver texto leído"}</button>
              {puedePdf && <a className="btn btn-sec btn-chico" href={urlPdfLote(v.lote)} target="_blank" rel="noopener"><Icono n="descargar" />PDF buscable del lote</a>}
            </div>
            {verTexto && <pre className="maq texto-leido">{v.texto || "Sin texto."}</pre>}
          </>
        )}
      </div>
    </div>
  );
}

export default function BusquedaReal() {
  const [q, setQ] = useState("");
  const [consulta, setConsulta] = useState("");
  const [caja, setCaja] = useState("");
  const [idioma, setIdioma] = useState("");
  const [res, setRes] = useState<Busqueda | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [abierta, setAbierta] = useState<string | null>(null);
  const [resumen, setResumen] = useState<ResumenProceso | null>(null);
  const [ms, setMs] = useState(0);

  useEffect(() => { resumenProceso().then(setResumen).catch(() => {}); }, []);

  const ejecutar = useCallback(async (texto: string, f: { caja?: string; idioma?: string } = {}) => {
    if (!texto.trim()) return;
    setCargando(true); setError(""); const t0 = performance.now();
    const p: Record<string, string> = { q: texto };
    if (f.caja) p.caja = f.caja;
    if (f.idioma) p.idioma = f.idioma;
    try { setRes(await buscar(p)); setConsulta(texto); setMs(performance.now() - t0); }
    catch (e) {
      setRes(null);
      setError(e instanceof ErrorApi && e.estado === 403
        ? "Tu rol todavía no puede buscar en el contenido. Llegará cuando cada documento tenga su nivel de sensibilidad."
        : e instanceof ErrorApi ? e.message : "No se pudo buscar. Revisa tu conexión.");
    } finally { setCargando(false); }
  }, []);

  useEffect(() => { const u = new URLSearchParams(window.location.search).get("q"); if (u) { setQ(u); ejecutar(u); } }, [ejecutar]);

  const filtrar = (tipo: "caja" | "idioma", valor: string) => {
    const nc = tipo === "caja" ? (caja === valor ? "" : valor) : caja;
    const ni = tipo === "idioma" ? (idioma === valor ? "" : valor) : idioma;
    setCaja(nc); setIdioma(ni); ejecutar(consulta, { caja: nc, idioma: ni });
  };
  const tesseract = resumen?.proveedores.find((p) => p.proveedor === resumen.proveedor_activo) ?? resumen?.proveedores[0];

  return (
    <>
      <Cab titulo="Búsqueda" maq="cualquier palabra, en cualquier página" desc="Busca en el texto que la IA leyó de cada página: nombres, números, frases. Encuentra también plurales y palabras sin tilde, y abre la página con la coincidencia resaltada." />
      <div style={{ display: "grid", gap: 14, minWidth: 0 }}>
        <form className="buscador" style={{ maxWidth: "none", padding: "13px 16px", fontSize: "1.02rem" }} onSubmit={(e) => { e.preventDefault(); setCaja(""); setIdioma(""); ejecutar(q); }}>
          <Icono n="busqueda" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ej.: subsidio, Huamán, «informe médico»" aria-label="Consulta" maxLength={200} />
          <button className="btn btn-prim btn-chico" type="submit" disabled={cargando}>{cargando ? "Buscando…" : "Buscar"}</button>
        </form>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
          <span className="gris2" style={{ fontSize: ".78rem" }}>Prueba con:</span>
          {ejemplos.map((e) => <button key={e} className="btn btn-sec btn-chico" onClick={() => { setQ(e); setCaja(""); setIdioma(""); ejecutar(e); }}>{e}</button>)}
          {tesseract && <span className="gris2" style={{ fontSize: ".74rem", marginLeft: "auto" }}>OCR {resumen?.proveedor_activo} · {tesseract.paginas} páginas leídas · US$ {tesseract.usd_por_mil.toFixed(2)} por mil · {tesseract.segundos_por_pagina} s por página</span>}
        </div>
        {error && <div className="aviso"><Icono n="alerta" /><span>{error}</span></div>}
        {res && (
          <div className="rejilla bus-res" style={{ gap: 14 }}>
            <div className="panel plano" style={{ padding: 14, display: "grid", gap: 14, alignContent: "start", fontSize: ".82rem" }}>
              {([["Caja", "caja", res.facetas.cajas, caja], ["Idioma", "idioma", res.facetas.idiomas, idioma]] as const).map(([t, tipo, ops, activo]) => (
                <div key={t} style={{ display: "grid", gap: 6 }}>
                  <b style={{ color: "var(--blanco)", fontWeight: 500 }}>{t}</b>
                  {ops.length === 0 && <span className="gris2">—</span>}
                  {ops.map((o) => (
                    <label key={o.valor} style={{ display: "flex", justifyContent: "space-between", gap: 6, cursor: "pointer" }}>
                      <span><input type="checkbox" checked={activo === o.valor} onChange={() => filtrar(tipo, o.valor)} style={{ accentColor: "#DCE57A" }} /> {tipo === "idioma" ? IDIOMAS[o.valor] ?? o.valor : <span className="maq">{o.valor}</span>}</span>
                      <span className="gris2">{o.n}</span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
            <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--linea)", display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                <b style={{ color: "var(--blanco)", fontWeight: 500 }}>{res.total === 1 ? "1 página" : `${res.total.toLocaleString("es-PE")} páginas`} para «{res.consulta}»</b>
                <span className="gris2" style={{ fontSize: ".78rem" }}>{(ms / 1000).toFixed(2)} s</span>
              </div>
              {res.total === 0 && <p className="gris" style={{ padding: 16, fontSize: ".88rem" }}>No hay páginas con esas palabras. Prueba con menos palabras o revisa que el lote ya esté leído.</p>}
              {res.resultados.map((r) => (
                <button key={r.pagina_id} className="resultado-pag" onClick={() => setAbierta(r.pagina_id)}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={urlMiniaturaBusqueda(r.pagina_id)} alt="" loading="lazy" />
                  <span style={{ display: "grid", gap: 6, minWidth: 0 }}>
                    <span style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", fontSize: ".82rem" }}>
                      <b className="maq lima">{r.lote}</b><span className="gris2">Caja</span><span className="maq">{r.caja}</span><span className="gris2">· pág. {r.indice}</span>
                      {r.idioma && <span className="chip neutro">{IDIOMAS[r.idioma] ?? r.idioma}</span>}
                      {r.confianza != null && r.confianza < 0.7 && <span className="chip duda">lectura {Math.round(r.confianza * 100)}%</span>}
                    </span>
                    <span className="maq frag"><Fragmento texto={r.fragmento} marcas={res.marcas} /></span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
        {!res && !error && <p className="gris" style={{ fontSize: ".88rem" }}>Las páginas aparecen aquí apenas el OCR las lee, unos segundos después de capturarlas.</p>}
      </div>
      {abierta && <Visor id={abierta} q={consulta} onCerrar={() => setAbierta(null)} puedePdf={!!resumen} />}
    </>
  );
}
