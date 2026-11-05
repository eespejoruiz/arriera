"use client";
import { useCallback, useEffect, useState } from "react";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { accesosSensibles, urlAccesosCsv, verificarCadena, ErrorApi, type AccesoSensible, type VerifCadena } from "@/lib/api";
import { SkeletonRows } from "./Esqueleto";

// Auditoría y Ley 29733: quién vio datos sensibles (N3), cuándo y desde dónde; y la verificación de la cadena.
export default function CumplimientoReal() {
  const [dias, setDias] = useState(30);
  const [datos, setDatos] = useState<{ total: number; por_usuario: { usuario: string; accesos: number }[]; accesos: AccesoSensible[] } | null>(null);
  const [cadena, setCadena] = useState<VerifCadena | null>(null);
  const [error, setError] = useState("");
  const [verificando, setVerificando] = useState(false);
  const cargar = useCallback(() => {
    accesosSensibles(dias).then((d) => { setDatos(d); setError(""); })
      .catch((e) => setError(e instanceof ErrorApi && e.estado === 403 ? "Este panel es para el Oficial de Datos Personales (auditoría) y administración." : "No se pudo cargar el panel."));
  }, [dias]);
  useEffect(() => { cargar(); }, [cargar]);
  const verificar = async () => { setVerificando(true); try { setCadena(await verificarCadena()); } catch { setError("No se pudo verificar la cadena."); } finally { setVerificando(false); } };
  return (
    <>
      <Cab titulo="Auditoría" maq="quién vio datos sensibles" desc="Para el Oficial de Datos Personales (Ley 29733): cada vista de un documento o página de nivel N3 queda registrada con usuario, fecha e IP en una cadena que nadie puede alterar.">
        {datos && <a className="btn btn-sec" href={urlAccesosCsv(dias)}><Icono n="descargar" />Exportar CSV</a>}
        <button className="btn btn-prim" onClick={verificar} disabled={verificando}><Icono n="auditoria" />{verificando ? "Verificando…" : "Verificar la cadena"}</button>
      </Cab>
      {error && <div className="aviso" style={{ marginBottom: 12 }}><Icono n="alerta" /><span>{error}</span></div>}
      {cadena && (
        <div className={`aviso`} style={{ marginBottom: 12 }}><Icono n={cadena.integra ? "check" : "alerta"} /><span>{cadena.integra ? <>Cadena íntegra: {cadena.eventos.toLocaleString("es-PE")} eventos verificados. Última huella <span className="maq">{cadena.ultimo_hash?.slice(0, 16)}…</span></> : <>La cadena está rota en el evento {cadena.primer_error_id}: {cadena.motivo}</>}</span></div>
      )}
      {!datos && !error && <div className="rejilla" style={{ gridTemplateColumns: "minmax(0,280px) minmax(0,1fr)", gap: 14 }}><div className="panel plano"><SkeletonRows n={3} /></div><div className="panel"><SkeletonRows n={6} /></div></div>}
      {datos && (
        <div className="rejilla" style={{ gridTemplateColumns: "minmax(0,280px) minmax(0,1fr)", gap: 14 }}>
          <div className="panel plano" style={{ display: "grid", gap: 12, alignContent: "start" }}>
            <div className="stat"><span className="l">Accesos a datos N3</span><span className="v">{datos.total.toLocaleString("es-PE")}</span><span className="d">últimos {dias} días</span></div>
            <div className="seg" role="group" aria-label="Periodo">{[7, 30, 90].map((d) => <label key={d}><input type="radio" name="dias" checked={dias === d} onChange={() => setDias(d)} /><span>{d} días</span></label>)}</div>
            <div style={{ display: "grid", gap: 6, fontSize: ".84rem" }}>
              <b style={{ color: "var(--blanco)", fontWeight: 500 }}>Por usuario</b>
              {datos.por_usuario.length === 0 && <span className="gris2">Nadie vio datos sensibles en el periodo.</span>}
              {datos.por_usuario.map((u) => <div key={u.usuario} style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><span>{u.usuario}</span><span className="maq">{u.accesos}</span></div>)}
            </div>
          </div>
          <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
            <div className="tabla-env">
              <table className="tabla">
                <thead><tr><th>Fecha</th><th>Quién</th><th>Acción</th><th>Documento</th><th>Lote</th><th>IP</th></tr></thead>
                <tbody>
                  {datos.accesos.map((a, i) => (
                    <tr key={i}><td className="maq">{new Date(a.fecha).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" })}</td><td>{a.usuario}</td><td>{a.accion}</td><td>{a.documento}</td><td className="maq">{a.lote}</td><td className="maq">{a.ip}</td></tr>
                  ))}
                  {datos.accesos.length === 0 && <tr><td colSpan={6} className="gris2">Sin accesos en el periodo.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
