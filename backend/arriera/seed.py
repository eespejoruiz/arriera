"""Semillas: roles base y, con --demo, usuarios de DATOS DEMO.

Uso:  python -m arriera.seed            (solo roles)
      python -m arriera.seed --demo     (roles + usuarios demo; clave en ARRIERA_DEMO_CLAVE)
"""

import os
import sys

from sqlalchemy import select

from arriera.audit.cadena import registrar
from arriera.db import SessionLocal
from arriera.models import Role, User
from arriera.security import passwords

ROLES = [
    ("admin", "Administrador", True),
    ("archivero", "Archivero o supervisor", True),
    ("operador", "Operador de captura", False),
    ("validador", "Validador", False),
    ("consulta", "Consulta", False),
    ("aprobador", "Aprobador de depuración", True),
    ("auditor", "Auditor u oficial de datos personales", True),
]

DEMO = [  # DATOS DEMO · correos ficticios
    ("admin@demo.arriera.tech", "Administración (demo)", ["admin"]),
    ("archivo@demo.arriera.tech", "Ana R. · Archivera (demo)", ["archivero"]),
    ("captura@demo.arriera.tech", "Julio P. · Operador (demo)", ["operador"]),
    ("validacion@demo.arriera.tech", "Luis V. · Validador (demo)", ["validador"]),
    ("consulta@demo.arriera.tech", "Carmen L. · Consulta (demo)", ["consulta"]),
    ("auditoria@demo.arriera.tech", "Oficial de datos (demo)", ["auditor"]),
]


def sembrar(demo: bool) -> None:
    with SessionLocal() as db:
        existentes = {r.key: r for r in db.scalars(select(Role)).all()}
        for key, name, mfa in ROLES:
            if key not in existentes:
                existentes[key] = Role(key=key, name=name, requiere_2fa=mfa)
                db.add(existentes[key])
        db.flush()
        creados = 0
        if demo:
            clave = os.environ.get("ARRIERA_DEMO_CLAVE")
            if not clave or passwords.clave_valida(clave):
                sys.exit("Define ARRIERA_DEMO_CLAVE (12+ caracteres, mayúsculas, minúsculas y números).")
            for email, name, roles in DEMO:
                if db.scalar(select(User).where(User.email == email)):
                    continue
                db.add(
                    User(
                        email=email,
                        name=name,
                        password_hash=passwords.hashear(clave),
                        roles=[existentes[r] for r in roles],
                    )
                )
                creados += 1
        registrar(
            db, "sistema.semillas", actor_type="system", details={"roles": len(ROLES), "usuarios_demo": creados}
        )
        db.commit()
        print(f"Roles listos: {len(ROLES)}. Usuarios demo creados: {creados}.")


if __name__ == "__main__":
    sembrar(demo="--demo" in sys.argv)
