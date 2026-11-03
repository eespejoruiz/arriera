import hashlib
import io

from PIL import Image

from arriera.procesamiento import documentos as proc
from arriera.providers.llm import LLMAnthropic
from tests import ia_simulada
from tests.conftest import CLAVE, ingresar_con_2fa
from tests.paginas_demo import pagina_con_texto
from tests.test_documentos import INFORME, SOLICITUD


def _a_300dpi(jpeg: bytes) -> bytes:
    im = Image.open(io.BytesIO(jpeg))
    im = im.resize((int(im.width * 2.2), int(im.height * 2.2)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def _entrar(c, email):
    c.post("/auth/logout")
    if email.startswith(("archivo", "auditoria", "admin")):
        ingresar_con_2fa(c, email)
    else:
        assert c.post("/auth/login", json={"email": email, "password": CLAVE}).status_code == 200


def _paso(c, code, paso, **kw):
    return c.post(f"/microformas/lotes/{code}/pasos/{paso}", json=kw)


def test_lote_de_microformas_de_punta_a_punta(cliente, monkeypatch):
    monkeypatch.setattr(proc, "proveedor_llm", lambda: LLMAnthropic("k", transporte=ia_simulada.transporte()))
    _entrar(cliente, "captura@demo.arriera.tech")
    code = cliente.post("/captura/lotes", json={"caja": "C-0044", "microformas": True}).json()["code"]
    assert _paso(cliente, code, "preparacion").status_code == 409  # el orden importa
    r = _paso(cliente, code, "recepcion", notas="Caja en buen estado")
    assert r.status_code == 200 and r.json()["actas"][0]["tipo"] == "apertura_lote", r.text
    token = cliente.post(f"/captura/lotes/{code}/emparejar").json()["url"].split("t=")[1]
    llave = cliente.post("/estacion/emparejar", json={"token": token, "modelo": "Prueba"}).json()["llave"]

    def subir(d):
        return cliente.post(
            f"/estacion/lotes/{code}/paginas",
            headers={"X-Station-Key": llave},
            files={"archivo": ("p.jpg", d, "image/jpeg")},
            data={"sha256": hashlib.sha256(d).hexdigest()},
        )

    subir(pagina_con_texto(INFORME))  # foto a ~150 dpi: no sirve para microformas
    det = cliente.get(f"/captura/lotes/{code}").json()
    assert det["paginas"][0]["estado"] == "reescanear" and "300" in det["paginas"][0]["motivo"]
    assert _paso(cliente, code, "preparacion").status_code == 200
    _entrar(cliente, "archivo@demo.arriera.tech")
    assert _paso(cliente, code, "digitalizacion").status_code == 409  # hay una página por repetir
    _entrar(cliente, "captura@demo.arriera.tech")
    # Se reescanea bien en un lote nuevo de la misma caja… aquí basta con subir la hoja buena y descartar la mala.
    assert subir(_a_300dpi(pagina_con_texto(SOLICITUD))).status_code == 201
    from sqlalchemy import update

    from arriera.db import SessionLocal
    from arriera.models import Pagina

    with SessionLocal() as db:  # el operador retira la hoja mala (flujo de reescaneo completo: Sprint 4)
        db.execute(
            update(Pagina)
            .where(Pagina.page_index == 1, Pagina.qc_status == "reescanear")
            .values(qc_status="en_blanco")
        )
        db.commit()
    assert cliente.post(f"/captura/lotes/{code}/cerrar").status_code == 200  # dispara la IA
    assert _paso(cliente, code, "control_calidad").status_code == 409  # falta registrar la digitalización

    # La archivera registra la digitalización; por separación de funciones no puede controlar su trabajo.
    _entrar(cliente, "archivo@demo.arriera.tech")
    assert _paso(cliente, code, "digitalizacion").status_code == 200
    r = _paso(cliente, code, "control_calidad")
    assert r.status_code == 403 and "Separación de funciones" in r.json()["detail"]

    _entrar(cliente, "validacion@demo.arriera.tech")
    assert _paso(cliente, code, "control_calidad").status_code == 200
    r = _paso(cliente, code, "indizacion")
    assert r.status_code == 409 and "por validar" in r.json()["detail"]
    doc = cliente.get("/documentos", params={"lote": code}).json()[0]
    for t in cliente.get(f"/documentos/{doc['id']}").json()["tareas"]:
        assert cliente.post(f"/validacion/tareas/{t['id']}", json={"accion": "aceptar"}).status_code == 200
    assert _paso(cliente, code, "indizacion").status_code == 200
    assert _paso(cliente, code, "grabacion").status_code == 403  # rol

    _entrar(cliente, "archivo@demo.arriera.tech")
    r = _paso(cliente, code, "grabacion")
    assert r.status_code == 200, r.text
    estado = r.json()
    assert len(estado["hash_manifiesto"]) == 64 and estado["siguiente"] is None
    cierre = next(a for a in estado["actas"] if a["tipo"] == "cierre_lote")
    pdf = cliente.get(f"/microformas/actas/{cierre['id']}.pdf")
    assert pdf.status_code == 200 and hashlib.sha256(pdf.content).hexdigest() == cierre["sha256"]


def test_panel_de_accesos_a_datos_sensibles(cliente, monkeypatch):
    monkeypatch.setattr(proc, "proveedor_llm", lambda: LLMAnthropic("k", transporte=ia_simulada.transporte()))
    _entrar(cliente, "captura@demo.arriera.tech")
    code = cliente.post("/captura/lotes", json={"caja": "C-0045"}).json()["code"]
    token = cliente.post(f"/captura/lotes/{code}/emparejar").json()["url"].split("t=")[1]
    llave = cliente.post("/estacion/emparejar", json={"token": token, "modelo": "Prueba"}).json()["llave"]
    d = pagina_con_texto(INFORME)
    cliente.post(
        f"/estacion/lotes/{code}/paginas",
        headers={"X-Station-Key": llave},
        files={"archivo": ("p.jpg", d, "image/jpeg")},
        data={"sha256": hashlib.sha256(d).hexdigest()},
    )
    cliente.post(f"/captura/lotes/{code}/cerrar")
    _entrar(cliente, "validacion@demo.arriera.tech")
    doc = cliente.get("/documentos", params={"lote": code}).json()[0]
    assert doc["sensibilidad"] == "N3"
    cliente.get(f"/documentos/{doc['id']}")
    assert cliente.get("/cumplimiento/accesos-sensibles").status_code == 403

    _entrar(cliente, "auditoria@demo.arriera.tech")
    r = cliente.get("/cumplimiento/accesos-sensibles", params={"dias": 7}).json()
    assert any(a["documento_id"] == doc["id"] and a["usuario"].startswith("Luis V.") for a in r["accesos"])
    csv = cliente.get("/cumplimiento/accesos-sensibles", params={"formato": "csv"})
    assert csv.status_code == 200 and "Informe médico" in csv.text
