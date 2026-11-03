import hashlib

from sqlalchemy import select

from arriera.config import settings
from arriera.db import SessionLocal
from arriera.models import AuditEvent, Documento, Extraccion, Lote, Persona
from arriera.procesamiento import documentos as proc
from arriera.providers.llm import LLMAnthropic
from arriera.security.cifrado import hmac_busqueda
from tests import ia_simulada
from tests.conftest import CLAVE
from tests.paginas_demo import pagina_con_texto

SOLICITUD = [
    "Solicitud de subsidio por enfermedad",
    "Asociada: Rosa Huamán Quispe · DNI 41234518",
    "Fecha: 14 de marzo de 2018 · Expediente 2018-0412",
    "Monto solicitado: S/ 1,250.00",
]
SOLICITUD_2 = [
    "Página 2 de 2",
    "Declaro que los datos son verdaderos",
    "Firma de la asociada",
    "Sello de mesa de partes",
]
INFORME = [
    "Informe médico",
    "Paciente: Rosa Huamán Quispe",
    "Diagnóstico: lumbalgia mecánica",
    "Reposo: siete días · CMP 00000",
]
BOLETA = [
    "Boleta de pago",
    "Trabajadora: Rosa Huamán Quispe",
    "Periodo: febrero 2018",
    "Neto a pagar: S/ 2,100.00",
]


def _lote_con_paginas(c, caja, hojas):
    c.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    code = c.post("/captura/lotes", json={"caja": caja}).json()["code"]
    token = c.post(f"/captura/lotes/{code}/emparejar").json()["url"].split("t=")[1]
    llave = c.post("/estacion/emparejar", json={"token": token, "modelo": "Prueba"}).json()["llave"]
    for h in hojas:
        d = pagina_con_texto(h)
        r = c.post(
            f"/estacion/lotes/{code}/paginas",
            headers={"X-Station-Key": llave},
            files={"archivo": ("p.jpg", d, "image/jpeg")},
            data={"sha256": hashlib.sha256(d).hexdigest()},
        )
        assert r.status_code == 201
    return code


def test_ia_separa_clasifica_extrae_y_valida(cliente, monkeypatch):
    llamadas: list = []
    monkeypatch.setattr(
        proc, "proveedor_llm", lambda: LLMAnthropic("k-demo", transporte=ia_simulada.transporte(llamadas))
    )
    code = _lote_con_paginas(cliente, "C-0047", [SOLICITUD, SOLICITUD_2, INFORME, BOLETA])
    r = cliente.post(f"/captura/lotes/{code}/cerrar")
    assert r.status_code == 200, r.text
    lote = cliente.get(f"/captura/lotes/{code}").json()
    assert lote["ia"]["estado"] == "listo" and lote["ia"]["documentos"] == 3, lote["ia"]
    assert llamadas.count("separacion") == 1 and llamadas.count("clasificacion") == 3
    cliente.post("/auth/logout")

    # El validador ve la cola: tres documentos, con sus páginas.
    cliente.post("/auth/login", json={"email": "validacion@demo.arriera.tech", "password": CLAVE})
    docs = {d["tipo"]: d for d in cliente.get("/documentos", params={"lote": code}).json()}
    assert set(docs) == {"solicitud_subsidio", "informe_medico", "boleta_pago"}
    assert [p["indice"] for p in docs["solicitud_subsidio"]["paginas"]] == [1, 2]
    assert docs["informe_medico"]["sensibilidad"] == "N3"

    sol = cliente.get(f"/documentos/{docs['solicitud_subsidio']['id']}").json()
    campos = {c["key"]: c for c in sol["campos"]}
    assert campos["dni_titular"]["estado"] == "auto_aceptado"
    assert campos["fecha_solicitud"]["valor"] == "2018-03-14"
    assert campos["monto_solicitado"]["estado"] == "pendiente" and campos["monto_solicitado"]["valor"] == "1250.00"
    assert campos["codigo_asociado"]["estado"] == "vacio"
    assert campos["dni_titular"]["caja"] and campos["dni_titular"]["caja"]["pagina"] == 1
    assert sol["titulo"] == "Solicitud de subsidio · Rosa Huamán Quispe"
    # La persona se creó por DNI y el DNI no quedó en claro.
    with SessionLocal() as db:
        p = db.scalar(select(Persona).where(Persona.dni_hash == hmac_busqueda("41234518")))
        assert p is not None and p.dni_enc and "41234518" not in p.dni_enc

    inf = cliente.get(f"/documentos/{docs['informe_medico']['id']}").json()
    diag = next(c for c in inf["campos"] if c["key"] == "diagnostico")
    assert diag["estado"] == "pendiente" and diag["sensible"]
    bol = cliente.get(f"/documentos/{docs['boleta_pago']['id']}").json()
    assert any(t["tipo"] == "clasificacion" for t in bol["tareas"])

    # Corrige el monto y el documento queda validado.
    tarea = next(t for t in sol["tareas"] if t["campo"] == campos["monto_solicitado"]["id"])
    r = cliente.post(f"/validacion/tareas/{tarea['id']}", json={"accion": "corregir", "valor": "S/ 1,300.00"})
    assert r.status_code == 200 and r.json()["estado"] == "validado", r.text
    with SessionLocal() as db:
        e = db.get(Extraccion, campos["monto_solicitado"]["id"])
        assert e.value_norm == "1300.00" and e.source == "human"
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "validacion.resuelta")) is not None
    # Un valor inválido no se acepta.
    t_diag = next(t for t in inf["tareas"] if t["campo"] == diag["id"])
    assert cliente.post(f"/validacion/tareas/{t_diag['id']}", json={"accion": "aceptar"}).status_code == 200
    cola = cliente.get("/validacion/cola").json()
    assert all(d["id"] != docs["solicitud_subsidio"]["id"] for d in cola["documentos"])


