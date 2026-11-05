"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import Icono from "./Icono";
import Logo from "./Logo";
import { cliente } from "@/lib/demo";
import { modoDemo, salir, yo, type Yo } from "@/lib/api";

type Item = { h: string; n: string; i: string; c?: string; corto?: string };
const grupos: { t: string; items: Item[] }[] = [
  { t: "Trabajo", items: [
    { h: "/inicio/", n: "Inicio", i: "inicio" },
    { h: "/captura/", n: "Captura", i: "captura", c: "1" },
    { h: "/validacion/", n: "Validación", i: "validacion", c: "214" },
  ]},
  { t: "Archivo", items: [
    { h: "/archivo/", n: "Archivo", i: "archivo" },
    { h: "/busqueda/", n: "Búsqueda y asistente", i: "busqueda", corto: "Búsqueda" },
    { h: "/conservacion/", n: "Conservación", i: "conservacion" },
  ]},
  { t: "Control", items: [
    { h: "/auditoria/", n: "Auditoría", i: "auditoria" },
    { h: "/dispositivos/", n: "Dispositivos", i: "dispositivos" },
    { h: "/integraciones/", n: "Integraciones", i: "integraciones" },
  ]},
];
const todos = grupos.flatMap((g) => g.items);
// En el celular: los cuatro de todos los días en la barra inferior; el resto en «Más».
const barra = ["/inicio/", "/captura/", "/validacion/", "/busqueda/"];

export default function Shell({ children }: { children: React.ReactNode }) {
  const ruta = usePathname() || "/";
  const [mas, setMas] = useState(false);
  const [montado, setMontado] = useState(false);
  const router = useRouter();
  const [usuario, setUsuario] = useState<Yo | null>(null);
  // Con API: solo se entra con sesión completa (clave + verificación en dos pasos si el rol lo exige).
  useEffect(() => { if (!modoDemo) yo().then(setUsuario).catch(() => router.replace("/")); }, [router]);
  useEffect(() => setMontado(true), []);
  useEffect(() => { setMas(false); }, [ruta]);
  useEffect(() => {
    if (!mas) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && setMas(false);
    window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k);
  }, [mas]);
  const iniciales = (usuario?.name ?? "Ana R.").split(/\s+/).map((p) => p[0]).join("").slice(0, 2).toUpperCase();
  const activo = (h: string) => ruta === h || ruta.startsWith(h) || (h === "/archivo/" && ruta.startsWith("/expedientes"));
  const fuera = async () => { await salir().catch(() => {}); router.replace("/"); };
  const resto = todos.filter((it) => !barra.includes(it.h));
  const masActivo = resto.some((it) => activo(it.h));

  return (
    <div className="app">
      <aside className="lateral glass-dark" aria-label="Navegación principal">
        <Link href="/inicio/" className="marca">
          <Logo />
          <b>Arriera<small>Gestión documental con IA</small></b>
        </Link>
        <nav className="nav">
          {grupos.map((g) => (
            <div key={g.t} style={{ display: "grid", gap: 2 }}>
              <span className="nav-t">{g.t}</span>
              {g.items.map((it) => (
                <Link key={it.h} href={it.h} className={activo(it.h) ? "activo" : ""} aria-current={activo(it.h) ? "page" : undefined}>
                  <Icono n={it.i} />{it.n}{it.c && modoDemo ? <span className="cuenta">{it.c}</span> : null}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="lateral-pie">
          {modoDemo && <div className="estacion">
            <span className="estado on"><i />5 de 6 dispositivos en línea</span>
            <b>Estación Archivo 1</b>
            <span className="gris2">Ricoh fi-8170 · lector QR</span>
          </div>}
          <div className="cliente">
            <span className="logo-c">{cliente.corto}</span>
            <span><b>{cliente.nombre}</b>{cliente.detalle}</span>
          </div>
        </div>
      </aside>
      <div className="principal">
        <header className="barra-sup glass-chrome">
          <Link href="/inicio/" className="marca-movil" aria-label="Arriera, inicio"><Logo /></Link>
          <form className="buscador" action="/busqueda/" role="search">
            <Icono n="busqueda" />
            <input id="buscar-global" name="q" placeholder="Busca por nombre, DNI, fecha o escribe una pregunta" aria-label="Buscar en el archivo" />
            <kbd>/</kbd>
          </form>
          <div className="der">
            <button className="icono-btn solo-escritorio" aria-label="Avisos"><Icono n="campana" /><span className="punto" /></button>
            <div className="usuario"><span className="avatar">{iniciales}</span><span className="nombre"><b style={{ fontWeight: 500, color: "var(--blanco)" }}>{usuario?.name ?? "Ana R."}</b><br /><span className="gris2">{usuario ? usuario.roles.join(", ") : "Archivera"}</span></span></div>
            {!modoDemo && <button className="icono-btn solo-escritorio" aria-label="Salir" title="Salir" onClick={fuera}><Icono n="salir" /></button>}
          </div>
        </header>
        <main className="contenido">{children}</main>
      </div>

      <nav className="barra-inf glass-dark" aria-label="Navegación">
        {barra.map((h) => { const it = todos.find((x) => x.h === h)!; return (
          <Link key={h} href={h} className={activo(h) ? "activo" : ""} aria-current={activo(h) ? "page" : undefined}>
            <Icono n={it.i} /><span>{it.corto ?? it.n}</span>
          </Link>
        ); })}
        <button className={masActivo || mas ? "activo" : ""} onClick={() => setMas(true)} aria-haspopup="dialog" aria-expanded={mas}>
          <Icono n="cuadricula" /><span>Más</span>
        </button>
      </nav>

      {montado && mas && createPortal(
        <div className="hoja-fondo" onClick={() => setMas(false)}>
          <div className="hoja glass-dark" role="dialog" aria-modal="true" aria-label="Más secciones" onClick={(e) => e.stopPropagation()}>
            <span className="hoja-asa" aria-hidden="true" />
            <div className="hoja-cab">
              <b>Más secciones</b>
              <button className="icono-btn" onClick={() => setMas(false)} aria-label="Cerrar"><Icono n="x" /></button>
            </div>
            <div className="hoja-rejilla">
              {resto.map((it) => (
                <Link key={it.h} href={it.h} className={activo(it.h) ? "activo" : ""} onClick={() => setMas(false)}>
                  <Icono n={it.i} /><span>{it.corto ?? it.n}</span>
                </Link>
              ))}            </div>
            <div className="hoja-pie">
              <span className="cliente"><span className="logo-c">{cliente.corto}</span><span><b>{cliente.nombre}</b>{cliente.detalle}</span></span>
              {!modoDemo && <button className="btn btn-sec" onClick={fuera}><Icono n="salir" />Cerrar sesión</button>}
            </div>
          </div>
        </div>, document.body)}
    </div>
  );
}
