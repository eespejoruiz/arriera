// Íconos de línea propios (trazo 1.8, extremos redondeados). Sin dependencias.
const P: Record<string, string> = {
  inicio: "M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z",
  captura: "M4 8V5h3M17 5h3v3M20 16v3h-3M7 19H4v-3M7 12h10",
  inventario: "M4 7l8-4 8 4-8 4-8-4zM4 7v10l8 4 8-4V7M12 11v10",
  validacion: "M9 12l2 2 4-4M5 4h14v16H5z",
  archivo: "M3 7h6l2 2h10v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z",
  busqueda: "M10.5 17a6.5 6.5 0 1 1 0-13 6.5 6.5 0 0 1 0 13zM15.5 15.5L21 21",
  asistente: "M4 5h16v11H9l-5 4zM8 9h8M8 12h5",
  conservacion: "M5 4h14v4H5zM6 8v11a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8M10 12h4",
  auditoria: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4",
  dispositivos: "M7 3h10v18H7zM11 18h2M3 9h2v6H3zM19 9h2v6h-2z",
  integraciones: "M8 7a3 3 0 1 1 0 .01M16 17a3 3 0 1 1 0 .01M10.5 8.5l3 7M5 17h6M13 7h6",
  ajustes: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19 12l2-1-2-4-2 1-2-1-1-2h-4l-1 2-2 1-2-1-2 4 2 1v2l-2 1 2 4 2-1 2 1 1 2h4l1-2 2-1 2 1 2-4-2-1z",
  campana: "M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 20h4",
  mas: "M12 5v14M5 12h14",
  escaner: "M3 14h18v5H3zM5 14l2-6h10l2 6M7 17h4",
  celular: "M8 3h8a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM11 18h2",
  red: "M6 9h12v7H6zM8 9V5h8v4M8 19h8M9 13h6",
  qr: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h2v2h-2zM18 14h2M14 18h2v2M18 18h2v2",
  pistola: "M4 7h12l3 3v2H8l-1 7H4l1-7H4z",
  camara: "M4 8h3l2-3h6l2 3h3v11H4zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  ojo: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  descargar: "M12 4v11M7 10l5 5 5-5M5 20h14",
  check: "M5 12.5l4.5 4.5L19 7",
  x: "M6 6l12 12M18 6L6 18",
  alerta: "M12 4l9 16H3zM12 10v4M12 17v.01",
  reloj: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
  candado: "M6 11h12v9H6zM8 11V8a4 4 0 0 1 8 0v3",
  doc: "M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6",
  flecha: "M5 12h14M13 6l6 6-6 6",
  volver: "M19 12H5M11 6l-6 6 6 6",
  ia: "M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z",
  menu: "M4 7h16M4 12h16M4 17h16",
  cuadricula: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
  cortar: "M6 7a2 2 0 1 0 0 .01M6 17a2 2 0 1 0 0 .01M8 8l12 9M8 16l12-9",
  unir: "M8 6v12M16 6v12M8 12h8",
  copiar: "M8 8h11v13H8zM5 16H4V3h11v1",
  enviar: "M4 12l16-8-6 16-2-7z",
  llave: "M14 10a4 4 0 1 0-3.5 4L9 16v2H7v2H4v-3l6.2-6.2",
  webhook: "M12 8a3 3 0 1 1 2.6 3M9 17a3 3 0 1 1-1.4-5.6L12 4M15 14h5a3 3 0 1 1-2.6 4.5",
  caja: "M3 8l9-4 9 4v10l-9 4-9-4zM3 8l9 4 9-4M12 12v10",
  usuario: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0",
  salir: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10",
};
export default function Icono({ n, className }: { n: keyof typeof P | string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>
      <path d={P[n] ?? P.doc} />
    </svg>
  );
}