def test_presupuesto_agotado_pausa_el_procesamiento(cliente, monkeypatch):
    monkeypatch.setattr(proc, "proveedor_llm", lambda: LLMAnthropic("k-demo", transporte=ia_simulada.transporte()))
    code = _lote_con_paginas(cliente, "C-0046", [SOLICITUD])
    monkeypatch.setattr(settings(), "ia_presupuesto_usd_mes", 0.0)
    cliente.post(f"/captura/lotes/{code}/cerrar")
    with SessionLocal() as db:
        lote = db.scalar(select(Lote).where(Lote.code == code))
        assert lote.manifest["ia"]["estado"] == "pausado_presupuesto"
        assert db.scalar(select(Documento).where(Documento.batch_id == lote.id)) is None


def test_normalizacion_local():
    from arriera.procesamiento.normalizar import normalizar_valor, ubicar

    assert normalizar_valor("dni", "4123 4518") == ("41234518", None)
    assert normalizar_valor("dni", "412345")[1]
    assert normalizar_valor("date", "14/03/18") == ("2018-03-14", None)
    assert normalizar_valor("date", "1990-01-01")[1]
    assert normalizar_valor("money_pen", "S/ 1,250.00") == ("1250.00", None)
    assert normalizar_valor("money_pen", "1.250,50") == ("1250.50", None)
    assert normalizar_valor("enum", "Enfermedad", ["enfermedad", "otro"]) == ("enfermedad", None)
    palabras = [
        {"texto": "Monto:", "x0": 0.1, "y0": 0.2, "x1": 0.2, "y1": 0.22},
        {"texto": "S/", "x0": 0.21, "y0": 0.2, "x1": 0.24, "y1": 0.22},
        {"texto": "1,250.00", "x0": 0.25, "y0": 0.2, "x1": 0.35, "y1": 0.22},
    ]
    assert ubicar(palabras, "S/ 1,250.00") == {"x0": 0.21, "y0": 0.2, "x1": 0.35, "y1": 0.22, "conf": None}


def test_ocr_corrobora_un_dni_impreso_una_sola_vez():
    from arriera.procesamiento.documentos import evaluar_campo

    dni = {"key": "dni_titular", "nombre": "DNI", "type": "dni", "required": True, "auto_accept": 0.97}
    ia = {"valor_original": "41234518", "valor": "41234518", "confianza": 0.95, "pagina": 1}
    una = [{"texto": "DNI:", "x0": 0.1, "y0": 0.1, "x1": 0.15, "y1": 0.12, "conf": 0.96},
           {"texto": "41234518", "x0": 0.16, "y0": 0.1, "x1": 0.3, "y1": 0.12, "conf": 0.96}]  # fmt: skip
    r = evaluar_campo(dni, ia, 1, lambda n: una)
    assert r["estado"] == "auto_aceptado" and r["corroborado"]
    dos = una + [{"texto": "41234518", "x0": 0.16, "y0": 0.5, "x1": 0.3, "y1": 0.52, "conf": 0.96}]
    assert evaluar_campo(dni, ia, 1, lambda n: dos)["estado"] == "pendiente"
    borroso = [{**w, "conf": 0.6} for w in una]
    assert evaluar_campo(dni, ia, 1, lambda n: borroso)["estado"] == "pendiente"
