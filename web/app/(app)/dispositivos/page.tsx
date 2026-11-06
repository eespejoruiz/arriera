"use client";
import { useState } from "react";
import { Cab, QR } from "@/components/ui";
import Icono from "@/components/Icono";
import { dispositivos, cliente } from "@/lib/demo";

const tipos = [
  { k: "escaner", t: "Escáner USB", d: "Ricoh, Fujitsu, Epson, Canon y otros con TWAIN o WIA", i: "escaner" },
  { k: "celular", t: "Celular", d: "Android o iPhone, desde el navegador", i: "celular" },
  { k: "red", t: "Multifuncional de red", d: "Escanear a carpeta, FTP o correo", i: "red" },
  { k: "pistola", t: "Lector de QR o barras", d: "USB o Bluetooth, modo teclado", i: "pistola" },
];

export default function Dispositivos() {
  const [nuevo, setNuevo] = useState<string | null>(null);
  const [lectura, setLectura] = useState("");
  return (
    <>
      <Cab titulo="Dispositivos" maq="escáneres, celulares, multifuncionales y lectores" desc="Todo lo que alimenta el archivo. Cada dispositivo se registra con un código de un solo uso y queda ligado a una estación y a sus operadores.">
        <button className="btn btn-prim" onClick={() => setNuevo("escaner")}><Icono n="mas" />Agregar dispositivo</button>
      </Cab>

      {tipos.map((t) => {
        const lista = dispositivos.filter((d) => d.tipo === t.k);
        return (
          <div className="panel" key={t.k}>
            <div className="panel-cab"><div style={{ display: "flex", gap: 12, alignItems: "center" }}><span className="ic-cuadro"><Icono n={t.i} /></span><div><h2>{t.t}</h2><span className="sub">{t.d}</span></div></div><button className="btn btn-sec btn-chico" onClick={() => setNuevo(t.k)}><Icono n="mas" />Agregar</button></div>
            <div className="tabla-env"><table className="tabla">
              <thead><tr><th>Dispositivo</th><th>Conexión</th><th>Estado</th><th /></tr></thead>
              <tbody>{lista.map((d) => (
                <tr key={d.id}>
                  <td><span className="t-princ">{d.nombre}</span><span className="t-sec">{d.detalle}</span></td>
                  <td className="gris">{d.via}</td>
                  <td><span className={`estado ${d.estado}`}><i />{d.nota}</span></td>
                  <td style={{ textAlign: "right" }}><button className="btn btn-sec btn-chico">Configurar</button></td>
                </tr>
              ))}</tbody>
            </table></div>
          </div>
        );
      })}

      {nuevo && (
        <div className="modal-fondo" onClick={() => setNuevo(null)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="t-disp" onClick={(e) => e.stopPropagation()}>
            <div className="panel-cab" style={{ margin: 0 }}><h2 id="t-disp">Agregar dispositivo</h2><button className="icono-btn" aria-label="Cerrar" onClick={() => setNuevo(null)}><Icono n="x" /></button></div>
            <div className="tabs">{tipos.map((t) => <button key={t.k} className={nuevo === t.k ? "on" : ""} onClick={() => setNuevo(t.k)}>{t.t}</button>)}</div>
            {nuevo === "escaner" && (
              <ol style={{ display: "grid", gap: 12, paddingLeft: 18, margin: 0 }}>
                <li>Instala el <b>agente de captura de Arriera</b> en la computadora con Windows donde está conectado el escáner. <button className="btn btn-sec btn-chico" style={{ marginLeft: 6 }}><Icono n="descargar" />Descargar instalador</button></li>
                <li>Al abrirlo, ingresa este código de registro de un solo uso: <b className="maq lima" style={{ fontSize: "1.2rem", letterSpacing: ".08em" }}>KX7-29Q-M4P</b> <span className="gris2">(vence en 15 min)</span></li>
                <li>El agente detecta el escáner (TWAIN o WIA) y crea el perfil <b className="maq">Arriera 300 dpi</b>: doble cara, escala de grises, sin borrar páginas en blanco.</li>
                <li>Listo: la estación aparece aquí en línea y empieza a enviar latidos cada minuto.</li>
              </ol>
            )}
            {nuevo === "celular" && (
              <div className="rejilla r2" style={{ alignItems: "center" }}>
                <div style={{ background: "#F4F5EE", borderRadius: 14, padding: 12, justifySelf: "center" }}><QR texto="https://demo.arriera.tech/m/?emparejar=7H2K" tam={180} /></div>
                <div style={{ display: "grid", gap: 10 }}>
                  <p>Abre la cámara del celular y escanea el código. Se abre la app de captura en el navegador, ya emparejada con tu usuario.</p>
                  <p className="gris" style={{ fontSize: ".84rem" }}>No hay que instalar nada. Las fotos se recortan, se corrigen y se suben cifradas; no quedan guardadas en la galería del teléfono.</p>
                  <span className="gris2" style={{ fontSize: ".78rem" }}>El código vence en 10 minutos.</span>
                </div>
              </div>
            )}
            {nuevo === "red" && (
              <div style={{ display: "grid", gap: 12 }}>
                <p>Configura en la multifuncional un destino de escaneo. Arriera acepta cualquiera de estos:</p>
                <div className="rejilla r3" style={{ gap: 10 }}>
                  {[["Carpeta de red (SMB)", "\\\\arriera\\entrada-red"], ["FTP seguro (SFTP)", "sftp://captura.arriera.local"], ["Correo", `escaneos@${cliente.dominio.replace(".demo", "")}.arriera.tech`]].map(([t, v]) => (
                    <div className="panel plano" key={t} style={{ padding: 12, display: "grid", gap: 6 }}><b style={{ color: "var(--blanco)", fontWeight: 500, fontSize: ".86rem" }}>{t}</b><span className="maq lima" style={{ fontSize: ".78rem", overflowWrap: "anywhere" }}>{v}</span></div>
                  ))}
                </div>
                <p className="gris" style={{ fontSize: ".84rem" }}>Usuario y contraseña se generan para cada equipo. Arriera asocia cada archivo a su lote leyendo la hoja QR de la primera página.</p>
              </div>
            )}
            {nuevo === "pistola" && (
              <div style={{ display: "grid", gap: 12 }}>
                <p>Conecta el lector por USB o Bluetooth en modo teclado. No necesita drivers. Pruébalo leyendo la etiqueta de una caja:</p>
                <input id="prueba-lector" className="inp maq" autoFocus value={lectura} onChange={(e) => setLectura(e.target.value)} placeholder="Escanea una etiqueta…" aria-label="Prueba del lector" />
                {lectura ? <div className="aviso verde"><Icono n="check" /><span>Lectura recibida: <b className="maq">{lectura}</b>. Arriera reconoce cajas (<span className="maq">ARR1|C|…</span>), lotes y expedientes.</span></div> : null}
              </div>
            )}
            <div style={{ display: "flex", justifyContent: "flex-end" }}><button className="btn btn-prim" onClick={() => setNuevo(null)}>Listo</button></div>
          </div>
        </div>
      )}
    </>
  );
}
