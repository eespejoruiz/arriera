from tests.conftest import CLAVE, ingresar_con_2fa


def test_solo_admin_crea_usuarios(cliente):
    cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    nuevo = {
        "email": "nuevo@demo.arriera.tech",
        "name": "Nuevo (demo)",
        "password": "Clave-Segura-2026",
        "roles": ["consulta"],
    }
    assert cliente.post("/users", json=nuevo).status_code == 403
    cliente.post("/auth/logout")
    ingresar_con_2fa(cliente, "admin@demo.arriera.tech")
    assert cliente.post("/users", json={**nuevo, "password": "debilisima12"}).status_code == 422
    r = cliente.post("/users", json=nuevo)
    assert r.status_code == 201 and r.json()["roles"] == ["consulta"]
    assert cliente.post("/users", json=nuevo).status_code == 409
