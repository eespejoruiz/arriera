"use client";
import { useState } from "react";
import Link from "next/link";
import { Cab, Pagina, LeidoIA } from "@/components/ui";
import Icono from "@/components/Icono";
import { expediente as e } from "@/lib/demo";

export default function Visor() {
  const [doc, setDoc] = useState("d-2");
  const [pag, setPag] = useState(0);
  const [exportar, setExportar] = useState(false);
  const [ocultar, setOcultar] = useState({ dni: true, diag: true, firma: false });
  const actual = e.documentos.find((d) => d.id === doc)!;
  const variante = actual.tipo.startsWith("Informe") || actual.tipo.startsWith("Certificado") ? "informe" : "solicitud";
  return (
    <>
      <Cab titulo={`Expediente ${e.codigo}`} maq={e.titular} migas={<><Link href="/archivo/">Archivo</Link> › {e.serie}</>}>
        <button className="btn btn-sec" onClick={() => setExportar(true)}><Icono n="descargar" />Exportar con ocultamiento</button>
        <Link className="btn btn-prim" href="/busqueda/?q=asistente"><Icono n="asistente" />Preguntar al asistente</Link>
      </Cab>

      <div className="rejilla r4">
        <div className="panel"><div className="stat"><span className="l">Titular</span><span style={{ color: "var(--blanco)", fontWeight: 500 }}>{e.titular}</span><span className="gris2 maq">DNI {e.dni}</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Trámite</span><span style={{ color: "var(--blanco)", fontWeight: 500 }}>{e.tramite}</span><span className="gris2">{e.abierto} → {e.cerrado} · {e.estado}</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Ubicación física</span><span style={{ color: "var(--blanco)", fontWeight: 500 }} className="maq">Caja {e.caja}</span><span className="gris2">Estante {e.estante} · papel en archivo</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Requisitos</span><span style={{ display: "flex", flexWrap: "wrap", gap: 5, minWidth: 0 }}>{e.requisitos.map((r) => <span key={r.t} className={`chip ${r.ok ? "ok" : "falta"}`}>{r.ok ? "" : "Falta "}{r.t}</span>)}</span></div></div>
      </div>

      <div className="rejilla" style={{ gridTemplateColumns: "minmax(0,1fr)" }}>
        <div className="rejilla exp-grid">
          <div className="panel plano">
            <div className="panel-cab"><h2>Línea de tiempo</h2><span className="sub">{e.documentos.length} documentos</span></div>
            <ol className="linea-t">
              {e.documentos.map((d) => (
                <li key={d.id}>
                  <div className={"doc-item" + (doc === d.id ? " on" : "")} onClick={() => { setDoc(d.id); setPag(0); }}>
                    <span className="ic-cuadro"><Icono n="doc" /></span>
                    <div className="tx"><b>{d.tipo}</b><span>{d.fecha} · {d.paginas} pág.{d.nota ? ` · ${d.nota}` : ""}</span></div>
                    <span className={`sens ${d.sens === "N3" ? "n3" : ""}`}>{d.sens}</span>
                    {d.estado === "duda" ? <span className="chip duda">Validar</span> : null}
                  </div>
                </li>
              ))}
              <li className="falta"><div className="doc-item falta"><span className="ic-cuadro" style={{ background: "transparent", border: "1px dashed rgba(224,122,78,.6)" }}><Icono n="alerta" /></span><div className="tx"><b>Boleta de pago</b><span>Requisito del trámite · no encontrado en el archivo</span></div></div></li>
            </ol>
          </div>

          <div className="panel" style={{ display: "grid", gap: 12 }}>
            <div className="visor-barra">
              <div><h2 style={{ fontSize: "1.05rem" }}>{actual.tipo}</h2><span className="gris2" style={{ fontSize: ".78rem" }}>Versión 1 · SHA-256 <span className="maq">9f3a…e21c</span> · capturado 03/11/2026 09:31</span></div>
              <div className="acciones">
                <button className="btn btn-sec btn-chico"><Icono n="busqueda" />Buscar aquí</button>
                <button className="btn btn-sec btn-chico"><Icono n="descargar" />Descargar con marca de agua</button>
              </div>
            </div>
            {actual.sens === "N3" ? <div className="aviso" style={{ fontSize: ".78rem" }}><Icono n="candado" /><span>Documento sensible (datos de salud). Lo ves porque tu perfil tiene acceso N3; esta vista queda en la auditoría.</span></div> : null}
            <div style={{ maxWidth: 560, width: "100%", justifySelf: "center" }}><Pagina variante={variante} marcar={pag === 0 ? "todo" : undefined} /></div>
            <div className="miniat-v">
              {Array.from({ length: actual.paginas }).map((_, i) => (
                <button key={i} className={pag === i ? "on" : ""} onClick={() => setPag(i)} aria-label={`Página ${i + 1}`}><div className="papel">{Array.from({ length: 6 }).map((_, k) => <div key={k} style={{ height: 2, background: "#8A8273", margin: "3px 0" }} />)}</div></button>
              ))}
            </div>
          </div>

          <div className="panel" style={{ display: "grid", gap: 10, alignContent: "start" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2>Datos</h2><LeidoIA /></div>
            {(variante === "informe"
              ? [["Paciente", "Rosa Huamán Quispe"], ["Fecha del informe", "02/03/2018"], ["Establecimiento", "Clínica San Gabriel"], ["Diagnóstico", "Validado por Luis V."], ["CIE-10", "M54.5"], ["Días de descanso", "15"]]
              : [["Titular", "Rosa Huamán Quispe"], ["DNI", "4•••••18"], ["Fecha", "14/03/2018"], ["Tipo", "Enfermedad"], ["Monto", "S/ 1,250.00"]]
            ).map(([k, v]) => (
              <div key={k} style={{ display: "grid", gap: 2, paddingBottom: 8, borderBottom: "1px solid var(--linea)" }}><span className="gris2" style={{ fontSize: ".76rem" }}>{k}</span><span className="maq" style={{ color: "var(--blanco)" }}>{v}</span></div>
            ))}
            <div className="panel-cab" style={{ margin: "8px 0 0" }}><h3 style={{ fontSize: ".92rem" }}>Historial</h3></div>
            <ul className="lista-l" style={{ fontSize: ".8rem" }}>
              <li><div className="tx"><b style={{ fontSize: ".82rem" }}>Carmen L. vio la página 1</b><span>hoy 11:46</span></div></li>
              <li><div className="tx"><b style={{ fontSize: ".82rem" }}>Luis V. validó el diagnóstico</b><span>03/11 10:20</span></div></li>
              <li><div className="tx"><b style={{ fontSize: ".82rem" }}>Indexado por la IA</b><span>03/11 09:34 · 98% de confianza</span></div></li>
            </ul>
          </div>
        </div>
      </div>

      {exportar && (
        <div className="modal-fondo" onClick={() => setExportar(false)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="t-exp" onClick={(ev) => ev.stopPropagation()} style={{ width: "min(560px,100%)" }}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-exp">Exportar con ocultamiento</h2><button className="icono-btn" aria-label="Cerrar" onClick={() => setExportar(false)}><Icono n="x" /></button></div>
            <p className="gris">Arriera quema recuadros negros sobre la imagen y rehace el PDF sin capa de texto oculta. El dato desaparece de verdad.</p>
            {([["dni", "DNI y otros documentos de identidad"], ["diag", "Diagnóstico y CIE-10"], ["firma", "Firmas y sellos"]] as const).map(([k, t]) => (
              <label key={k} style={{ display: "flex", gap: 10, alignItems: "center", cursor: "pointer" }}><input type="checkbox" id={`o-${k}`} checked={ocultar[k]} onChange={() => setOcultar((o) => ({ ...o, [k]: !o[k] }))} style={{ accentColor: "#DCE57A", width: 18, height: 18 }} />{t}</label>
            ))}
            <div className="campo-f"><label htmlFor="enlace">Entrega</label><select id="enlace" className="inp"><option>Enlace temporal de 72 h con contraseña</option><option>Descarga directa (ZIP)</option></select></div>
            <div className="aviso" style={{ fontSize: ".8rem" }}><Icono n="candado" /><span>Incluye documentos N3: la exportación necesita la aprobación de la archivera.</span></div>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button className="btn btn-sec" onClick={() => setExportar(false)}>Cancelar</button><button className="btn btn-prim" onClick={() => setExportar(false)}>Solicitar exportación</button></div>
          </div>
        </div>
      )}
    </>
  );
}
