"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Logo from "@/components/Logo";
import Icono from "@/components/Icono";
import { apiEstacion, canjearCodigo, ErrorApi, type LoteEstacion } from "@/lib/api";

// App de captura con celular: se empareja con un QR, toma fotos, calcula la huella SHA-256 en el teléfono
// y las envía en cola con reintentos. Las fotos no se guardan en la galería del teléfono.

const LLAVE = "arriera_llave_estacion";
type Envio = { id: number; blob: Blob; url: string; estado: "en_cola" | "enviando" | "enviada" | "error"; intento: number; pagina?: number; error?: string };

const guardar = (k: string, v: string | null) => { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch { /* modo privado */ } };
const leer = (k: string) => { try { return localStorage.getItem(k); } catch { return null; } };

async function sha256(blob: Blob): Promise<string> {
  const h = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
  return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

const textoEstado: Record<string, [string, string]> = {
  pendiente: ["Revisando", "neutro"], ok: ["Bien", "ok"], corregida: ["Enderezada", "ok"],
  reescanear: ["Repetir", "falta"], en_blanco: ["En blanco", "neutro"],
};

export default function MovilReal() {
  const [llave, setLlave] = useState<string | null>(null);
  const [info, setInfo] = useState<LoteEstacion | null>(null);
  const [error, setError] = useState("");
  const [camara, setCamara] = useState<"apagada" | "activa" | "sin_permiso">("apagada");
  const [envios, setEnvios] = useState<Envio[]>([]);
  const [flash, setFlash] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const archivo = useRef<HTMLInputElement>(null);
  const contador = useRef(0);
  const ocupado = useRef(false);

  // 1) Emparejar con el código del QR o recuperar la llave guardada.
  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("t");
    (async () => {
      try {
        if (t) {
          const modelo = (navigator.userAgent.match(/\(([^)]+)\)/)?.[1] ?? "Celular").split(";").slice(0, 2).join(" ").slice(0, 90);
          const r = await canjearCodigo(t, modelo);
          guardar(LLAVE, r.llave); setLlave(r.llave); setInfo(r);
          window.history.replaceState(null, "", "/m/");
        } else {
          const k = leer(LLAVE);
          if (!k) { setError("Escanea el código QR que aparece en Captura, en la computadora."); return; }
          setLlave(k); setInfo(await apiEstacion<LoteEstacion>("/estacion/lote", k));
        }
      } catch (e) {
        if (e instanceof ErrorApi && (e.estado === 401 || e.estado === 410)) guardar(LLAVE, null);
        setError(e instanceof ErrorApi ? e.message : "Sin conexión. Revisa tus datos o el wifi.");
      }
    })();
  }, []);

  // 2) Refrescar el estado del lote (resultado del control de calidad).
  const refrescar = useCallback(async () => {
    if (!llave) return;
    try { setInfo(await apiEstacion<LoteEstacion>("/estacion/lote", llave)); } catch { /* reintenta luego */ }
  }, [llave]);
  useEffect(() => { const i = setInterval(refrescar, 4000); return () => clearInterval(i); }, [refrescar]);

  // 3) Cola de envío: una foto a la vez, con reintentos.
  useEffect(() => {
    if (!llave || !info || ocupado.current) return;
    const sig = envios.find((e) => e.estado === "en_cola");
    if (!sig) return;
    ocupado.current = true;
    setEnvios((x) => x.map((e) => (e.id === sig.id ? { ...e, estado: "enviando" } : e)));
    (async () => {
      try {
        const fd = new FormData();
        fd.append("archivo", sig.blob, `pagina-${sig.id}.jpg`);
        fd.append("sha256", await sha256(sig.blob));
        const r = await apiEstacion<{ pagina: number }>(`/estacion/lotes/${info.lote}/paginas`, llave, { method: "POST", body: fd });
        setEnvios((x) => x.map((e) => (e.id === sig.id ? { ...e, estado: "enviada", pagina: r.pagina } : e)));
        refrescar();
      } catch (e) {
        const definitivo = e instanceof ErrorApi && [401, 403, 409, 413, 415].includes(e.estado);
        const intento = sig.intento + 1;
        setEnvios((x) => x.map((v) => (v.id === sig.id ? { ...v, intento, estado: definitivo || intento >= 5 ? "error" : "en_cola", error: e instanceof Error ? e.message : "" } : v)));
        if (!definitivo) await new Promise((r) => setTimeout(r, 1500 * intento));
      } finally { ocupado.current = false; setEnvios((x) => [...x]); }
    })();
  }, [envios, llave, info, refrescar]);

  const encolar = (blob: Blob) => {
    contador.current += 1;
    setEnvios((x) => [...x, { id: contador.current, blob, url: URL.createObjectURL(blob), estado: "en_cola", intento: 0 }]);
  };

  const encenderCamara = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 2560 }, height: { ideal: 1920 } }, audio: false });
      stream.current = s; setCamara("activa");
      setTimeout(() => { if (video.current) { video.current.srcObject = s; video.current.play().catch(() => {}); } }, 30);
    } catch { setCamara("sin_permiso"); }
  };
  useEffect(() => () => stream.current?.getTracks().forEach((t) => t.stop()), []);

  const disparar = () => {
    const v = video.current;
    if (!v || !v.videoWidth) return;
    const c = document.createElement("canvas");
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d")?.drawImage(v, 0, 0);
    setFlash(true); setTimeout(() => setFlash(false), 140);
    c.toBlob((b) => b && encolar(b), "image/jpeg", 0.9);
  };

  const estadoPagina = (n?: number) => info?.paginas.find((p) => p.indice === n);
  const enviadas = envios.filter((e) => e.estado === "enviada").length;
  const enCola = envios.filter((e) => e.estado === "en_cola" || e.estado === "enviando").length;
  const repetir = info?.paginas.filter((p) => p.estado === "reescanear") ?? [];

  return (
    <div className="movil-escena">
      <div className="telefono">
        <div className="tel-sup">
          <span className="tel-marca"><Logo /><b>Arriera</b></span>
          <span className={`estado ${info ? "on" : "off"}`} style={{ fontSize: ".72rem" }}><i />{info ? "Emparejado" : "Sin emparejar"}</span>
        </div>
        {info && <div className="tel-lote"><span className="gris2">Lote</span> <b className="maq lima">{info.lote}</b> <span className="gris2">· Caja {info.caja}</span></div>}

        {!info ? (
          <div className="tel-revisar" style={{ alignContent: "center", textAlign: "center", justifyItems: "center" }}>
            <span className="ic-cuadro" style={{ width: 60, height: 60, borderRadius: 18 }}><Icono n="qr" /></span>
            <h2>Empareja este celular<span className="maq lima">con un código QR</span></h2>
            <p className="gris" style={{ fontSize: ".86rem" }}>{error || "Conectando…"}</p>
          </div>
        ) : (
          <>
            <div className="visor-cam">
              {camara === "activa" ? <video ref={video} playsInline muted /> : (
                <div style={{ display: "grid", gap: 12, justifyItems: "center", textAlign: "center", padding: 20 }}>
                  <p className="gris" style={{ fontSize: ".86rem" }}>{camara === "sin_permiso" ? "El navegador no dio permiso para la cámara. Usa «Tomar con la cámara del teléfono»." : "Pon la hoja sobre una superficie oscura, con buena luz y sin sombras."}</p>
                  {camara !== "sin_permiso" && <button className="btn btn-prim" onClick={encenderCamara}><Icono n="camara" />Abrir cámara</button>}
                </div>
              )}
              {camara === "activa" && <svg className="bordes" viewBox="0 0 100 140" preserveAspectRatio="none" aria-hidden="true"><polygon points="8,8 92,8 92,132 8,132" /></svg>}
              {camara === "activa" && <span className="cam-aviso">Encuadra la hoja dentro del marco</span>}
              {flash && <div className="flash" />}
            </div>
            <div className="cam-controles">
              <span className="mini" aria-label={`${envios.length} fotos`}>{envios.length > 0 && <><span className="mini-hoja" style={{ backgroundImage: `url(${envios[envios.length - 1].url})`, backgroundSize: "cover" }} /><span className="mini-n">{envios.length}</span></>}</span>
              <button className="obturador" onClick={disparar} disabled={camara !== "activa"} aria-label="Tomar foto"><span /></button>
              <button className="icono-btn" onClick={() => archivo.current?.click()} aria-label="Tomar con la cámara del teléfono"><Icono n="descargar" /></button>
              <input ref={archivo} type="file" accept="image/*" capture="environment" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) encolar(f); e.target.value = ""; }} />
            </div>
            <div className="tel-opc">
              <span className="chip ok">{enviadas} enviadas</span>
              {enCola > 0 && <span className="chip info">{enCola} en cola</span>}
              {repetir.length > 0 && <span className="chip falta">{repetir.length} por repetir</span>}
            </div>
            {repetir.length > 0 && <div className="aviso" style={{ fontSize: ".78rem" }}><Icono n="alerta" /><span>Repite {repetir.map((p) => `la página ${p.indice} (${(p.motivo ?? "").toLowerCase()})`).join(", ")}.</span></div>}
            {envios.length > 0 && (
              <div className="miniaturas" style={{ maxHeight: 220 }}>
                {[...envios].reverse().map((e) => {
                  const q = estadoPagina(e.pagina);
                  const [t, c] = e.estado === "enviada" ? (textoEstado[q?.estado ?? "pendiente"] ?? ["Revisando", "neutro"]) : e.estado === "error" ? ["No se envió", "falta"] : ["Enviando", "info"];
                  return (
                    <div key={e.id} className="mini-pag">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={e.url} alt={`Foto ${e.id}`} style={{ width: "100%", aspectRatio: "3/4", objectFit: "cover", borderRadius: 6 }} />
                      <span className={`chip ${c}`} title={q?.motivo ?? e.error ?? ""}>{e.pagina ? `${e.pagina} · ` : ""}{t}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
      <p className="movil-nota">App de captura de Arriera. Las fotos se envían cifradas y no quedan en la galería del teléfono.</p>
    </div>
  );
}
