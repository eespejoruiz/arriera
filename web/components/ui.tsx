import Icono from "./Icono";

export function Cab({ titulo, maq, desc, migas, children }: { titulo: string; maq?: string; desc?: string; migas?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="cab">
      <div>
        {migas ? <div className="migas">{migas}</div> : null}
        <h1>{titulo}{maq ? <span className="maq">{maq}</span> : null}</h1>
        {desc ? <p>{desc}</p> : null}
      </div>
      {children ? <div className="acciones">{children}</div> : null}
    </div>
  );
}

export function LeidoIA() {
  return <span className="ia" title="Dato leído por la IA"><Icono n="ia" />leído por IA</span>;
}

export function Confianza({ c }: { c: number }) {
  const k = c >= 95 ? "ok" : c >= 85 ? "duda" : "falta";
  return <span className={`chip lleno ${k}`}>{c}%{c < 90 ? " · validar" : ""}</span>;
}

// Código QR ilustrativo (patrón determinista a partir del texto). En el sistema real lo genera `segno`.
export function QR({ texto, tam = 120, color = "#14160F", fondo = "#F4F5EE" }: { texto: string; tam?: number; color?: string; fondo?: string }) {
  const n = 25;
  let h = 2166136261;
  for (const ch of texto) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  const celdas: string[] = [];
  const finder = (x: number, y: number) => {
    const dx = x < 7 ? x : x >= n - 7 ? x - (n - 7) : -1;
    const dy = y < 7 ? y : y >= n - 7 ? y - (n - 7) : -1;
    if (dx < 0 || dy < 0 || (x >= n - 7 && y >= n - 7)) return null;
    const ring = Math.min(dx, dy, 6 - dx, 6 - dy);
    return ring === 0 || ring >= 2;
  };
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const f = finder(x, y);
    let on: boolean;
    if (f !== null) on = f;
    else if ((x === 7 || y === 7 || x === n - 8 || y === n - 8) && (x < 8 || y < 8 || x > n - 9 || y > n - 9)) on = false;
    else { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; on = (h >>> 0) % 100 < 47; }
    if (on) celdas.push(`M${x} ${y}h1v1h-1z`);
  }
  return (
    <svg viewBox={`-2 -2 ${n + 4} ${n + 4}`} width={tam} height={tam} role="img" aria-label={`Código QR ${texto}`} shapeRendering="crispEdges">
      <rect x="-2" y="-2" width={n + 4} height={n + 4} fill={fondo} />
      <path d={celdas.join("")} fill={color} />
    </svg>
  );
}

export function Barras({ datos, etiquetas, alto = 150 }: { datos: number[]; etiquetas: string[]; alto?: number }) {
  const max = Math.max(...datos) * 1.1, W = 560, H = alto, pad = 26, bw = (W - pad) / datos.length;
  return (
    <svg viewBox={`0 0 ${W} ${H + 22}`} style={{ width: "100%", height: "auto", display: "block" }} role="img" aria-label="Páginas capturadas por día">
      {[0.25, 0.5, 0.75, 1].map((t) => (
        <g key={t}><line x1={pad} x2={W} y1={H - H * t} y2={H - H * t} stroke="rgba(255,255,255,.06)" />
          <text x={0} y={H - H * t + 4} fill="#7E8372" fontSize="10">{Math.round((max * t) / 1000)}k</text></g>
      ))}
      {datos.map((d, i) => {
        const h = (d / max) * H, ult = i === datos.length - 1;
        return (
          <g key={i}>
            <rect x={pad + i * bw + bw * 0.22} y={H - h} width={bw * 0.56} height={h} rx={4} fill={ult ? "#DCE57A" : "rgba(169,182,64,.55)"} />
            <text x={pad + i * bw + bw / 2} y={H + 16} fill="#7E8372" fontSize="10" textAnchor="middle">{etiquetas[i]}</text>
            {ult ? <text x={pad + i * bw + bw / 2} y={H - h - 7} fill="#DCE57A" fontSize="11" textAnchor="middle">{d.toLocaleString("en-US")}</text> : null}
          </g>
        );
      })}
    </svg>
  );
}

export function Pagina({ variante = "solicitud", marcar }: { variante?: "solicitud" | "informe" | "boleta"; marcar?: string }) {
  const m = (k: string, t: string) => (marcar === k ? <mark>{t}</mark> : marcar === "todo" ? <mark className="ok">{t}</mark> : <>{t}</>);
  if (variante === "informe") return (
    <div className="papel">
      <div className="membrete"><b>CLÍNICA SAN GABRIEL (DEMO)</b><span>Historia N.º 55120</span></div>
      <h4>INFORME MÉDICO</h4>
      <div className="fila-p"><span>Paciente:</span><i>{m("nombre", "Rosa Huamán Quispe")}</i></div>
      <div className="fila-p"><span>DNI:</span><i>{m("dni", "4•••••18")}</i><span>Fecha:</span><i>{m("fecha", "02/03/2018")}</i></div>
      <div className="fila-p"><span>Diagnóstico:</span><i>{m("diag", "Lumbalgia aguda — reposo")}</i></div>
      <div className="fila-p"><span>CIE-10:</span><i>{m("cie", "M54.5")}</i><span>Días de descanso:</span><i>{m("dias", "15")}</i></div>
      <p style={{ marginTop: 14 }}>Se indica descanso médico y control en 15 días. Paciente evoluciona favorablemente con tratamiento analgésico.</p>
      <div className="fila-p" style={{ marginTop: 26 }}><span>Médico tratante:</span><i>Dr. A. Salinas · CMP 0••••2</i></div>
      <div className="sello">CLÍNICA<br />SAN GABRIEL<br />DEMO</div>
      <div className="demo-pie">DATOS DEMO · NO VÁLIDO</div>
    </div>
  );
  return (
    <div className="papel">
      <div className="membrete"><b>FONDO DE AYUDA MUTUA (DEMO)</b><span>Form. B-02</span></div>
      <h4>SOLICITUD DE SUBSIDIO</h4>
      <div className="fila-p"><span>Apellidos y nombres:</span><i>{m("nombre", "Rosa Huamán Quispe")}</i></div>
      <div className="fila-p"><span>DNI:</span><i>{m("dni", "4•••••18")}</i><span>Código:</span><i>{m("codigo", "AS-02231")}</i></div>
      <div className="fila-p"><span>Fecha de solicitud:</span><i>{m("fecha", "14/03/2018")}</i></div>
      <div className="fila-p"><span>Tipo de subsidio:</span><i>{m("tipo", "Enfermedad")}</i></div>
      <div className="fila-p"><span>Monto solicitado (S/):</span><i>{m("monto", "1,250.00")}</i></div>
      <p style={{ marginTop: 14 }}>Solicito se me otorgue el subsidio por enfermedad conforme al reglamento vigente, para lo cual adjunto el informe médico y la documentación requerida.</p>
      <div className="fila-p" style={{ marginTop: 34 }}><span>Firma:</span><i style={{ fontSize: 18 }}>R. Huamán</i></div>
      <div className="sello">FONDO<br />RECIBIDO<br />15 MAR 2018</div>
      <div className="demo-pie">DATOS DEMO · NO VÁLIDO</div>
    </div>
  );
}
