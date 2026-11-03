"use client";
import { useEffect, useRef, useState } from "react";
import Logo from "@/components/Logo";
import Icono from "@/components/Icono";

// Captura con celular: app web emparejada por QR. Recorta bordes, corrige perspectiva y sube al lote.
export default function MovilDemo() {
  const [paso, setPaso] = useState<"camara" | "revisar" | "enviando" | "listo">("camara");
  const [paginas, setPaginas] = useState(3);
  const [flash, setFlash] = useState(false);
  const [real, setReal] = useState(false);
  const [error, setError] = useState("");
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [prog, setProg] = useState(0);

  const disparar = () => { setFlash(true); setTimeout(() => setFlash(false), 160); setPaginas((p) => p + 1); };
  const camaraReal = async () => {
    setError("");
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      stream.current = s; setReal(true);
      setTimeout(() => { if (video.current) { video.current.srcObject = s; video.current.play().catch(() => {}); } }, 50);
    } catch { setError("No se pudo abrir la cámara. Revisa el permiso del navegador."); }
  };
  useEffect(() => () => stream.current?.getTracks().forEach((t) => t.stop()), []);
  useEffect(() => {
    if (paso !== "enviando") return;
    setProg(0);
    const t = setInterval(() => setProg((p) => { if (p >= 100) { clearInterval(t); setPaso("listo"); return 100; } return p + 7; }), 120);
    return () => clearInterval(t);
  }, [paso]);

  return (
    <div className="movil-escena">
      <div className="telefono">
        <div className="tel-sup">
          <span className="tel-marca"><Logo /><b>Arriera</b></span>
          <span className="estado on" style={{ fontSize: ".72rem" }}><i />Emparejado</span>
        </div>
        <div className="tel-lote"><span className="gris2">Lote</span> <b className="maq lima">L-2026-000188</b> <span className="gris2">· Caja C-0047</span></div>

        {paso === "camara" && (
          <>
            <div className="visor-cam">
              {real ? <video ref={video} playsInline muted /> : (
                <div className="papel hoja-cam">
                  <div className="membrete"><b>FONDO DE AYUDA MUTUA (DEMO)</b><span>Form. B-02</span></div>
                  <h4>SOLICITUD DE SUBSIDIO</h4>
                  {Array.from({ length: 7 }).map((_, k) => <div key={k} className="fila-p"><span>Campo {k + 1}:</span><i>&nbsp;</i></div>)}
                  <div className="demo-pie">DATOS DEMO · NO VÁLIDO</div>
                </div>
              )}
              <svg className="bordes" viewBox="0 0 100 140" preserveAspectRatio="none" aria-hidden="true"><polygon points="14,16 88,12 92,128 9,124" /></svg>
              <span className="cam-aviso">Documento detectado · mantén firme</span>
              {flash && <div className="flash" />}
            </div>
            {error && <p className="gris" style={{ fontSize: ".78rem", textAlign: "center" }}>{error}</p>}
            <div className="cam-controles">
              <button className="mini" onClick={() => setPaso("revisar")} aria-label="Revisar páginas"><span className="mini-hoja" /><span className="mini-n">{paginas}</span></button>
              <button className="obturador" onClick={disparar} aria-label="Tomar foto"><span /></button>
              <button className="icono-btn" onClick={camaraReal} aria-label="Usar cámara real"><Icono n="camara" /></button>
            </div>
            <div className="tel-opc"><span className="chip ok">Recorte automático</span><span className="chip ok">Corrección de perspectiva</span><span className="chip neutro">Separador: no</span></div>
          </>
        )}

        {paso === "revisar" && (
          <div className="tel-revisar">
            <h2>{paginas} páginas<span className="maq lima">listas para enviar</span></h2>
            <div className="miniaturas">
              {Array.from({ length: paginas }).map((_, i) => (
                <div key={i} className="mini-pag"><div className="papel" style={{ padding: "12%", fontSize: 3 }}>{Array.from({ length: 8 }).map((_, k) => <div key={k} style={{ height: 2, background: "#8A8273", margin: "4px 0", width: `${60 + ((k * 17 + i * 7) % 40)}%` }} />)}</div><span className="maq">{i + 1}</span></div>
              ))}
            </div>
            <div className="aviso verde" style={{ fontSize: ".78rem" }}><Icono n="check" /><span>Todas pasaron el control de calidad del teléfono: nítidas y sin cortes.</span></div>
            <button className="btn btn-prim" onClick={() => setPaso("enviando")}><Icono n="enviar" />Enviar al lote</button>
            <button className="btn btn-sec" onClick={() => setPaso("camara")}><Icono n="camara" />Seguir escaneando</button>
          </div>
        )}

        {paso === "enviando" && (
          <div className="tel-revisar" style={{ alignContent: "center" }}>
            <h2>Enviando<span className="maq lima">verificando huella SHA-256</span></h2>
            <div className="barra-prog" style={{ height: 10 }}><i style={{ width: `${prog}%` }} /></div>
            <p className="gris num" style={{ fontSize: ".82rem" }}>{Math.min(prog, 100)}% · si se corta la señal, continúa sola al volver.</p>
          </div>
        )}

        {paso === "listo" && (
          <div className="tel-revisar" style={{ alignContent: "center", textAlign: "center", justifyItems: "center" }}>
            <span className="ic-cuadro" style={{ width: 64, height: 64, borderRadius: 18 }}><Icono n="check" /></span>
            <h2>Recibido<span className="maq lima">{paginas} páginas en L-2026-000188</span></h2>
            <p className="gris" style={{ fontSize: ".84rem" }}>La IA ya está leyendo el lote. Verás en minutos si alguna página necesita repetirse.</p>
            <button className="btn btn-prim" onClick={() => { setPaginas(0); setPaso("camara"); }}>Nuevo documento</button>
          </div>
        )}
      </div>
      <p className="movil-nota">Vista de la app de captura en el celular. En un teléfono real ocupa toda la pantalla.</p>
    </div>
  );
}
