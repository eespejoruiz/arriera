// Vista de solicitudes sin servidor (DATOS DEMO), para la web estática.
import { Cab } from "@/components/ui";

const filas = [
  { n: "S-2026-00014", q: "Rosa H. Q.", t: "Copia de historia clínica", e: "En búsqueda", p: "3 días hábiles", c: "duda" },
  { n: "S-2026-00013", q: "Carmen R. P.", t: "Copia de expediente", e: "Copia lista", p: "1 día hábil", c: "ok" },
  { n: "S-2026-00012", q: "Lucía V. M.", t: "Acceso a datos personales (Ley 29733)", e: "Recibida", p: "17 días hábiles", c: "info" },
];

export default function SolicitudesDemo() {
  return (
    <>
      <Cab titulo="Solicitudes" maq="copias y acceso, con plazo a la vista" desc="Registra el pedido, junta los documentos, emite la copia con lo sensible oculto y deja constancia de la entrega. DATOS DEMO." />
      <div className="panel"><ul className="lista-l">
        {filas.map((f) => <li key={f.n} style={{ padding: "11px 8px" }}><div className="tx"><b>{f.q}</b><span><span className="maq">{f.n}</span> · {f.t}</span></div><div style={{ display: "grid", justifyItems: "end", gap: 4 }}><span className={`chip ${f.c}`}>{f.e}</span><span className="plazo ok">{f.p}</span></div></li>)}
      </ul></div>
    </>
  );
}
