"use client";
import { useCallback, useEffect, useState } from "react";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { SkeletonRows } from "./Esqueleto";
import {
  agregarASolicitud, buscarDocumentos, cambiarEstadoSolicitud, crearSolicitud, ErrorApi, generarCopia, quitarDeSolicitud,
  solicitud as apiSolicitud, solicitudes as apiSolicitudes, tiposSolicitud, urlCopiaSolicitud,
  type DocResumen, type SolicitudDetalle, type SolicitudResumen, type TiposSolicitud,
} from "@/lib/api";

const claseEstado: Record<string, string> = { recibida: "info", en_busqueda: "duda", lista: "ok", entregada: "neutro", rechazada: "falta" };
const fecha = (iso: string) => new Date(iso + (iso.length === 10 ? "T12:00:00" : "")).toLocaleDateString("es-PE", { day: "2-digit", month: "short" });

function Plazo({ dias }: { dias: number | null }) {
  if (dias === null) return <span className="plazo gris2">cerrada</span>;
  if (dias < 0) return <span className="plazo vencida">vencida hace {-dias} día{dias === -1 ? "" : "s"} hábil{dias === -1 ? "" : "es"}</span>;
  if (dias === 0) return <span className="plazo vence">vence hoy</span>;
  return <span className={`plazo ${dias <= 2 ? "vence" : "ok"}`}>{dias} día{dias === 1 ? "" : "s"} hábil{dias === 1 ? "" : "es"}</span>;
}

function FilaDoc({ d, accion, etiqueta, icono }: { d: DocResumen; accion: () => void; etiqueta: string; icono: string }) {
  return (
    <div className="sol-item">
      <div className="tx"><b>{d.titulo}</b><span>{d.tipo_nombre} · lote <span className="maq">{d.lote}</span> · {d.paginas.length} pág.{d.fecha ? ` · ${d.fecha}` : ""} {d.sensibilidad === "N3" && <span className="chip falta">N3</span>}</span></div>
      <button className="btn btn-sec btn-chico" onClick={accion}><Icono n={icono} />{etiqueta}</button>
    </div>
  );
}

