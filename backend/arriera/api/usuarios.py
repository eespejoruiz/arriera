from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.api.schemas import NuevoUsuario, UsuarioOut
from arriera.audit.cadena import registrar
from arriera.db import get_db
from arriera.models import Role, User
from arriera.security import passwords

router = APIRouter(prefix="/users", tags=["usuarios"])


def _out(u: User) -> UsuarioOut:
    return UsuarioOut(
        id=str(u.id),
        email=u.email,
        name=u.name,
        roles=u.role_keys,
        is_active=u.is_active,
        totp_confirmado=u.totp_confirmado,
    )


@router.get("", response_model=list[UsuarioOut])
def listar(_: User = Depends(requiere_roles("admin")), db: Session = Depends(get_db)):
    return [_out(u) for u in db.scalars(select(User).order_by(User.name)).all()]


@router.post("", response_model=UsuarioOut, status_code=201)
def crear(
    datos: NuevoUsuario,
    admin: User = Depends(requiere_roles("admin")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    if (msg := passwords.clave_valida(datos.password)) is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, msg)
    if db.scalar(select(User).where(func.lower(User.email) == datos.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo.")
    roles = db.scalars(select(Role).where(Role.key.in_(datos.roles))).all()
    if len(roles) != len(set(datos.roles)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Algún rol no existe.")
    u = User(
        email=datos.email.lower(),
        name=datos.name,
        password_hash=passwords.hashear(datos.password),
        roles=list(roles),
    )
    db.add(u)
    db.flush()
    registrar(
        db,
        "usuario.creado",
        user_id=admin.id,
        object_type="user",
        object_id=str(u.id),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        details={"roles": sorted(datos.roles)},
    )
    db.commit()
    return _out(u)
