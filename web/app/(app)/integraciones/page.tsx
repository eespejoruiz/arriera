import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { integraciones, webhooks, cliente } from "@/lib/demo";

export const metadata = { title: "Integraciones" };

export default function Integraciones() {
  return (
    <>
      <Cab titulo="Integraciones" maq="Arriera como módulo de tu ERP" desc="Llaves de API, permisos y avisos para que tu ERP envíe documentos, consulte datos y muestre el visor dentro de sus pantallas.">
        <button className="btn btn-sec"><Icono n="doc" />Documentación del API</button>
        <button className="btn btn-prim"><Icono n="mas" />Nueva integración</button>
      </Cab>
      <div className="rejilla r2">
        {integraciones.map((i) => (
          <div className="panel" key={i.nombre}>
            <div className="panel-cab"><div style={{ display: "flex", gap: 12, alignItems: "center" }}><span className="ic-cuadro"><Icono n="integraciones" /></span><div><h2>{i.nombre}</h2><span className="sub">{i.sistema}</span></div></div><span className={`estado ${i.estado}`}><i />{i.estado === "on" ? "Activa" : "Revisar"}</span></div>
            <div className="rejilla r2" style={{ gap: 12, fontSize: ".84rem" }}>
              <div><span className="gris2">Actividad</span><br />{i.llamadas}</div>
              <div><span className="gris2">Última llamada</span><br />{i.ultima}</div>
              <div style={{ gridColumn: "1 / -1" }}><span className="gris2">Techo de permisos</span><br />{i.techo} <span className="chip falta" style={{ marginLeft: 4 }}>Sin acceso a N3</span></div>
            </div>
            <div className="acciones" style={{ marginTop: 14 }}><button className="btn btn-sec btn-chico"><Icono n="llave" />Rotar llave</button><button className="btn btn-sec btn-chico">Permisos</button><button className="btn btn-sec btn-chico">Ver registros</button></div>
          </div>
        ))}
      </div>
      <div className="rejilla r-64">
        <div className="panel">
          <div className="panel-cab"><h2>Llaves de API</h2><span className="sub">Se muestran una sola vez al crearlas</span></div>
          <div className="tabla-env"><table className="tabla">
            <thead><tr><th>Llave</th><th>Integración</th><th>Alcances</th><th>Último uso</th></tr></thead>
            <tbody>
              <tr><td className="maq lima">ark_live_7f2c••••</td><td>Odoo {cliente.nombre}</td><td className="gris">documentos:escribir, documentos:leer, busqueda, embed:emitir</td><td className="gris">hace 1 min</td></tr>
              <tr><td className="maq lima">ark_live_19ad••••</td><td>Starsoft Contabilidad</td><td className="gris">documentos:escribir, documentos:leer</td><td className="gris">hace 14 min</td></tr>
              <tr><td className="maq gris2">ark_test_c08e••••</td><td>Pruebas</td><td className="gris">todos (solo DATOS DEMO)</td><td className="gris">ayer</td></tr>
            </tbody>
          </table></div>
        </div>
        <div className="panel">
          <div className="panel-cab"><h2>Webhooks</h2><button className="btn btn-sec btn-chico">Probar</button></div>
          {webhooks.map((w) => (
            <div key={w.url} style={{ display: "grid", gap: 8, fontSize: ".84rem" }}>
              <span className="maq lima" style={{ overflowWrap: "anywhere" }}>{w.url}</span>
              <span className="gris">{w.eventos}</span>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><span className="chip ok">Entregas {w.ok}</span><span className="chip neutro">{w.ult}</span><span className="chip neutro">Firma HMAC-SHA256</span></div>
            </div>
          ))}
        </div>
      </div>
      <div className="panel plano">
        <div className="panel-cab"><h2>Visor embebido</h2><span className="sub">Así se ve un expediente dentro de la ficha del contacto en Odoo</span></div>
        <div className="rejilla r-46">
          <pre className="maq" style={{ margin: 0, background: "#0B0D07", border: "1px solid var(--linea)", borderRadius: 12, padding: 14, fontSize: ".78rem", overflowX: "auto", color: "#D9DDCB", fontFamily: "ui-monospace, Menlo, Consolas, monospace" }}>{`POST /v1/embed/tokens
{ "alcance": "persona",
  "referencia_erp": "res.partner/1842",
  "usuario_externo": "odoo:jperez",
  "vida_segundos": 600 }

→ <iframe src="https://archivo.${cliente.dominio}
   /embed/persona/…?t=eyJ…">`}</pre>
          <div className="panel" style={{ background: "#F5F5F2", color: "#333", borderColor: "#ddd", padding: 0, overflow: "hidden" }}>
            <div style={{ background: "#71639e", color: "#fff", padding: "8px 14px", fontSize: ".8rem", fontFamily: "Arial, sans-serif" }}>Odoo · Contactos › Rosa Huamán Quispe</div>
            <div style={{ display: "flex", gap: 14, padding: "8px 14px", fontSize: ".78rem", borderBottom: "1px solid #ddd", fontFamily: "Arial, sans-serif" }}><span>Información</span><span>Ventas</span><b style={{ borderBottom: "2px solid #71639e", paddingBottom: 6 }}>Documentos (Arriera)</b></div>
            <div style={{ margin: 12, borderRadius: 12, background: "var(--musgo)", padding: 12, display: "grid", gap: 8, color: "var(--texto)" }}>
              {["Solicitud de subsidio · 14/03/2018", "Informe médico · 02/03/2018 · N3 oculto", "Resolución de aprobación · 02/05/2018"].map((t) => <div key={t} className="doc-item" style={{ padding: "8px 10px" }}><span className="ic-cuadro" style={{ width: 28, height: 28 }}><Icono n="doc" /></span><div className="tx"><b style={{ fontSize: ".84rem" }}>{t}</b></div></div>)}
              <span className="chip falta" style={{ justifySelf: "start" }}>Falta boleta de pago</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
