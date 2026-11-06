"use client";
import { useState } from "react";
import Link from "next/link";
import { Cab, QR } from "@/components/ui";
import Icono from "@/components/Icono";
import { lotes, estadoLote, rechazos, dispositivos, cajas, cliente } from "@/lib/demo";

const origenes = [
  { k: "usb", t: "Escáner USB", d: "Ricoh fi-8170 en Estación Archivo 1", i: "escaner" },
  { k: "cel", t: "Celular", d: "Empareja un teléfono con un QR", i: "celular" },
  { k: "red", t: "Multifuncional de red", d: "Ricoh IM 430 · escanear a carpeta", i: "red" },
  { k: "web", t: "Subir archivos", d: "PDF, TIFF o JPG desde esta computadora", i: "descargar" },
];

export default function CapturaDemo() {
  const [modal, setModal] = useState(false);
  const [origen, setOrigen] = useState("usb");
  const [caja, setCaja] = useState("C-0047");
  const [creado, setCreado] = useState(false);
  const codigo = "L-2026-000188";
  return (
    <>
      <Cab titulo="Captura" maq="cada hoja entra con su caja y su lote" desc="Crea lotes, imprime la hoja de lote y sigue en vivo lo que llega de escáneres, celulares y multifuncionales.">
        <Link className="btn btn-sec" href="/m/"><Icono n="celular" />Vista del celular</Link>
        <button className="btn btn-prim" onClick={() => { setModal(true); setCreado(false); }}><Icono n="mas" />Nuevo lote</button>
      </Cab>

      <div className="aviso verde"><Icono n="qr" /><span><b>Lector QR listo en Estación Archivo 1.</b> Escanea la etiqueta de una caja o de un lote y Arriera abre su ficha sin tipear.</span></div>

      <div className="rejilla r4">
        {dispositivos.filter((d) => d.tipo !== "pistola").slice(0, 4).map((d) => (
          <div className="panel" key={d.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
              <span className="ic-cuadro"><Icono n={d.tipo} /></span>
              <span className={`estado ${d.estado}`}><i />{d.estado === "on" ? "En línea" : d.estado === "warn" ? "Atención" : "Sin conexión"}</span>
            </div>
            <b style={{ display: "block", marginTop: 12, color: "var(--blanco)", fontWeight: 500 }}>{d.nombre}</b>
            <span className="gris2" style={{ fontSize: ".78rem" }}>{d.detalle}</span>
            <p style={{ marginTop: 8, fontSize: ".82rem" }} className={d.nota.startsWith("Escaneando") ? "lima" : "gris"}>{d.nota}</p>
          </div>
        ))}
      </div>

      <div className="rejilla r-73">
        <div className="panel">
          <div className="panel-cab"><h2>Lotes de hoy</h2><div className="tabs"><button className="on">Todos</button><button>Míos</button><button>Con rechazos</button></div></div>
          <div className="tabla-env">
            <table className="tabla">
              <thead><tr><th>Lote</th><th>Caja</th><th>Origen</th><th className="num">Páginas</th><th>Estado</th><th /></tr></thead>
              <tbody>
                {lotes.map((l) => (
                  <tr key={l.codigo} className="fila-link">
                    <td><span className="t-princ maq">{l.codigo}</span><span className="t-sec">{l.operador} · {l.hora}</span></td>
                    <td className="maq">{l.caja}</td>
                    <td className="gris">{l.origen}</td>
                    <td className="num">
                      {l.paginas}{l.estado === "recibiendo" ? <span className="gris2"> / {l.esperadas}</span> : null}
                      {l.estado === "recibiendo" ? <div className="barra-prog" style={{ marginTop: 5, width: 90 }}><i style={{ width: `${(l.paginas / l.esperadas) * 100}%` }} /></div> : null}
                    </td>
                    <td><span className={`chip ${estadoLote[l.estado].c}`}>{estadoLote[l.estado].t}</span></td>
                    <td><button className="btn btn-sec btn-chico">Abrir</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-cab"><h2>Volver a escanear</h2><span className="chip duda">3 páginas</span></div>
          <p className="gris" style={{ fontSize: ".84rem", marginBottom: 12 }}>Lote <span className="maq lima">L-2026-000185</span>. Imprime la hoja de reescaneo y pasa solo estas páginas.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
            {rechazos.map((r, i) => (
              <div key={r.pagina} style={{ display: "grid", gap: 6 }}>
                <div className="papel" style={{ padding: "10%", fontSize: 4, transform: i === 0 ? "rotate(-9deg) scale(.92)" : undefined, filter: i === 1 ? "blur(1.4px)" : undefined, clipPath: i === 2 ? "inset(0 18% 0 0)" : undefined }}>
                  <div style={{ height: 4, background: "#24211B", width: "60%", margin: "0 auto 6px" }} />
                  {Array.from({ length: 9 }).map((_, k) => <div key={k} style={{ height: 2, background: "#8A8273", margin: "5px 0", width: `${70 + ((k * 13) % 30)}%` }} />)}
                </div>
                <span style={{ fontSize: ".76rem" }}><b className="maq">pág. {r.pagina}</b><br /><span className="gris2">{r.motivo}</span></span>
              </div>
            ))}
          </div>
          <button className="btn btn-sec" style={{ width: "100%", marginTop: 14 }}><Icono n="doc" />Imprimir hoja de reescaneo</button>
        </div>
      </div>

      <div className="panel plano">
        <div className="panel-cab"><h2>Cajas en captura</h2><Link href="/archivo/" className="btn btn-sec btn-chico">Inventario completo</Link></div>
        <div className="rejilla r4">
          {cajas.map((c) => (
            <div key={c.codigo} style={{ display: "grid", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><b className="maq" style={{ color: "var(--blanco)", fontSize: "1.05rem" }}>{c.codigo}</b><span className="gris2" style={{ fontSize: ".78rem" }}>Estante {c.estante}</span></div>
              <span className="gris" style={{ fontSize: ".8rem" }}>{c.serie} · {c.anios}</span>
              <div className="barra-prog"><i style={{ width: `${(c.capturadas / c.estimadas) * 100}%` }} /></div>
              <span className="gris2 num" style={{ fontSize: ".76rem" }}>{c.capturadas.toLocaleString("en-US")} de {c.estimadas.toLocaleString("en-US")} páginas · {c.estado}</span>
            </div>
          ))}
        </div>
      </div>

      {modal && (
        <div className="modal-fondo" onClick={() => setModal(false)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="t-nuevo" onClick={(e) => e.stopPropagation()}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-nuevo">{creado ? "Lote creado" : "Nuevo lote"}</h2><button className="icono-btn" aria-label="Cerrar" onClick={() => setModal(false)}><Icono n="x" /></button></div>
            {!creado ? (
              <>
                <div className="campo-f"><label htmlFor="caja">Caja</label>
                  <select id="caja" className="inp" value={caja} onChange={(e) => setCaja(e.target.value)}>{cajas.map((c) => <option key={c.codigo} value={c.codigo}>{c.codigo} · {c.serie} {c.anios} · estante {c.estante}</option>)}</select>
                  <span className="gris2" style={{ fontSize: ".76rem" }}>También puedes leer la etiqueta de la caja con el lector QR.</span>
                </div>
                <div className="campo-f"><span className="et">¿Desde dónde vas a escanear?</span>
                  <div className="rejilla r2" style={{ gap: 10 }}>
                    {origenes.map((o) => (
                      <button key={o.k} type="button" onClick={() => setOrigen(o.k)} className="panel" style={{ textAlign: "left", cursor: "pointer", display: "flex", gap: 12, alignItems: "center", borderColor: origen === o.k ? "rgba(220,229,122,.6)" : undefined, background: origen === o.k ? "rgba(220,229,122,.08)" : undefined }}>
                        <span className="ic-cuadro"><Icono n={o.i} /></span>
                        <span><b style={{ display: "block", color: "var(--blanco)", fontWeight: 500 }}>{o.t}</b><span className="gris2" style={{ fontSize: ".78rem" }}>{o.d}</span></span>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="campo-f"><label htmlFor="esperadas">Páginas aproximadas (opcional)</label><input id="esperadas" className="inp" inputMode="numeric" placeholder="220" /></div>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button className="btn btn-sec" onClick={() => setModal(false)}>Cancelar</button><button className="btn btn-prim" onClick={() => setCreado(true)}>Crear lote</button></div>
              </>
            ) : (
              <div className="rejilla r2" style={{ alignItems: "center" }}>
                <div className="papel" style={{ display: "grid", justifyItems: "center", alignContent: "space-between", fontFamily: "Arial, sans-serif", padding: "8% 6%" }}>
                  <div style={{ textAlign: "center" }}><b style={{ fontSize: 13, letterSpacing: ".1em" }}>HOJA DE LOTE</b><br /><span style={{ fontSize: 9 }}>{cliente.nombre.toUpperCase()} (DEMO)</span></div>
                  <QR texto={`ARR1|B|${codigo}|${caja}`} tam={150} color="#14160F" fondo="#ECEBDF" />
                  <b style={{ fontSize: 18, fontFamily: "var(--f-maq)" }}>{codigo}</b>
                  <span style={{ fontSize: 9, textAlign: "center" }}>Caja {caja} · Ana R. · 03/11/2026 12:04<br /><b>Poner como primera hoja</b></span>
                </div>
                <div style={{ display: "grid", gap: 12 }}>
                  {origen === "cel" ? (
                    <>
                      <p>Escanea este código con el celular para emparejarlo con el lote. No hay que instalar nada.</p>
                      <div style={{ background: "#F4F5EE", borderRadius: 12, padding: 10, justifySelf: "start" }}><QR texto={`https://demo.arriera.tech/m/?lote=${codigo}`} tam={140} /></div>
                      <span className="gris2" style={{ fontSize: ".78rem" }}>El enlace vence en 10 minutos.</span>
                    </>
                  ) : origen === "red" ? (
                    <p>En la multifuncional elige el perfil <b className="maq lima">Arriera 300 dpi</b>. El archivo llega a la carpeta de red y Arriera lo asocia al lote por la hoja QR.</p>
                  ) : origen === "web" ? (
                    <p>Arrastra aquí los PDF del lote. Arriera calcula la huella SHA-256 y verifica la subida.</p>
                  ) : (
                    <p>Pon la hoja de lote primero y escanea con el perfil <b className="maq lima">Arriera 300 dpi</b>. El agente de la Estación Archivo 1 sube el archivo y verifica su huella.</p>
                  )}
                  <button className="btn btn-prim"><Icono n="doc" />Imprimir hoja de lote</button>
                  <button className="btn btn-sec" onClick={() => setModal(false)}>Listo</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
