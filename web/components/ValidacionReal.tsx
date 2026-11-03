"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { colaValidacion, documento, resolverTarea, urlImagenPagina, ErrorApi, type CampoDoc, type Cola, type DocDetalle, type TareaDoc } from "@/lib/api";

// Validación real (Sprint 3): la página a la izquierda con el dato resaltado donde se leyó; los campos a la derecha.
// Enter acepta o guarda la corrección; Tab pasa al siguiente campo pendiente. Cada decisión queda en la auditoría.

const ESTADO: Record<string, [string, string]> = {
  auto_aceptado: ["Aceptado por la IA", "ok"], validado: ["Validado", "ok"], pendiente: ["Por validar", "duda"],
  vacio: ["No está en el documento", "neutro"], rechazado: ["Vaciado", "neutro"],
};
const pct = (c: number | null) => (c == null ? null : Math.round(c * 100));

function Campo({ c, tarea, activo, onActivar, onResuelto }: { c: CampoDoc; tarea?: TareaDoc; activo: boolean; onActivar: () => void; onResuelto: (msg?: string) => void }) {
  const [valor, setValor] = useState(c.valor ?? "");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const ref = useRef<HTMLInputElement | HTMLSelectElement>(null);
  useEffect(() => { setValor(c.valor ?? ""); setError(""); }, [c.id, c.valor]);
  useEffect(() => { if (activo && tarea && ref.current) { ref.current.focus({ preventScroll: true }); ref.current.scrollIntoView({ block: "nearest", behavior: "smooth" }); } }, [activo, tarea]);
  const enviar = async (accion: "aceptar" | "corregir" | "vaciar") => {
    if (!tarea) return;
    setOcupado(true); setError("");
    try {
      const cambiado = valor.trim() !== (c.valor ?? "");
      await resolverTarea(tarea.id, accion === "aceptar" && cambiado ? { accion: "corregir", valor } : accion === "corregir" ? { accion, valor } : { accion });
      onResuelto();
    } catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo guardar."); }
    finally { setOcupado(false); }
  };
  const [txt, cls] = ESTADO[c.estado] ?? [c.estado, "neutro"];
  const p = pct(c.confianza);
  return (
    <div className={`campo-val${activo ? " activo" : ""}${tarea ? " pendiente" : ""}`} onClick={onActivar}>
      <div className="campo-val-cab">
        <label htmlFor={`f-${c.key}`}>{c.nombre}{c.requerido ? <span className="gris2"> *</span> : null}{c.sensible ? <span className="chip falta" style={{ marginLeft: 6 }}>sensible</span> : null}</label>
        <span style={{ display: "flex", gap: 6 }}>{p != null && <span className={`chip lleno ${p >= 95 ? "ok" : p >= 85 ? "duda" : "falta"}`}>{p}%</span>}<span className={`chip ${cls}`}>{txt}</span></span>
      </div>
      {c.opciones ? (
        <select id={`f-${c.key}`} ref={ref as React.RefObject<HTMLSelectElement>} className="inp maq" value={valor} disabled={!tarea || ocupado} onChange={(e) => setValor(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); enviar("aceptar"); } }}>
          <option value="">—</option>{c.opciones.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input id={`f-${c.key}`} ref={ref as React.RefObject<HTMLInputElement>} className="inp maq" value={valor} placeholder={tarea ? "Escribe el valor" : "—"} readOnly={!tarea} disabled={ocupado}
          onChange={(e) => setValor(e.target.value)} onFocus={onActivar}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); enviar("aceptar"); } if (e.key === "d" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); enviar("vaciar"); } }} />
      )}
      {(tarea || c.original) && (
        <div className="campo-val-pie">
          {tarea ? <span className="duda-txt">{tarea.motivo}</span> : <span className="gris2">Leído: <span className="maq">{c.original}</span></span>}
          {c.pagina ? <span className="gris2">pág. {c.pagina}</span> : null}
        </div>
      )}
      {tarea && activo && (
        <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
          <button className="btn btn-prim btn-chico" disabled={ocupado} onClick={(e) => { e.stopPropagation(); enviar("aceptar"); }}><Icono n="check" />{valor.trim() !== (c.valor ?? "") ? "Guardar corrección" : "Aceptar"}</button>
          <button className="btn btn-sec btn-chico" disabled={ocupado} onClick={(e) => { e.stopPropagation(); enviar("vaciar"); }}>No está en el documento</button>
        </div>
      )}
      {error && <span style={{ color: "var(--falta)", fontSize: ".78rem" }}>{error}</span>}
    </div>
  );
}

