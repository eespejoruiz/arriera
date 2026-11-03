"use client";
import { useCallback, useEffect, useState } from "react";
import Icono from "@/components/Icono";
import { estadoMicroformas, registrarPaso, urlActa, ErrorApi, type EstadoMf } from "@/lib/api";

// Pasos de la NTP 392.030-2 sobre el lote: quién hizo cada uno, con qué rol, y las actas con su huella.
export default function PanelMicroformas({ code }: { code: string }) {
  const [e, setE] = useState<EstadoMf | null>(null);
  const [notas, setNotas] = useState("");
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const cargar = useCallback(() => estadoMicroformas(code).then(setE).catch(() => {}), [code]);
  useEffect(() => { cargar(); const i = setInterval(cargar, 8000); return () => clearInterval(i); }, [cargar]);
  if (!e) return null;
  const sig = e.pasos.find((p) => p.paso === e.siguiente);
  const registrar = async () => {
    if (!sig) return;
    setOcupado(true); setError("");
    try { setE(await registrarPaso(code, sig.paso, notas)); setNotas(""); }
    catch (x) { setError(x instanceof ErrorApi ? x.message : "No se pudo registrar."); }
    finally { setOcupado(false); }
  };
  return (
    <div className="panel plano" style={{ padding: 14, marginBottom: 12, display: "grid", gap: 10 }}>
      <div className="panel-cab" style={{ margin: 0 }}><h3 style={{ fontSize: ".95rem" }}>Microformas · NTP 392.030-2</h3>{e.paginas_bajo_300dpi ? <span className="chip falta">{e.paginas_bajo_300dpi} bajo 300 dpi</span> : <span className="chip ok">300 dpi</span>}</div>
      <ol className="pasos-mf">
        {e.pasos.map((p) => (
          <li key={p.paso} className={p.hecho ? "hecho" : p.paso === e.siguiente ? "actual" : ""}>
            <span className="punto-mf">{p.hecho ? <Icono n="check" /> : null}</span>
            <span><b>{p.nombre}</b>{p.hecho ? <span className="gris2"> · {p.por} ({p.rol})</span> : p.paso === e.siguiente ? <span className="gris2"> · lo registra: {p.roles.join(", ")}</span> : null}</span>
          </li>
        ))}
      </ol>
      {sig && (
        <div style={{ display: "grid", gap: 6 }}>
          <input className="inp" placeholder="Observaciones (opcional)" value={notas} onChange={(x) => setNotas(x.target.value)} maxLength={500} />
          <button className="btn btn-prim btn-chico" onClick={registrar} disabled={ocupado}><Icono n="check" />Registrar «{sig.nombre}»</button>
        </div>
      )}
      {error && <p className="error-form" style={{ margin: 0 }}>{error}</p>}
      {e.hash_manifiesto && <p style={{ fontSize: ".74rem", margin: 0 }} className="gris2">Huella del manifiesto: <span className="maq" style={{ overflowWrap: "anywhere" }}>{e.hash_manifiesto}</span></p>}
      {e.actas.length > 0 && <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{e.actas.map((a) => <a key={a.id} className="btn btn-sec btn-chico" href={urlActa(a.id)} target="_blank" rel="noopener"><Icono n="doc" />Acta {a.numero}</a>)}</div>}
    </div>
  );
}
