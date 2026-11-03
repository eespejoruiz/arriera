"use client";
import { useEffect, useState } from "react";
import { Cab, Pagina, Confianza, LeidoIA } from "@/components/ui";
import Icono from "@/components/Icono";
import { tareas, campos } from "@/lib/demo";

const claves: Record<string, string> = { "Nombre del titular": "nombre", DNI: "dni", "Código de asociada": "codigo", "Fecha de solicitud": "fecha", "Tipo de subsidio": "tipo", "Monto solicitado": "monto" };

export default function ValidacionDemo() {
  const [sel, setSel] = useState(5);
  const [vals, setVals] = useState(campos.map((c) => c.v));
  const [hechos, setHechos] = useState<boolean[]>(campos.map((c) => c.ok));
  const [tarea, setTarea] = useState("v-1");
  const aceptar = (i: number) => { setHechos((h) => h.map((x, k) => (k === i ? true : x))); const sig = hechos.findIndex((x, k) => !x && k !== i); if (sig >= 0) setSel(sig); };
  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT" && e.key !== "Enter") return;
      if (e.key === "Enter") { e.preventDefault(); aceptar(sel); }
      if (e.key === "Tab" && !e.shiftKey && (e.target as HTMLElement)?.tagName !== "INPUT") { e.preventDefault(); setSel((s) => (s + 1) % campos.length); }
    };
    window.addEventListener("keydown", f); return () => window.removeEventListener("keydown", f);
  });
  const pendientes = hechos.filter((h) => !h).length;
  return (
    <>
      <Cab titulo="Validación" maq="solo lo que la IA no tiene claro" desc="La página a la izquierda con el dato resaltado donde se leyó; los campos a la derecha con su confianza.">
        <div className="tabs"><button className="on">Campos dudosos · 128</button><button>Separación · 31</button><button>Duplicados · 22</button><button>Asignación · 33</button></div>
      </Cab>
      <div className="rejilla val-grid">
        <div className="panel plano" style={{ padding: 10 }}>
          <span className="nav-t" style={{ display: "block" }}>Cola · prioridad</span>
          <ul className="lista-l">
            {tareas.map((t) => (
              <li key={t.id} onClick={() => setTarea(t.id)} style={{ cursor: "pointer", padding: "10px 8px", borderRadius: 10, background: tarea === t.id ? "rgba(220,229,122,.08)" : undefined }}>
                <div className="tx"><b>{t.doc}</b><span>{t.tipo} · {t.detalle}</span></div>
                <span className={`chip ${t.prioridad === "Alta" ? "duda" : "neutro"}`}>{t.prioridad}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel" style={{ display: "grid", gap: 12, alignContent: "start" }}>
          <div className="panel-cab" style={{ margin: 0 }}>
            <div><h2>Solicitud de subsidio</h2><span className="sub">Exp. <span className="maq lima">2018-0412</span> · lote L-2026-000183 · págs. 1–2</span></div>
            <div className="acciones"><button className="btn btn-sec btn-chico"><Icono n="cortar" />Separar</button><button className="btn btn-sec btn-chico"><Icono n="unir" />Unir</button></div>
          </div>
          <div style={{ maxWidth: 520, width: "100%", justifySelf: "center" }}><Pagina variante="solicitud" marcar={claves[campos[sel].k]} /></div>
        </div>

        <div className="panel" style={{ display: "grid", gap: 10, alignContent: "start" }}>
          <div className="panel-cab" style={{ margin: 0 }}><h2>Datos extraídos</h2><span className={`chip ${pendientes ? "duda" : "ok"}`}>{pendientes ? `${pendientes} por validar` : "Todo validado"}</span></div>
          <div className="campo-f"><span className="et">Tipo documental</span><div style={{ display: "flex", gap: 8, alignItems: "center" }}><b style={{ color: "var(--blanco)", fontWeight: 500 }}>Solicitud de subsidio</b><Confianza c={99} /></div></div>
          {campos.map((c, i) => (
            <div key={c.k} onClick={() => setSel(i)} className="campo-f" style={{ padding: 10, borderRadius: 12, border: `1px solid ${sel === i ? "rgba(220,229,122,.5)" : "var(--linea)"}`, background: sel === i ? "rgba(220,229,122,.05)" : "transparent", cursor: "pointer" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><label htmlFor={`c${i}`}>{c.k}</label>{hechos[i] && !c.ok ? <span className="chip lleno ok">Validado</span> : <Confianza c={c.c} />}</div>
              <input id={`c${i}`} className="inp maq" value={vals[i]} onChange={(e) => setVals((v) => v.map((x, k) => (k === i ? e.target.value : x)))} onFocus={() => setSel(i)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); aceptar(i); } }} />
              <div style={{ display: "flex", justifyContent: "space-between" }}><LeidoIA /><span className="gris2" style={{ fontSize: ".72rem" }}>pág. 1</span></div>
            </div>
          ))}
          <div style={{ display: "flex", gap: 8 }}><button className="btn btn-prim" style={{ flex: 1 }} onClick={() => aceptar(sel)}><Icono n="check" />Aceptar campo</button><button className="btn btn-sec">Siguiente documento</button></div>
          <p className="gris2" style={{ fontSize: ".74rem" }}><span className="maq">Enter</span> acepta · <span className="maq">Tab</span> pasa al siguiente · <span className="maq">Ctrl+D</span> descarta. Cada corrección queda en la auditoría.</p>
        </div>
      </div>
    </>
  );
}