export default function ValidacionReal() {
  const [cola, setCola] = useState<Cola | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [doc, setDoc] = useState<DocDetalle | null>(null);
  const [activo, setActivo] = useState<string | null>(null);
  const [pagina, setPagina] = useState(0);
  const [aviso, setAviso] = useState("");
  const [tipoNuevo, setTipoNuevo] = useState("");

  const cargarCola = useCallback(async () => {
    try { const c = await colaValidacion(); setCola(c); return c; }
    catch (e) { setAviso(e instanceof ErrorApi && e.estado === 403 ? "Tu rol no valida documentos." : "No se pudo cargar la cola."); return null; }
  }, []);
  const abrir = useCallback(async (id: string) => {
    setSel(id); setDoc(null);
    try {
      const d = await documento(id); setDoc(d); setTipoNuevo(d.tipo);
      const t = d.tareas.find((x) => x.tipo === "campo");
      const c = t ? d.campos.find((x) => x.id === t.campo) : undefined;
      setActivo(c?.key ?? null);
      setPagina(Math.max(0, (c?.caja?.pagina ?? c?.pagina ?? 1) - 1));
    } catch { setAviso("No se pudo abrir el documento."); }
  }, []);
  useEffect(() => { cargarCola().then((c) => { if (c?.documentos[0]) abrir(c.documentos[0].id); }); }, [cargarCola, abrir]);

  const tareaDe = useMemo(() => Object.fromEntries((doc?.tareas ?? []).filter((t) => t.campo).map((t) => [t.campo as string, t])), [doc]);
  const campoActivo = doc?.campos.find((c) => c.key === activo);
  const resaltes = (doc?.campos ?? []).filter((c) => c.caja && (c.caja.pagina ?? 1) - 1 === pagina);

  const trasResolver = async () => {
    if (!doc) return;
    const d = await documento(doc.id).catch(() => null);
    if (d && d.tareas.length) {
      setDoc(d);
      const t = d.tareas.find((x) => x.tipo === "campo");
      const c = t ? d.campos.find((x) => x.id === t.campo) : undefined;
      if (c) { setActivo(c.key); setPagina(Math.max(0, (c.caja?.pagina ?? c.pagina ?? 1) - 1)); }
      cargarCola();
    } else {
      setAviso(`«${doc.titulo}» quedó validado.`);
      const c = await cargarCola();
      const sig = c?.documentos.find((x) => x.id !== doc.id);
      if (sig) abrir(sig.id); else { setDoc(null); setSel(null); }
    }
  };
  const resolverOtra = async (t: TareaDoc, cuerpo: { accion: string; tipo?: string }) => {
    try {
      const r = await resolverTarea(t.id, cuerpo);
      if (r.estado === "reextrayendo") { setAviso("Tipo corregido. La IA vuelve a leer los campos con el nuevo tipo; aparecerá en la cola en unos segundos."); setDoc(null); setTimeout(() => cargarCola(), 6000); return; }
      trasResolver();
    } catch (e) { setAviso(e instanceof ErrorApi ? e.message : "No se pudo guardar."); }
  };

  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || e.shiftKey || !doc) return;
      const pend = doc.campos.filter((c) => c.id && tareaDe[c.id]);
      if (!pend.length) return;
      e.preventDefault();
      const i = pend.findIndex((c) => c.key === activo);
      const sig = pend[(i + 1) % pend.length];
      setActivo(sig.key); setPagina(Math.max(0, (sig.caja?.pagina ?? sig.pagina ?? 1) - 1));
    };
    window.addEventListener("keydown", f); return () => window.removeEventListener("keydown", f);
  }, [doc, activo, tareaDe]);

  const otras = (doc?.tareas ?? []).filter((t) => t.tipo !== "campo");
  const pagActual = doc?.paginas[pagina];
  return (
    <>
      <Cab titulo="Validación" maq="solo lo que la IA no tiene claro" desc="La página a la izquierda con el dato resaltado donde se leyó; los campos a la derecha con su confianza. Enter acepta, Tab pasa al siguiente.">
        {cola && <div className="tabs"><button className="on">Por validar · {cola.documentos.length} documentos · {cola.tareas} datos</button><button disabled>{cola.validados} de {cola.total_documentos} listos</button></div>}
      </Cab>
      {aviso && <div className="aviso" style={{ marginBottom: 12 }}><Icono n="alerta" /><span>{aviso}</span><button className="icono-btn" style={{ marginLeft: "auto" }} onClick={() => setAviso("")} aria-label="Cerrar aviso"><Icono n="x" /></button></div>}
      {cola && cola.documentos.length === 0 && !doc && <div className="panel"><p className="gris">No hay nada por validar. Cuando se cierre un lote, la IA separa, clasifica y extrae; aquí aparece solo lo dudoso.</p></div>}
      {(cola?.documentos.length || doc) ? (
        <div className="rejilla val-grid">
          <div className="panel plano" style={{ padding: 10, alignSelf: "start" }}>
            <span className="nav-t" style={{ display: "block" }}>Cola · prioridad</span>
            <ul className="lista-l">
              {cola?.documentos.map((d) => (
                <li key={d.id} onClick={() => abrir(d.id)} style={{ cursor: "pointer", padding: "10px 8px", borderRadius: 10, background: sel === d.id ? "rgba(220,229,122,.08)" : undefined }}>
                  <div className="tx"><b>{d.tipo_nombre}</b><span><span className="maq">{d.lote}</span> · {d.pendientes} por validar</span></div>
                  <span className={`chip ${d.prioridad === 1 ? "duda" : "neutro"}`}>{d.prioridad === 1 ? "Alta" : "Normal"}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel val-pagina" style={{ display: "grid", gap: 12, alignContent: "start", minWidth: 0 }}>
            {doc ? (
              <>
                <div className="panel-cab" style={{ margin: 0 }}>
                  <div><h2>{doc.titulo}</h2><span className="sub">Lote <span className="maq lima">{doc.lote}</span> · caja <span className="maq">{doc.caja}</span> · {doc.serie} · {doc.sensibilidad}{doc.fecha ? ` · ${doc.fecha}` : ""}</span></div>
                  {doc.paginas.length > 1 && <div className="acciones">{doc.paginas.map((p, i) => <button key={p.id} className={`btn btn-chico ${i === pagina ? "btn-prim" : "btn-sec"}`} onClick={() => setPagina(i)}>pág. {i + 1}</button>)}</div>}
                </div>
                {pagActual && (
                  <div className="visor-pag" style={{ maxWidth: 560, width: "100%", justifySelf: "center" }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={urlImagenPagina(pagActual.id)} alt={`Página ${pagina + 1} del documento`} />
                    {resaltes.map((c) => c.caja && (
                      <span key={c.key} className={`resalte${c.key === activo ? "" : " suave"}`} title={c.nombre} onClick={() => setActivo(c.key)}
                        style={{ left: `${c.caja.x0 * 100}%`, top: `${c.caja.y0 * 100}%`, width: `${(c.caja.x1 - c.caja.x0) * 100}%`, height: `${(c.caja.y1 - c.caja.y0) * 100}%`, pointerEvents: "auto", cursor: "pointer" }} />
                    ))}
                  </div>
                )}
                {campoActivo && !campoActivo.caja && campoActivo.valor && <p className="gris2" style={{ fontSize: ".78rem", textAlign: "center" }}>No se ubicó «{campoActivo.nombre}» en la imagen; revisa el texto de la página.</p>}
              </>
            ) : <p className="gris">Abriendo documento…</p>}
          </div>

          <div className="panel val-campos" style={{ display: "grid", gap: 10, alignContent: "start" }}>
            {doc && (
              <>
                <div className="panel-cab" style={{ margin: 0 }}><h2>Datos extraídos</h2><span className={`chip ${doc.tareas.length ? "duda" : "ok"}`}>{doc.tareas.length ? `${doc.tareas.length} por validar` : "Todo validado"}</span></div>
                <div className="campo-val">
                  <div className="campo-val-cab"><span>Tipo documental</span>{pct(doc.confianza_tipo) != null && <span className={`chip lleno ${pct(doc.confianza_tipo)! >= 95 ? "ok" : pct(doc.confianza_tipo)! >= 85 ? "duda" : "falta"}`}>{pct(doc.confianza_tipo)}%</span>}</div>
                  {otras.filter((t) => t.tipo === "clasificacion").map((t) => (
                    <div key={t.id} style={{ display: "grid", gap: 6 }}>
                      <span className="duda-txt">{t.motivo}</span>
                      <select className="inp" value={tipoNuevo} onChange={(e) => setTipoNuevo(e.target.value)}>{doc.tipos.map((x) => <option key={x.key} value={x.key}>{x.nombre}</option>)}</select>
                      <button className="btn btn-prim btn-chico" onClick={() => resolverOtra(t, tipoNuevo === doc.tipo ? { accion: "aceptar" } : { accion: "tipo", tipo: tipoNuevo })}><Icono n="check" />{tipoNuevo === doc.tipo ? "El tipo es correcto" : "Cambiar tipo y volver a leer"}</button>
                    </div>
                  ))}
                  {!otras.some((t) => t.tipo === "clasificacion") && <b style={{ color: "var(--blanco)", fontWeight: 500 }}>{doc.tipo_nombre}</b>}
                </div>
                {otras.filter((t) => t.tipo === "separacion").map((t) => (
                  <div key={t.id} className="campo-val pendiente"><span className="duda-txt">{t.motivo}</span><button className="btn btn-sec btn-chico" onClick={() => resolverOtra(t, { accion: "separacion_ok" })}>Las páginas están bien</button></div>
                ))}
                {doc.campos.map((c) => (
                  <Campo key={c.key} c={c} tarea={c.id ? tareaDe[c.id] : undefined} activo={activo === c.key}
                    onActivar={() => { setActivo(c.key); if (c.caja?.pagina || c.pagina) setPagina(Math.max(0, (c.caja?.pagina ?? c.pagina ?? 1) - 1)); }}
                    onResuelto={trasResolver} />
                ))}
                <p className="gris2" style={{ fontSize: ".74rem" }}><span className="maq">Enter</span> acepta o guarda · <span className="maq">Tab</span> siguiente pendiente · <span className="maq">Ctrl+D</span> no está en el documento. Cada decisión queda en la auditoría.</p>
              </>
            )}
          </div>
        </div>
      ) : null}
    </>
  );
}
