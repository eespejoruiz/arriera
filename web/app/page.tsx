"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Logo from "@/components/Logo";
import Icono from "@/components/Icono";
import { configurar2fa, ingresar, modoDemo, verificar2fa, ErrorApi } from "@/lib/api";

type Paso = "clave" | "verificar" | "configurar";

export default function Ingreso() {
  const router = useRouter();
  const [paso, setPaso] = useState<Paso>("clave");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [qr, setQr] = useState<{ img: string; secreto: string } | null>(null);
  const [digitos, setDigitos] = useState<string[]>(modoDemo ? ["4", "8", "1", "9", "0", "3"] : ["", "", "", "", "", ""]);
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  const fallo = (e: unknown) => setError(e instanceof ErrorApi ? e.message : "No hay conexión con el servidor. Revisa tu red e intenta de nuevo.");

  const enviarClave = async (ev: React.FormEvent<HTMLFormElement>) => {
    ev.preventDefault(); setError("");
    if (modoDemo) { setPaso("verificar"); return; }
    const f = new FormData(ev.currentTarget);
    setCargando(true);
    try {
      const r = await ingresar(String(f.get("correo")), String(f.get("clave")));
      if (r.paso === "listo") return router.push("/inicio/");
      if (r.paso === "configurar_2fa") {
        const c = await configurar2fa();
        setQr({ img: `data:image/svg+xml;base64,${btoa(c.qr_svg)}`, secreto: c.secreto });
        setPaso("configurar");
      } else setPaso("verificar");
      setTimeout(() => refs.current[0]?.focus(), 50);
    } catch (e) { fallo(e); } finally { setCargando(false); }
  };

  const enviarCodigo = async (ev: React.FormEvent) => {
    ev.preventDefault(); setError("");
    if (modoDemo) return router.push("/inicio/");
    setCargando(true);
    try { await verificar2fa(digitos.join("")); router.push("/inicio/"); }
    catch (e) { fallo(e); setDigitos(["", "", "", "", "", ""]); refs.current[0]?.focus(); }
    finally { setCargando(false); }
  };

  const escribir = (i: number, v: string) => {
    const solo = v.replace(/\D/g, "");
    if (solo.length > 1) { const d = solo.slice(0, 6).split(""); setDigitos([...d, ...Array(6 - d.length).fill("")]); refs.current[Math.min(d.length, 5)]?.focus(); return; }
    setDigitos((x) => x.map((y, k) => (k === i ? solo : y)));
    if (solo && i < 5) refs.current[i + 1]?.focus();
  };

  const codigo = (
    <div className="codigo-2fa">
      {digitos.map((d, i) => (
        <input key={i} id={`d${i}`} ref={(el) => { refs.current[i] = el; }} className="inp maq" value={d} inputMode="numeric" autoComplete={i === 0 ? "one-time-code" : "off"}
          aria-label={`Dígito ${i + 1}`} onChange={(e) => escribir(i, e.target.value)}
          onKeyDown={(e) => { if (e.key === "Backspace" && !d && i > 0) refs.current[i - 1]?.focus(); }} />
      ))}
    </div>
  );

  return (
    <div className="ingreso">
      <div className="ingreso-foto" aria-hidden="true" />
      <div className="ingreso-caja">
        <div className="ingreso-marca"><Logo /><b>Arriera</b></div>
        <span className="pill"><span className="p" />{modoDemo ? "FAMENSSALUD · demostración" : "FAMENSSALUD · archivo digital"}</span>
        {paso === "clave" && (
          <form className="ingreso-form" onSubmit={enviarClave}>
            <h1>Ingresa a tu archivo<span className="maq lima">con tu cuenta</span></h1>
            <div className="campo-f"><label htmlFor="correo">Correo</label><input id="correo" name="correo" className="inp" type="email" required defaultValue={modoDemo ? "ana.rojas@famenssalud.demo" : ""} autoComplete="username" /></div>
            <div className="campo-f"><label htmlFor="clave">Contraseña</label><input id="clave" name="clave" className="inp" type="password" required defaultValue={modoDemo ? "demostracion" : ""} autoComplete="current-password" /></div>
            {error && <p className="error-form" role="alert">{error}</p>}
            <button className="btn btn-prim" type="submit" disabled={cargando}>{cargando ? "Verificando…" : "Continuar"}</button>
          </form>
        )}
        {paso === "configurar" && qr && (
          <form className="ingreso-form" onSubmit={enviarCodigo}>
            <h1>Activa la verificación en dos pasos<span className="maq lima">una sola vez</span></h1>
            <p className="gris">Tu perfil puede ver documentos confidenciales. Escanea el código con Google Authenticator, Microsoft Authenticator o similar, y escribe el código de 6 dígitos que aparece.</p>
            <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={qr.img} width={168} height={168} alt="Código QR para tu app autenticadora" style={{ borderRadius: 12 }} />
              <span className="gris2" style={{ fontSize: ".78rem", maxWidth: 220 }}>¿No puedes escanear? Ingresa esta clave a mano:<br /><b className="maq lima" style={{ overflowWrap: "anywhere" }}>{qr.secreto}</b></span>
            </div>
            {codigo}
            {error && <p className="error-form" role="alert">{error}</p>}
            <button className="btn btn-prim" type="submit" disabled={cargando || digitos.join("").length < 6}>Activar e ingresar</button>
          </form>
        )}
        {paso === "verificar" && (
          <form className="ingreso-form" onSubmit={enviarCodigo}>
            <h1>Verificación en dos pasos<span className="maq lima">abre tu app autenticadora</span></h1>
            <p className="gris">Escribe el código de 6 dígitos que muestra tu app.</p>
            {codigo}
            {error && <p className="error-form" role="alert">{error}</p>}
            <button className="btn btn-prim" type="submit" disabled={cargando || digitos.join("").length < 6}>{cargando ? "Verificando…" : "Verificar e ingresar"}</button>
            <button className="btn btn-sec" type="button" onClick={() => { setPaso("clave"); setError(""); }}><Icono n="volver" />Volver</button>
          </form>
        )}
        <p className="ingreso-pie"><Icono n="candado" />Conexión cifrada. Cada ingreso queda en la auditoría.</p>
      </div>
    </div>
  );
}
