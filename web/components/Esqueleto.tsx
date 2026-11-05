// Esqueletos de carga: la forma de lo que viene, sin ruedas que giran ni pantallas que «brincan».
import type { CSSProperties } from "react";

export function Skel({ w = "100%", h = 14, r = 8, style }: { w?: number | string; h?: number | string; r?: number; style?: CSSProperties }) {
  return <span className="skel" style={{ width: w, height: h, borderRadius: r, ...style }} aria-hidden="true" />;
}

export function SkeletonRows({ n = 5, avatar = false, etiqueta = "Cargando" }: { n?: number; avatar?: boolean; etiqueta?: string }) {
  return (
    <div className="skel-filas" role="status" aria-label={etiqueta}>
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="skel-fila">
          {avatar && <Skel w={40} h={40} r={12} />}
          <div style={{ display: "grid", gap: 7, flex: 1 }}>
            <Skel w={`${62 - (i % 3) * 12}%`} h={13} />
            <Skel w={`${38 + (i % 2) * 14}%`} h={11} />
          </div>
          <Skel w={58} h={22} r={99} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonCards({ n = 3 }: { n?: number }) {
  return (
    <div className="rejilla r3" role="status" aria-label="Cargando">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="panel" style={{ display: "grid", gap: 10 }}><Skel w="45%" h={15} /><Skel h={90} r={14} /><Skel w="70%" h={11} /></div>
      ))}
    </div>
  );
}

export function SkeletonStats({ n = 4 }: { n?: number }) {
  return (
    <div className="rejilla r4 stats" role="status" aria-label="Cargando indicadores">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="panel" style={{ display: "grid", gap: 9 }}><Skel w="55%" h={11} /><Skel w="40%" h={28} r={10} /><Skel w="65%" h={10} /></div>
      ))}
    </div>
  );
}

/** Ficha: página escaneada a la izquierda y campos a la derecha (validación, visor). */
export function SkeletonPagina({ alto = 520 }: { alto?: number }) {
  return (
    <div className="skel-pagina" role="status" aria-label="Abriendo página">
      <Skel w="38%" h={14} style={{ marginTop: "8%" }} />
      {Array.from({ length: 9 }, (_, i) => <Skel key={i} w={`${88 - (i * 13) % 34}%`} h={10} />)}
      <Skel w="30%" h={10} style={{ marginTop: 18 }} />
      <span style={{ display: "block", height: Math.max(0, alto - 340) }} />
    </div>
  );
}

export function SkeletonDetail() {
  return (
    <div className="rejilla val-grid" role="status" aria-label="Cargando">
      <div className="panel plano" style={{ padding: 10 }}><SkeletonRows n={6} /></div>
      <div className="panel" style={{ display: "grid", gap: 12 }}><Skel w="50%" h={18} /><SkeletonPagina /></div>
      <div className="panel" style={{ display: "grid", gap: 10, alignContent: "start" }}>
        {Array.from({ length: 6 }, (_, i) => <div key={i} style={{ display: "grid", gap: 7, padding: 10, border: "1px solid var(--linea)", borderRadius: 12 }}><Skel w="45%" h={11} /><Skel h={40} r={12} /></div>)}
      </div>
    </div>
  );
}
