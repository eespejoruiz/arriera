import hashlib

from sqlalchemy import select

from arriera.db import SessionLocal
from arriera.models import AuditEvent
from tests.conftest import CLAVE, ingresar_con_2fa
from tests.paginas_demo import pagina


def _subir(c, code, llave, datos, sha=None):
    return c.post(
        f"/estacion/lotes/{code}/paginas",
        headers={"X-Station-Key": llave},
        files={"archivo": ("p.jpg", datos, "image/jpeg")},
        data={"sha256": sha or hashlib.sha256(datos).hexdigest()},
    )


def test_flujo_completo_de_captura_con_celular(cliente):
    # La archivera registra la caja y descarga su etiqueta.
    ingresar_con_2fa(cliente, "archivo@demo.arriera.tech")
    r = cliente.post(
        "/cajas",
        json={
            "code": "C-0145",
            "shelf_location": "B-3",
            "year_from": 2017,
            "year_to": 2018,
            "series_hint": "Beneficios",
            "estimated_pages": 2200,
        },
    )
    assert r.status_code == 201, r.text
    assert cliente.get("/cajas/C-0145/etiqueta.pdf").content[:4] == b"%PDF"
    cliente.post("/auth/logout")

    # El operador crea el lote, imprime la hoja y genera el QR para el celular.
    cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    lote = cliente.post("/captura/lotes", json={"caja": "C-0045", "origen": "celular"}).json()
    code = lote["code"]
    assert code.startswith("L-") and lote["estado"] == "creado"
    assert cliente.get(f"/captura/lotes/{code}/hoja.pdf").content[:4] == b"%PDF"
    emp = cliente.post(f"/captura/lotes/{code}/emparejar").json()
    token = emp["url"].split("t=")[1]
    assert emp["qr_svg"].startswith("<svg")

    # El celular canjea el código (una sola vez) y recibe su llave.
    canje = cliente.post("/estacion/emparejar", json={"token": token, "modelo": "Teléfono de prueba"})
    assert canje.status_code == 200 and canje.json()["lote"] == code
    llave = canje.json()["llave"]
    assert cliente.post("/estacion/emparejar", json={"token": token}).status_code == 410

    # Huella incorrecta: se rechaza. Correcta: se recibe. Reintento: no duplica.
    ok = pagina("foto_mesa")
    assert _subir(cliente, code, llave, ok, sha="0" * 64).status_code == 422
    r1 = _subir(cliente, code, llave, ok)
    assert r1.status_code == 201 and r1.json()["pagina"] == 1
    assert _subir(cliente, code, llave, ok).json()["pagina"] == 1
    for v in ("inclinada", "borrosa", "blanco"):
        assert _subir(cliente, code, llave, pagina(v)).status_code == 201

    det = cliente.get(f"/captura/lotes/{code}").json()
    estados = {p["indice"]: p["estado"] for p in det["paginas"]}
    assert estados == {1: "ok", 2: "corregida", 3: "reescanear", 4: "en_blanco"}
    assert det["estado"] == "con_rechazos" and det["rechazos"] == 1
    pid = det["paginas"][0]["id"]
    m = cliente.get(f"/captura/paginas/{pid}/miniatura")
    assert m.status_code == 200 and m.headers["content-type"] == "image/webp"
    assert cliente.post(f"/captura/lotes/{code}/cerrar").status_code == 409  # hay una página por reescanear

    # Sin llave o con llave de otro lote: rechazado.
    assert _subir(cliente, code, "est_falsa", ok).status_code == 401
    lote2 = cliente.post("/captura/lotes", json={"caja": "C-0045"}).json()["code"]
    assert _subir(cliente, lote2, llave, pagina("ok", 7)).status_code == 403

    # Cada página recibida quedó en la auditoría con su huella.
    with SessionLocal() as db:
        eventos = db.scalars(select(AuditEvent).where(AuditEvent.action == "captura.pagina_recibida")).all()
        assert {e.details["sha256"] for e in eventos} >= {hashlib.sha256(ok).hexdigest()}


def test_consulta_no_puede_capturar(cliente):
    cliente.post("/auth/login", json={"email": "validacion@demo.arriera.tech", "password": CLAVE})
    assert cliente.post("/captura/lotes", json={"caja": "C-0045"}).status_code == 403
    assert cliente.get("/cajas").status_code == 403
