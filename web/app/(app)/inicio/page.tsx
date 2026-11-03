import Link from "next/link";
import { Cab, Barras } from "@/components/ui";
import Icono from "@/components/Icono";
import { resumen as r, lotes, estadoLote, dispositivos } from "@/lib/demo";

export const metadata = { title: "Inicio" };

export default function Inicio() {
  const avance = Math.round((r.capturadas / r.estimadas) * 100);
  return (
    <>
      <Cab titulo="Buenos días, Ana" maq="El archivo va al 43%." desc="Avance del proyecto de digitalización 2015–2025 y lo que necesita tu atención hoy.">
        <Link className="btn btn-sec" href="/captura/"><Icono n="captura" />Ir a captura</Link>
        <Link className="btn btn-prim" href="/validacion/"><Icono n="validacion" />Validar 214 pendientes</Link>
      </Cab>

      <div className="rejilla r-64">
        <div className="panel luz">
          <div className="panel-cab"><h2>Avance del archivo</h2><span className="sub">Término estimado al ritmo actual: <b className="lima">{r.terminoEstimado}</b></span></div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap" }}>
            <span className="stat"><span className="v" style={{ fontSize: "2.6rem" }}>{r.capturadas.toLocaleString("en-US")}</span></span>
            <span className="gris">de {r.estimadas.toLocaleString("en-US")} páginas estimadas en el inventario</span>
          </div>
          <div className="barra-prog" style={{ height: 12, margin: "14px 0 18px" }}><i style={{ width: `${avance}%` }} /></div>
          <Barras datos={r.porDia} etiquetas={r.dias} />
        </div>
        <div className="rejilla" style={{ gap: 16 }}>
          <div className="rejilla r2 stats" style={{ gap: 16 }}>
            <div className="panel"><div className="stat"><span className="l">Páginas hoy</span><span className="v">{r.hoy.toLocaleString("en-US")}</span><span className="d">+12.4% frente a ayer</span></div></div>
            <div className="panel"><div className="stat"><span className="l">Aceptados por la IA</span><span className="v">{r.autoAceptados}%</span><span className="d">sin intervención humana</span></div></div>
            <div className="panel"><div className="stat"><span className="l">Por validar</span><span className="v">{r.pendientes}</span><span className="d" style={{ color: "var(--ambar)" }}>tiempo medio {r.tiempoValidacion}</span></div></div>
            <div className="panel"><div className="stat"><span className="l">Reescaneo</span><span className="v">{r.reescaneo}%</span><span className="d">de las páginas capturadas</span></div></div>
          </div>
          <div className="panel">
            <div className="panel-cab"><h3>Consumo de IA del mes</h3><span className="sub num">US$ {r.costoMes.toFixed(2)} de {r.presupuesto}</span></div>
            <div className="barra-prog"><i style={{ width: `${(r.costoMes / r.presupuesto) * 100}%` }} /></div>
            <p className="gris2" style={{ fontSize: ".78rem", marginTop: 8 }}>US$ 3.40 por cada mil páginas. Alerta al 80% y pausa del procesamiento al 100%.</p>
          </div>
        </div>
      </div>

      <div className="rejilla r-64">
        <div className="panel">
          <div className="panel-cab"><h2>Lotes de hoy</h2><Link className="btn btn-sec btn-chico" href="/captura/">Ver todos</Link></div>
          <div className="tabla-env">
            <table className="tabla">
              <thead><tr><th>Lote</th><th>Origen</th><th className="num">Páginas</th><th>Estado</th></tr></thead>
              <tbody>
                {lotes.slice(0, 5).map((l) => (
                  <tr key={l.codigo}>
                    <td><span className="t-princ maq">{l.codigo}</span><span className="t-sec">Caja {l.caja} · {l.operador} · {l.hora}</span></td>
                    <td className="gris">{l.origen}</td>
                    <td className="num">{l.paginas}{l.estado === "recibiendo" ? <span className="gris2"> / {l.esperadas}</span> : null}</td>
                    <td><span className={`chip ${estadoLote[l.estado].c}`}>{estadoLote[l.estado].t}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="panel">
          <div className="panel-cab"><h2>Por serie</h2><span className="sub">páginas y % validado</span></div>
          <ul className="lista-l">
            {r.porSerie.map((s) => (
              <li key={s.serie}>
                <div className="tx"><b>{s.serie}</b><div className="barra-prog" style={{ marginTop: 6 }}><i style={{ width: `${(s.paginas / r.porSerie[0].paginas) * 100}%` }} /></div></div>
                <span className="num" style={{ width: 70, textAlign: "right" }}>{s.paginas.toLocaleString("en-US")}</span>
                <span className={`chip ${s.validados >= 95 ? "ok" : "duda"}`}>{s.validados}%</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="panel plano">
        <div className="panel-cab"><h2>Dispositivos</h2><Link className="btn btn-sec btn-chico" href="/dispositivos/">Administrar</Link></div>
        <div className="rejilla r3">
          {dispositivos.slice(0, 6).map((d) => (
            <div key={d.id} style={{ display: "flex", gap: 12, alignItems: "center", minWidth: 0 }}>
              <span className="ic-cuadro"><Icono n={d.tipo === "pistola" ? "qr" : d.tipo} /></span>
              <div style={{ minWidth: 0 }}>
                <b style={{ display: "block", fontWeight: 500, color: "var(--blanco)", fontSize: ".88rem" }}>{d.nombre}</b>
                <span className={`estado ${d.estado}`} style={{ fontSize: ".76rem" }}><i />{d.nota}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
