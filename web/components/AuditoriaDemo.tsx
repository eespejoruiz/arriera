import { Cab } from "@/components/ui";
import Icono from "@/components/Icono";
import { auditoria } from "@/lib/demo";


const colorRol: Record<string, string> = { IA: "ok", Integración: "info", Captura: "neutro" };

export default function AuditoriaDemo() {
  return (
    <>
      <Cab titulo="Auditoría" maq="quién vio, descargó o cambió qué" desc="Registro de solo inserción, encadenado con huellas: si alguien alterara un evento, la cadena se rompe y el sistema lo detecta.">
        <button className="btn btn-sec"><Icono n="descargar" />Exportar CSV</button>
        <button className="btn btn-prim"><Icono n="auditoria" />Verificar la cadena</button>
      </Cab>
      <div className="rejilla r4">
        <div className="panel"><div className="stat"><span className="l">Eventos hoy</span><span className="v">12,408</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Vistas de documentos N3</span><span className="v">86</span><span className="d">todas con permiso</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Cadena de huellas</span><span className="v" style={{ fontSize: "1.3rem" }}><span className="estado on"><i />Íntegra</span></span><span className="d">verificada hoy 06:00</span></div></div>
        <div className="panel"><div className="stat"><span className="l">Ancla del día</span><span className="v maq" style={{ fontSize: "1.1rem" }}>5d70…9ce1</span><span className="d">enviada al administrador</span></div></div>
      </div>
      <div className="panel">
        <div className="panel-cab">
          <div className="tabs"><button className="on">Todo</button><button>Vistas y descargas</button><button>Cambios</button><button>IA e integraciones</button><button>Accesos</button></div>
          <input id="filtro-aud" className="inp" style={{ maxWidth: 260 }} placeholder="Filtrar por usuario u objeto" aria-label="Filtrar" />
        </div>
        <div className="tabla-env">
          <table className="tabla">
            <thead><tr><th>Hora</th><th>Quién</th><th>Acción</th><th>Sobre qué</th><th>IP</th><th>Huella</th></tr></thead>
            <tbody>{auditoria.map((a) => (
              <tr key={a.hora}>
                <td className="num gris">{a.hora}</td>
                <td><span className="t-princ">{a.quien}</span><span className="t-sec"><span className={`chip ${colorRol[a.rol] ?? "neutro"}`} style={{ fontSize: ".68rem", padding: "0 7px" }}>{a.rol}</span></span></td>
                <td>{a.accion}</td>
                <td className="gris" style={{ maxWidth: 320 }}>{a.objeto}</td>
                <td className="maq gris2">{a.ip}</td>
                <td className="maq lima">{a.hash}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
      <div className="aviso"><Icono n="alerta" /><span><b>Registro de incidentes:</b> si ocurre una brecha, Arriera cuenta las 48 horas para avisar a la Autoridad Nacional de Protección de Datos Personales y prepara la comunicación a los titulares.</span></div>
    </>
  );
}