export default function SolicitudesReal() {
  const [lista, setLista] = useState<SolicitudResumen[] | null>(null);
  const [filtro, setFiltro] = useState("abiertas");
  const [tipos, setTipos] = useState<TiposSolicitud | null>(null);
  const [sel, setSel] = useState<SolicitudDetalle | null>(null);
  const [nueva, setNueva] = useState(false);
  const [q, setQ] = useState("");
  const [hallados, setHallados] = useState<DocResumen[] | null>(null);
  const [oculto, setOculto] = useState("sensibles");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [nota, setNota] = useState("");

  const cargar = useCallback(async () => {
    try { setLista(await apiSolicitudes(filtro === "todas" ? "" : filtro)); }
    catch (e) { setError(e instanceof ErrorApi && e.estado === 403 ? "Las solicitudes las atienden administración y archivo." : "No se pudo cargar la lista."); setLista([]); }
  }, [filtro]);
  useEffect(() => { cargar(); }, [cargar]);
  useEffect(() => { tiposSolicitud().then(setTipos).catch(() => {}); }, []);

  const hacer = async (f: () => Promise<SolicitudDetalle>) => {
    setOcupado(true); setError("");
    try { const s = await f(); setSel(s); cargar(); return s; }
    catch (e) { setError(e instanceof ErrorApi ? e.message : "No se pudo completar la acción."); }
    finally { setOcupado(false); }
  };
  const abrir = async (id: string) => { setHallados(null); setQ(""); const s = await hacer(() => apiSolicitud(id)); if (s) setOculto(s.ocultamiento === "ninguno" && s.tipo !== "copia_hc" ? "ninguno" : s.ocultamiento || "sensibles"); };
  const crear = async (ev: React.FormEvent<HTMLFormElement>) => {
    ev.preventDefault();
    const f = new FormData(ev.currentTarget);
    const s = await hacer(() => crearSolicitud({
      tipo: String(f.get("tipo")), solicitante: String(f.get("solicitante")), documento: String(f.get("documento") || "") || undefined,
      contacto: String(f.get("contacto") || "") || undefined, relacion: String(f.get("relacion") || "") || undefined, detalle: String(f.get("detalle") || "") || undefined,
    }));
    if (s) { setNueva(false); setOculto(s.tipo === "copia_hc" ? "sensibles" : "ninguno"); }
  };
  const buscar = async (ev: React.FormEvent) => {
    ev.preventDefault(); if (!q.trim()) return;
    try { setHallados(await buscarDocumentos(q.trim())); } catch { setError("No se pudo buscar."); }
  };
  const enSel = new Set(sel?.items.map((d) => d.id) ?? []);
  const abierta = sel && !["entregada", "rechazada"].includes(sel.estado);

  return (
    <>
      <Cab titulo="Solicitudes" maq="copias y acceso, con plazo a la vista" desc="Cuando una persona pide copia de su expediente, de su historia clínica o el acceso a sus datos: regístralo, junta los documentos, emite la copia con lo sensible oculto y deja constancia de la entrega.">
        <button className="btn btn-prim" onClick={() => { setError(""); setNueva(true); }}><Icono n="mas" />Nueva solicitud</button>
      </Cab>
      {error && <div className="aviso"><Icono n="alerta" /><span>{error}</span></div>}

      <div className="sol-grid">
        <div className="panel" style={{ display: "grid", gap: 12 }}>
          <div className="tabs llenas" role="group" aria-label="Filtro">
            {[["abiertas", "Abiertas"], ["entregada", "Entregadas"], ["todas", "Todas"]].map(([k, n]) => <button key={k} className={filtro === k ? "on" : ""} onClick={() => setFiltro(k)}>{n}</button>)}
          </div>
          {lista === null ? <SkeletonRows n={5} /> : lista.length === 0 ? <p className="gris" style={{ fontSize: ".88rem" }}>No hay solicitudes {filtro === "abiertas" ? "abiertas" : "en esta vista"}. Registra la primera con «Nueva solicitud».</p> : (
            <ul className="lista-l">
              {lista.map((s) => (
                <li key={s.id} onClick={() => abrir(s.id)} style={{ cursor: "pointer", padding: "11px 8px", borderRadius: 12, background: sel?.id === s.id ? "rgba(220,229,122,.08)" : undefined }}>
                  <div className="tx"><b>{s.solicitante}</b><span><span className="maq">{s.numero}</span> · {s.tipo_nombre} · {s.documentos} doc.</span></div>
                  <div style={{ display: "grid", justifyItems: "end", gap: 4 }}><span className={`chip ${claseEstado[s.estado]}`}>{s.estado_nombre}</span><Plazo dias={s.dias_habiles} /></div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel" style={{ display: "grid", gap: 14, alignContent: "start" }}>
          {!sel ? (
            <div style={{ display: "grid", gap: 10 }}>
              <h2 style={{ fontSize: "1.05rem" }}>Así se atiende una solicitud</h2>
              <ol className="pasos-sol gris" style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6, fontSize: ".88rem" }}>
                <li>Regístrala con el tipo: el plazo en días hábiles se calcula solo.</li>
                <li>Si pones el DNI, Arriera sugiere los documentos de esa persona.</li>
                <li>Elige qué ocultar: las cajas negras se queman en la imagen y la copia no lleva texto oculto.</li>
                <li>Cada copia lleva el número de solicitud y queda en la auditoría y en el panel de datos sensibles.</li>
              </ol>
            </div>
          ) : (
            <>
              <div className="panel-cab" style={{ margin: 0, alignItems: "flex-start" }}>
                <div><h2 style={{ fontSize: "1.1rem" }}>{sel.solicitante}</h2>
                  <span className="sub"><span className="maq lima">{sel.numero}</span> · {sel.tipo_nombre}{sel.relacion ? ` · ${sel.relacion}` : ""}{sel.documento ? ` · DNI ${sel.documento}` : ""}</span></div>
                <div style={{ display: "grid", justifyItems: "end", gap: 4 }}><span className={`chip ${claseEstado[sel.estado]}`}>{sel.estado_nombre}</span><Plazo dias={sel.dias_habiles} /></div>
              </div>
              <div className="gris" style={{ fontSize: ".84rem" }}>Recibida el {fecha(sel.recibida)} · vence el {fecha(sel.vence)} ({sel.plazo_dias} días hábiles){sel.contacto ? ` · contacto: ${sel.contacto}` : ""}</div>
              {sel.detalle && <p style={{ fontSize: ".88rem" }}>{sel.detalle}</p>}

              <div style={{ display: "grid", gap: 8 }}>
                <b style={{ fontWeight: 500, color: "var(--blanco)" }}>Documentos de la copia · {sel.items.length}</b>
                {sel.items.length === 0 && <p className="gris2" style={{ fontSize: ".84rem" }}>Todavía no hay documentos. Usa las sugerencias o busca abajo.</p>}
                {sel.items.map((d) => <FilaDoc key={d.id} d={d} etiqueta="Quitar" icono="x" accion={() => abierta && hacer(() => quitarDeSolicitud(sel.id, d.id))} />)}
              </div>

              {abierta && sel.sugeridos.length > 0 && (
                <div style={{ display: "grid", gap: 8 }}>
                  <b style={{ fontWeight: 500, color: "var(--blanco)" }}><span className="ia"><Icono n="ia" /></span> De la misma persona (por DNI)</b>
                  {sel.sugeridos.map((d) => <FilaDoc key={d.id} d={d} etiqueta="Agregar" icono="mas" accion={() => hacer(() => agregarASolicitud(sel.id, d.id))} />)}
                </div>
              )}

              {abierta && (
                <form onSubmit={buscar} className="buscador" style={{ maxWidth: "none" }}>
                  <Icono n="busqueda" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Busca por nombre, tipo o DNI" aria-label="Buscar documentos" />
                  <button className="btn btn-sec btn-chico" type="submit">Buscar</button>
                </form>
              )}
              {abierta && hallados && (hallados.length === 0 ? <p className="gris2" style={{ fontSize: ".84rem" }}>Sin resultados.</p> :
                hallados.filter((d) => !enSel.has(d.id)).slice(0, 8).map((d) => <FilaDoc key={d.id} d={d} etiqueta="Agregar" icono="mas" accion={() => hacer(() => agregarASolicitud(sel.id, d.id))} />))}

              {abierta && sel.items.length > 0 && tipos && (
                <div style={{ display: "grid", gap: 8 }}>
                  <b style={{ fontWeight: 500, color: "var(--blanco)" }}>Qué ocultar en la copia</b>
                  {tipos.ocultamientos.map((o) => <label key={o.key} className="radio-op"><input type="radio" name="oculto" checked={oculto === o.key} onChange={() => setOculto(o.key)} />{o.nombre}</label>)}
                  <button className="btn btn-prim" disabled={ocupado} onClick={() => hacer(() => generarCopia(sel.id, oculto))}><Icono n="doc" />{ocupado ? "Generando…" : sel.copia ? "Volver a generar la copia" : "Generar copia"}</button>
                </div>
              )}

              {sel.copia && (
                <div className="aviso" style={{ borderColor: "rgba(169,182,64,.4)", background: "rgba(169,182,64,.07)", color: "var(--texto)" }}>
                  <Icono n="check" /><span>Copia de {sel.copia.paginas} páginas · huella <span className="maq">{sel.copia.sha256.slice(0, 16)}…</span>. Cada página lleva el número de solicitud y la leyenda «no reemplaza al original».</span>
                </div>
              )}
              {abierta && <div className="campo-f"><label htmlFor="nota-sol">Nota de entrega o motivo de rechazo</label><input id="nota-sol" className="inp" value={nota} onChange={(e) => setNota(e.target.value)} placeholder="Entregada en mesa de partes, por correo…" /></div>}
              {sel.nota_entrega && <p className="gris" style={{ fontSize: ".84rem" }}>Nota: {sel.nota_entrega}</p>}
              <div className="acciones">
                {sel.copia && <a className="btn btn-sec" href={urlCopiaSolicitud(sel.id)}><Icono n="descargar" />Descargar copia</a>}
                {abierta && sel.copia && <button className="btn btn-lima" disabled={ocupado} onClick={() => hacer(() => cambiarEstadoSolicitud(sel.id, "entregada", nota)).then(() => setNota(""))}><Icono n="check" />Marcar entregada</button>}
                {abierta && <button className="btn btn-peligro" disabled={ocupado} onClick={() => { if (!nota.trim()) { setError("Escribe el motivo del rechazo en la nota."); return; } hacer(() => cambiarEstadoSolicitud(sel.id, "rechazada", nota)).then(() => setNota("")); }}>Rechazar</button>}
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <span className="nav-t" style={{ padding: 0 }}>Historial</span>
                <ul className="linea-tiempo">{sel.historial.map((h, i) => <li key={i}><span><b style={{ fontWeight: 500, color: "var(--blanco)" }}>{h.accion.replace("_", " ")}</b> · {new Date(h.fecha).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" })} · {h.por}{h.detalle ? <span className="gris2"> · {h.detalle}</span> : null}</span></li>)}</ul>
              </div>
            </>
          )}
        </div>
      </div>

      {nueva && tipos && (
        <div className="modal-fondo" onClick={() => setNueva(false)}>
          <form className="modal" role="dialog" aria-modal="true" aria-labelledby="t-sol" onClick={(e) => e.stopPropagation()} onSubmit={crear} style={{ width: "min(600px,100%)" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-sol">Nueva solicitud</h2><button type="button" className="icono-btn" aria-label="Cerrar" onClick={() => setNueva(false)}><Icono n="x" /></button></div>
            <div className="campo-f"><label htmlFor="tipo">Qué pide</label>
              <select id="tipo" name="tipo" className="inp" defaultValue="copia">{tipos.tipos.map((t) => <option key={t.key} value={t.key}>{t.nombre} · {t.plazo_dias} días hábiles</option>)}</select></div>
            <div className="rejilla r2" style={{ gap: 12 }}>
              <div className="campo-f"><label htmlFor="solicitante">Nombre de quien pide</label><input id="solicitante" name="solicitante" className="inp" required minLength={3} /></div>
              <div className="campo-f"><label htmlFor="documento">DNI (opcional)</label><input id="documento" name="documento" className="inp maq" inputMode="numeric" maxLength={12} /></div>
              <div className="campo-f"><label htmlFor="relacion">Relación con el titular</label><input id="relacion" name="relacion" className="inp" placeholder="titular, apoderado, familiar…" /></div>
              <div className="campo-f"><label htmlFor="contacto">Correo o teléfono (opcional)</label><input id="contacto" name="contacto" className="inp" /></div>
            </div>
            <div className="campo-f"><label htmlFor="detalle">Detalle del pedido</label><textarea id="detalle" name="detalle" className="inp" rows={3} placeholder="Qué documentos, de qué años, para qué trámite" /></div>
            <p className="gris2" style={{ fontSize: ".78rem" }}>El DNI y el contacto se guardan cifrados. Los plazos los ajusta la administración según su norma y su política.</p>
            {error && <p className="error-form">{error}</p>}
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button type="button" className="btn btn-sec" onClick={() => setNueva(false)}>Cancelar</button><button className="btn btn-prim" type="submit" disabled={ocupado}>Registrar</button></div>
          </form>
        </div>
      )}
    </>
  );
}
