import logging

import pyotp

from tests.conftest import CLAVE


def test_operador_ingresa_sin_2fa(cliente):
    r = cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    assert r.status_code == 200 and r.json()["paso"] == "listo"
    galleta = r.headers["set-cookie"].lower()
    assert "httponly" in galleta and "samesite=lax" in galleta
    yo = cliente.get("/auth/me").json()
    assert yo["roles"] == ["operador"] and yo["requiere_2fa"] is False


def test_archivera_debe_configurar_y_usar_2fa(cliente):
    r = cliente.post("/auth/login", json={"email": "archivo@demo.arriera.tech", "password": CLAVE})
    assert r.json()["paso"] == "configurar_2fa"
    assert cliente.get("/auth/me").status_code == 401  # sesión parcial no da acceso
    conf = cliente.post("/auth/2fa/configurar").json()
    assert conf["uri"].startswith("otpauth://totp/Arriera:") and conf["qr_svg"].startswith("<svg")
    assert cliente.post("/auth/2fa/verificar", json={"codigo": "000000"}).status_code == 401
    ok = cliente.post("/auth/2fa/verificar", json={"codigo": pyotp.TOTP(conf["secreto"]).now()})
    assert ok.status_code == 200 and ok.json()["paso"] == "listo"
    assert cliente.get("/auth/me").json()["roles"] == ["archivero"]
    # El segundo ingreso ya pide el código, no la configuración.
    cliente.post("/auth/logout")
    assert (
        cliente.post("/auth/login", json={"email": "archivo@demo.arriera.tech", "password": CLAVE}).json()["paso"]
        == "verificar_2fa"
    )


def test_clave_incorrecta_bloquea_tras_cinco_intentos(cliente):
    for _ in range(5):
        r = cliente.post("/auth/login", json={"email": "consulta@demo.arriera.tech", "password": "incorrecta"})
        assert r.status_code == 401 and r.json()["detail"] == "Correo o contraseña incorrectos."
    r = cliente.post("/auth/login", json={"email": "consulta@demo.arriera.tech", "password": CLAVE})
    assert r.status_code == 429


def test_correo_inexistente_responde_igual(cliente):
    r = cliente.post("/auth/login", json={"email": "nadie@demo.arriera.tech", "password": "x"})
    assert r.status_code == 401 and r.json()["detail"] == "Correo o contraseña incorrectos."


def test_logout_cierra_la_sesion(cliente):
    cliente.post("/auth/login", json={"email": "validacion@demo.arriera.tech", "password": CLAVE})
    assert cliente.get("/auth/me").status_code == 200
    assert cliente.post("/auth/logout").status_code == 204
    assert cliente.get("/auth/me").status_code == 401


def test_no_hay_datos_personales_en_los_logs(cliente, caplog):
    caplog.set_level(logging.DEBUG)
    cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    texto = caplog.text
    assert "captura@demo.arriera.tech" not in texto and CLAVE not in texto
