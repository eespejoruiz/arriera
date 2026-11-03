import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { depuracion as d } from "@/lib/demo";

export const metadata = { title: "Conservación" };

const reglas = [
  ["Comprobantes de pago", "10 años desde la fecha", "Eliminar papel y digital"],
  ["Correspondencia recibida", "5 años desde la fecha", "Eliminar papel, conservar digital"],
  ["Solicitudes de subsidio", "Cierre del expediente + 10 años", "Conservar digital"],
  ["Actas de asamblea", "Permanente", "Conservar"],
];

export default function Conservacion() {
  return (
    <>
      <Cab titulo="Conservación" maq="nada se elimina sin un acta aprobada" desc="Plazos por tipo de documento. Cada mes Arriera propone qué vence; una persona revisa, un comité aprueba y el sistema genera el acta.">
        <button className="btn btn-sec"><Icono n="ajustes" />Reglas de conservación</button>
      </Cab>
      <div className="rejilla r-64">
        <div className="panel luz">
          <div className="panel-cab"><div><h2>{d.numero}</h2><span className="sub">Generada por el sistema el 01/11/2026</span></div><span className="chip duda">{d.estado}</span></div>
          <div className="rejilla r3" style={{ marginBottom: 16 }}>
            <div className="stat"><span className="l">Documentos vencidos</span><span className="v">{d.total.toLocaleString("en-US")}</span></div>
            <div className="stat"><span className="l">Excluidos por bloqueo legal</span><span className="v" style={{ color: "var(--ambar)" }}>{d.excluidos}</span></div>
            <div className="stat"><span className="l">Cajas que se liberan</span><span className="v">13</span></div>
          </div>
          <div className="tabla-env">
            <table className="tabla">
              <thead><tr><th>Serie</th><th>Regla aplicada</th><th className="num">Documentos</th><th>Cajas</th></tr></thead>
              <tbody>{d.grupos.map((g) => (
                <tr key={g.serie}><td className="t-princ">{g.serie}{g.bloqueo ? <span className="t-sec" style={{ color: "var(--ambar)" }}>{g.bloqueo}</span> : null}</td><td className="gris">{g.regla}</td><td className="num">{g.docs}</td><td className="maq">{g.cajas}</td></tr>
              ))}</tbody>
            </table>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 16 }}>
            <button className="btn btn-prim"><Icono n="check" />Enviar al comité para aprobación</button>
            <button className="btn btn-sec">Quitar o agregar documentos</button>
          </div>
        </div>
        <div className="panel">
          <div className="panel-cab"><h2>Flujo del acta</h2></div>
          <ol className="linea-t">
            <li><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Propuesta del sistema</b><br /><span className="gris2" style={{ fontSize: ".8rem" }}>01/11 · documentos vencidos por regla</span></li>
            <li><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Revisión de la archivera</b><br /><span className="gris2" style={{ fontSize: ".8rem" }}>En curso · Ana R.</span></li>
            <li className="falta"><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Aprobación del comité</b><br /><span className="gris2" style={{ fontSize: ".8rem" }}>Pendiente · firma de 2 aprobadores</span></li>
            <li className="falta"><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Acta de depuración numerada</b><br /><span className="gris2" style={{ fontSize: ".8rem" }}>PDF con hashes y QR de verificación</span></li>
            <li className="falta"><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Ejecución</b><br /><span className="gris2" style={{ fontSize: ".8rem" }}>Papel: lo destruye la institución · digital: purga a los 30 días</span></li>
          </ol>
        </div>
      </div>
      <div className="panel plano">
        <div className="panel-cab"><h2>Reglas vigentes</h2><span className="sub">Las fija la institución con su asesoría legal</span></div>
        <div className="tabla-env"><table className="tabla"><thead><tr><th>Tipo documental</th><th>Plazo</th><th>Destino</th></tr></thead>
          <tbody>{reglas.map(([a, b, c]) => <tr key={a}><td className="t-princ">{a}</td><td className="gris">{b}</td><td><span className={`chip ${c.startsWith("Conservar") ? "ok" : "neutro"}`}>{c}</span></td></tr>)}</tbody></table></div>
      </div>
    </>
  );
}
