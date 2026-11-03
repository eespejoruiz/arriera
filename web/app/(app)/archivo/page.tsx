import Link from "next/link";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { resultados, cajas } from "@/lib/demo";

export const metadata = { title: "Archivo" };

const expedientes = [
  ...resultados.map((r) => ({ ...r, tramite: "Subsidio por enfermedad", anio: "2018", completo: false })),
  { exp: "2018-0390", titular: "María Quispe Torres", caja: "C-0045", tramite: "Subsidio por enfermedad", anio: "2018", completo: true, docs: [], campo: ["", "", ""] },
  { exp: "2018-0401", titular: "Elena Pari Choque", caja: "C-0045", tramite: "Subsidio por enfermedad", anio: "2018", completo: true, docs: [], campo: ["", "", ""] },
  { exp: "2018-0455", titular: "Gloria Ramos Vela", caja: "C-0046", tramite: "Subsidio por fallecimiento", anio: "2018", completo: true, docs: [], campo: ["", "", ""] },
];

export default function Archivo() {
  return (
    <>
      <Cab titulo="Archivo" maq="fondo, serie, subserie y expediente" desc="La estructura del archivo de FAMENSSALUD. Puedes crear, renombrar y mover carpetas; cada cambio queda registrado.">
        <button className="btn btn-sec"><Icono n="mas" />Nueva carpeta</button>
        <Link className="btn btn-prim" href="/busqueda/"><Icono n="busqueda" />Buscar en el archivo</Link>
      </Cab>
      <div className="rejilla arch-grid">
        <div className="panel plano">
          <ul className="arbol">
            <li><span className="n"><b style={{ color: "var(--blanco)", fontWeight: 500 }}>FAMENSSALUD</b><small>48,210</small></span>
              <ul>
                <li><a href="#">Asociados<small>12,310</small></a></li>
                <li><a href="#">Aportes<small>4,210</small></a></li>
                <li><span className="n">Beneficios<small>21,840</small></span>
                  <ul>
                    <li><a href="#" className="on">Subsidio por enfermedad<small>14,902</small></a></li>
                    <li><a href="#">Subsidio por fallecimiento<small>4,388</small></a></li>
                    <li><a href="#">Apoyos y otros beneficios<small>2,550</small></a></li>
                  </ul>
                </li>
                <li><a href="#">Préstamos<small>8,120</small></a></li>
                <li><a href="#">Gobierno<small>1,730</small></a></li>
                <li><a href="#">Administración y contabilidad<small>—</small></a></li>
                <li><a href="#">Correspondencia<small>—</small></a></li>
              </ul>
            </li>
          </ul>
        </div>
        <div className="panel">
          <div className="panel-cab">
            <div><h2>Subsidio por enfermedad</h2><span className="sub">Beneficios · 1,284 expedientes · requisitos: solicitud, informe o certificado médico, boleta de pago y resolución</span></div>
            <div className="tabs"><button className="on">2018</button><button>2017</button><button>2019</button><button>Todos</button></div>
          </div>
          <div className="tabla-env">
            <table className="tabla">
              <thead><tr><th>Expediente</th><th>Titular</th><th>Ubicación física</th><th>Requisitos</th><th /></tr></thead>
              <tbody>
                {expedientes.map((e) => (
                  <tr key={e.exp} className="fila-link">
                    <td><Link href="/expedientes/2018-0412/" className="t-princ maq">{e.exp}</Link><span className="t-sec">{e.tramite}</span></td>
                    <td>{e.titular}</td>
                    <td className="gris"><span className="maq">{e.caja}</span> · estante {cajas.find((c) => c.codigo === e.caja)?.estante}</td>
                    <td>{e.completo ? <span className="chip ok">Completo</span> : <span className="chip falta">Falta boleta de pago</span>}</td>
                    <td><Link className="btn btn-sec btn-chico" href="/expedientes/2018-0412/">Abrir</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
