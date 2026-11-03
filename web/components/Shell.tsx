"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import Icono from "./Icono";
import Logo from "./Logo";
import { cliente } from "@/lib/demo";

const grupos = [
  { t: "Trabajo", items: [
    { h: "/inicio/", n: "Inicio", i: "inicio" },
    { h: "/captura/", n: "Captura", i: "captura", c: "1" },
    { h: "/validacion/", n: "Validación", i: "validacion", c: "214" },
  ]},
  { t: "Archivo", items: [
    { h: "/archivo/", n: "Archivo", i: "archivo" },
    { h: "/busqueda/", n: "Búsqueda y asistente", i: "busqueda" },
    { h: "/conservacion/", n: "Conservación", i: "conservacion" },
  ]},
  { t: "Control", items: [
    { h: "/auditoria/", n: "Auditoría", i: "auditoria" },
    { h: "/dispositivos/", n: "Dispositivos", i: "dispositivos" },
    { h: "/integraciones/", n: "Integraciones", i: "integraciones" },
  ]},
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const ruta = usePathname() || "/";
  const [abierta, setAbierta] = useState(false);
  const activo = (h: string) => ruta === h || ruta.startsWith(h) || (h === "/archivo/" && ruta.startsWith("/expedientes"));
  return (
    <div className="app">
      <aside className={"lateral" + (abierta ? " abierta" : "")} aria-label="Navegación principal">
        <Link href="/inicio/" className="marca" onClick={() => setAbierta(false)}>
          <Logo />
          <b>Arriera<small>Gestión documental con IA</small></b>
        </Link>
        <nav className="nav">
          {grupos.map((g) => (
            <div key={g.t} style={{ display: "grid", gap: 2 }}>
              <span className="nav-t">{g.t}</span>
              {g.items.map((it) => (
                <Link key={it.h} href={it.h} className={activo(it.h) ? "activo" : ""} onClick={() => setAbierta(false)}>
                  <Icono n={it.i} />{it.n}{it.c ? <span className="cuenta">{it.c}</span> : null}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="lateral-pie">
          <div className="estacion">
            <span className="estado on"><i />5 de 6 dispositivos en línea</span>
            <b>Estación Archivo 1</b>
            <span className="gris2">Ricoh fi-8170 · lector QR</span>
          </div>
          <div className="cliente">
            <span className="logo-c">{cliente.corto}</span>
            <span><b>{cliente.nombre}</b>{cliente.detalle}</span>
          </div>
        </div>
      </aside>
      {abierta && <div onClick={() => setAbierta(false)} style={{ position: "fixed", inset: 0, zIndex: 55, background: "rgba(0,0,0,.5)" }} />}
      <div className="principal">
        <header className="barra-sup">
          <button className="icono-btn menu-movil" aria-label="Abrir menú" onClick={() => setAbierta(true)}><Icono n="menu" /></button>
          <form className="buscador" action="/busqueda/" role="search">
            <Icono n="busqueda" />
            <input id="buscar-global" name="q" placeholder="Busca por nombre, DNI, fecha o escribe una pregunta" aria-label="Buscar en el archivo" />
            <kbd>/</kbd>
          </form>
          <div className="der">
            <button className="icono-btn" aria-label="Avisos"><Icono n="campana" /><span className="punto" /></button>
            <div className="usuario"><span className="avatar">AR</span><span className="nombre"><b style={{ fontWeight: 500, color: "var(--blanco)" }}>Ana R.</b><br /><span className="gris2">Archivera</span></span></div>
          </div>
        </header>
        <main className="contenido">{children}</main>
      </div>
    </div>
  );
}
