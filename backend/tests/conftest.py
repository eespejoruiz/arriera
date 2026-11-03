import base64
import os

import pytest

# Base de pruebas aislada y claves efímeras. Nunca datos reales.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://arriera:arriera@localhost:5433/arriera_test")
os.environ["CIFRADO_KEY"] = base64.b64encode(os.urandom(32)).decode()
os.environ["DNI_HMAC_KEY"] = base64.b64encode(os.urandom(32)).decode()
os.environ["COOKIE_SEGURA"] = "false"
os.environ["ARRIERA_DEMO_CLAVE"] = "Prueba-Arriera-2026"
os.environ["ALMACEN"] = "local"
os.environ["ALMACEN_LOCAL_DIR"] = __import__("tempfile").mkdtemp(prefix="arriera-almacen-")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from arriera.config import settings  # noqa: E402
from arriera.db import engine  # noqa: E402

CLAVE = os.environ["ARRIERA_DEMO_CLAVE"]


@pytest.fixture(scope="session", autouse=True)
def base_limpia():
    settings.cache_clear()
    with engine().begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    command.upgrade(cfg, "head")
    from arriera.seed import sembrar

    sembrar(demo=True)
    yield


@pytest.fixture
def cliente():
    from arriera.main import crear_app

    with TestClient(crear_app()) as c:
        yield c


def ingresar_con_2fa(c: TestClient, email: str) -> None:
    """Hace el flujo completo: clave, configuración de TOTP si hace falta y código."""
    import pyotp

    from arriera.db import SessionLocal
    from arriera.models import User
    from arriera.security import cifrado

    r = c.post("/auth/login", json={"email": email, "password": CLAVE})
    assert r.status_code == 200, r.text
    if r.json()["paso"] == "configurar_2fa":
        secreto = c.post("/auth/2fa/configurar").json()["secreto"]
    else:
        with SessionLocal() as db:
            u = db.query(User).filter_by(email=email).one()
            secreto = cifrado.descifrar(u.totp_secret_enc, f"totp:{u.id}")
    r = c.post("/auth/2fa/verificar", json={"codigo": pyotp.TOTP(secreto).now()})
    assert r.status_code == 200 and r.json()["paso"] == "listo", r.text
