import threading

from sqlalchemy import text

from arriera.audit import cadena
from arriera.db import SessionLocal, engine
from tests.conftest import CLAVE, ingresar_con_2fa


def test_permisos_de_auditoria(cliente):
    assert cliente.get("/audit").status_code == 401
    cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    assert cliente.get("/audit").status_code == 403  # operador no ve la auditoría
    cliente.post("/auth/logout")
    ingresar_con_2fa(cliente, "auditoria@demo.arriera.tech")
    eventos = cliente.get("/audit?limite=20").json()
    assert eventos and {"auth.login", "auth.2fa_activada"} & {e["action"] for e in eventos}


def test_cadena_integra_y_concurrente(cliente):
    def escribir(i):
        with SessionLocal() as db:
            cadena.registrar(db, "prueba.concurrencia", actor_type="system", details={"i": i})
            db.commit()

    hilos = [threading.Thread(target=escribir, args=(i,)) for i in range(12)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    ingresar_con_2fa(cliente, "auditoria@demo.arriera.tech")
    v = cliente.get("/audit/verify-chain").json()
    assert v["integra"] is True and v["eventos"] > 12


def test_la_base_impide_modificar_la_auditoria():
    with engine().connect() as c:
        try:
            c.execute(text("DELETE FROM audit_events"))
            raise AssertionError("debió fallar")
        except Exception as e:  # noqa: BLE001
            assert "solo inserción" in str(e)


def test_detecta_alteracion_directa(cliente):
    # Simula a un atacante con acceso de superusuario que desactiva el trigger y altera un evento.
    with engine().begin() as c:
        c.execute(text("ALTER TABLE audit_events DISABLE TRIGGER audit_events_inmutable"))
        c.execute(
            text(
                "UPDATE audit_events SET details = '{\"alterado\": true}' WHERE id = (SELECT min(id) + 1 FROM audit_events)"
            )
        )
        c.execute(text("ALTER TABLE audit_events ENABLE TRIGGER audit_events_inmutable"))
    with SessionLocal() as db:
        v = cadena.verificar(db)
    assert v.integra is False and v.motivo == "El contenido del evento fue alterado."
