"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { resultados } from "@/lib/demo";

const ejemplos = ["solicitudes de subsidio de 2018 sin boleta de pago", "Rosa Huamán", "préstamos de 2019 con cronograma", "4•••••18"];

type Msg = { de: "yo" | "ia"; t: string; citas?: { t: string; h: string }[] };

export default function Busqueda() {
  const [q, setQ] = useState(ejemplos[0]);
  const [filtros, setFiltros] = useState(["Tipo: solicitud de subsidio", "Año: 2018", "Falta: boleta de pago"]);
  const [msgs, setMsgs] = useState<Msg[]>([
    { de: "yo", t: "¿Qué expedientes de subsidio de 2018 no tienen boleta de pago?" },
    { de: "ia", t: "Encontré 3 expedientes de 2018 con solicitud de subsidio y sin boleta de pago. En el 2018-0412, el informe médico está en la página 6. Los otros dos son 2018-0377 y 2018-0519.", citas: [{ t: "Exp. 2018-0412 · Informe médico · pág. 6", h: "/expedientes/2018-0412/" }, { t: "Exp. 2018-0377 · Solicitud · pág. 1", h: "/expedientes/2018-0412/" }, { t: "Exp. 2018-0519 · Solicitud · pág. 1", h: "/expedientes/2018-0412/" }] },
  ]);
  const [preg, setPreg] = useState("");
  const [escribiendo, setEscribiendo] = useState(false);
  useEffect(() => { const u = new URLSearchParams(window.location.search).get("q"); if (u && u !== "asistente") setQ(u); }, []);

  const preguntar = (texto: string) => {
    if (!texto.trim()) return;
    setMsgs((m) => [...m, { de: "yo", t: texto }]); setPreg(""); setEscribiendo(true);
    setTimeout(() => {
      setEscribiendo(false);
      setMsgs((m) => [...m, { de: "ia", t: "En 2019 hay 1,104 expedientes de subsidio. 37 no tienen boleta de pago; lo conté con el índice, no lo estimé. ¿Quieres que te los liste por caja para pedirlos al área de Beneficios?", citas: [{ t: "Conteo sobre 1,104 expedientes de 2019", h: "/archivo/" }] }]);
    }, 900);
  };

  return (
    <>
      <Cab titulo="Búsqueda y asistente" maq="pregúntale al archivo como a una persona" desc="Busca por nombre, DNI, fecha, tipo o cualquier palabra del documento. El asistente responde citando la página y solo con lo que tienes permiso de ver." />
      <div className="rejilla bus-grid">
        <div style={{ display: "grid", gap: 14, alignContent: "start", minWidth: 0 }}>
          <form className="buscador" style={{ maxWidth: "none", padding: "13px 16px", fontSize: "1.02rem" }} onSubmit={(e) => e.preventDefault()}>
            <Icono n="busqueda" /><input id="q" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Consulta" />
            <button className="btn btn-prim btn-chico" type="submit">Buscar</button>
          </form>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
            <span className="gris2" style={{ fontSize: ".78rem" }}>La IA entendió:</span>
            {filtros.map((f) => <span key={f} className="chip lleno ok" style={{ cursor: "pointer" }} onClick={() => setFiltros((x) => x.filter((y) => y !== f))}>{f} ✕</span>)}
            <button className="chip neutro" style={{ background: "transparent", cursor: "pointer" }}>+ filtro</button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {ejemplos.slice(1).map((e) => <button key={e} className="btn btn-sec btn-chico" onClick={() => setQ(e)}>{e}</button>)}
          </div>
          <div className="rejilla" style={{ gridTemplateColumns: "minmax(0,180px) minmax(0,1fr)", gap: 14 }}>
            <div className="panel plano" style={{ padding: 14, display: "grid", gap: 12, alignContent: "start", fontSize: ".82rem" }}>
              {[["Año", [["2018", 3], ["2019", 0]]], ["Serie", [["Beneficios", 3]]], ["Sensibilidad", [["N2", 3], ["N3", 2]]]].map(([t, ops]) => (
                <div key={t as string} style={{ display: "grid", gap: 6 }}><b style={{ color: "var(--blanco)", fontWeight: 500 }}>{t as string}</b>
                  {(ops as [string, number][]).map(([o, n]) => <label key={o} style={{ display: "flex", justifyContent: "space-between", gap: 6 }}><span><input type="checkbox" defaultChecked={n > 0} style={{ accentColor: "#DCE57A" }} /> {o}</span><span className="gris2">{n}</span></label>)}
                </div>
              ))}
            </div>
            <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--linea)", display: "flex", justifyContent: "space-between" }}><b style={{ color: "var(--blanco)", fontWeight: 500 }}>3 expedientes</b><span className="gris2" style={{ fontSize: ".78rem" }}>0.42 s · solo lo que puedes ver</span></div>
              {resultados.map((r) => (
                <Link href="/expedientes/2018-0412/" key={r.exp} style={{ display: "grid", gap: 8, padding: "14px 16px", borderBottom: "1px solid var(--linea)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Subsidio <span className="maq lima">{r.exp}</span> · {r.titular}</b><span className="gris2" style={{ fontSize: ".78rem" }}>Caja <span className="maq">{r.caja}</span></span></div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{r.docs.map(([c, t]) => <span key={t} className={`chip ${c}`}>{t}</span>)}</div>
                  <span className="gris" style={{ fontSize: ".82rem" }}>Leído por IA: {r.campo[0]} <b className="maq" style={{ color: "var(--blanco)", fontWeight: 400 }}>{r.campo[1]}</b> <span className={`chip lleno ${r.campo[2].includes("validar") ? "duda" : "ok"}`}>{r.campo[2]}</span></span>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="panel luz chat">
          <div className="panel-cab" style={{ margin: 0 }}><h2>Asistente</h2><span className="chip neutro">Cita siempre la página</span></div>
          <div className="chat-msgs">
            {msgs.map((m, i) => (
              <div key={i} className={`msg ${m.de}`}>
                <p>{m.t}</p>
                {m.citas ? <div className="citas">{m.citas.map((c) => <Link key={c.t} href={c.h} className="cita"><Icono n="doc" />{c.t}</Link>)}</div> : null}
              </div>
            ))}
            {escribiendo ? <div className="msg ia"><p className="maq gris">consultando el índice…</p></div> : null}
          </div>
          <form className="chat-in" onSubmit={(e) => { e.preventDefault(); preguntar(preg); }}>
            <input id="preg" className="inp" value={preg} onChange={(e) => setPreg(e.target.value)} placeholder="¿Y cuántos de 2019?" aria-label="Pregunta al asistente" />
            <button className="btn btn-lima" type="submit" aria-label="Enviar"><Icono n="enviar" /></button>
          </form>
          <p className="gris2" style={{ fontSize: ".72rem" }}>Muestra el DNI enmascarado y no da consejo médico ni legal. Cada pregunta queda en la auditoría.</p>
        </div>
      </div>
    </>
  );
}
