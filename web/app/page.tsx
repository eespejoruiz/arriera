"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Logo from "@/components/Logo";
import Icono from "@/components/Icono";

export default function Ingreso() {
  const [paso, setPaso] = useState<1 | 2>(1);
  const router = useRouter();
  return (
    <div className="ingreso">
      <div className="ingreso-foto" aria-hidden="true" />
      <div className="ingreso-caja">
        <div className="ingreso-marca"><Logo /><b>Arriera</b></div>
        <span className="pill"><span className="p" />FAMENSSALUD · archivo digital</span>
        {paso === 1 ? (
          <form className="ingreso-form" onSubmit={(e) => { e.preventDefault(); setPaso(2); }}>
            <h1>Ingresa a tu archivo<span className="maq lima">con tu cuenta</span></h1>
            <div className="campo-f"><label htmlFor="correo">Correo</label><input id="correo" className="inp" type="email" defaultValue="ana.rojas@famenssalud.demo" autoComplete="username" /></div>
            <div className="campo-f"><label htmlFor="clave">Contraseña</label><input id="clave" className="inp" type="password" defaultValue="demostracion" autoComplete="current-password" /></div>
            <button className="btn btn-prim" type="submit">Continuar</button>
            <a className="gris2" href="#" style={{ fontSize: ".82rem" }}>Olvidé mi contraseña</a>
          </form>
        ) : (
          <form className="ingreso-form" onSubmit={(e) => { e.preventDefault(); router.push("/inicio/"); }}>
            <h1>Verificación en dos pasos<span className="maq lima">abre tu app autenticadora</span></h1>
            <p className="gris">Tu rol de archivera tiene acceso a documentos confidenciales, por eso pedimos un código de 6 dígitos.</p>
            <div className="codigo-2fa">
              {["4", "8", "1", "9", "0", "3"].map((d, i) => <input key={i} id={`d${i}`} className="inp maq" defaultValue={d} maxLength={1} inputMode="numeric" aria-label={`Dígito ${i + 1}`} />)}
            </div>
            <button className="btn btn-prim" type="submit">Verificar e ingresar</button>
            <button className="btn btn-sec" type="button" onClick={() => setPaso(1)}><Icono n="volver" />Volver</button>
          </form>
        )}
        <p className="ingreso-pie"><Icono n="candado" />Conexión cifrada. Cada ingreso queda en la auditoría.</p>
      </div>
    </div>
  );
}
