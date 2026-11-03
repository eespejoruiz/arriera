import ipaddress
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from arriera.config import settings
from arriera.db import get_db
from arriera.models import Sesion, User
from arriera.security import sesiones


@dataclass
class Contexto:
    ip: str | None
    user_agent: str | None


def _ip_valida(valor: str | None) -> str | None:
    try:
        return str(ipaddress.ip_address((valor or "").strip()))
    except ValueError:
        return None


def contexto(request: Request) -> Contexto:
    # X-Forwarded-For solo es confiable detrás del proxy propio (Caddy/Traefik), que lo reescribe.
    reenviada = request.headers.get("x-forwarded-for", "").split(",")[0]
    ip = _ip_valida(reenviada) or _ip_valida(request.client.host if request.client else None)
    return Contexto(ip=ip, user_agent=request.headers.get("user-agent"))


def sesion_actual(request: Request, db: Session = Depends(get_db)) -> Sesion:
    s = sesiones.buscar(db, request.cookies.get(settings().cookie_nombre))
    if s is None or not s.user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión terminó. Vuelve a ingresar.")
    return s


def sesion_completa(s: Sesion = Depends(sesion_actual), db: Session = Depends(get_db)) -> Sesion:
    if not s.mfa_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta la verificación en dos pasos.")
    sesiones.tocar(s)
    db.commit()
    return s


def usuario(s: Sesion = Depends(sesion_completa)) -> User:
    return s.user


def requiere_roles(*claves: str):
    """Permite el acceso solo a quien tenga al menos uno de los roles. Se aplica en el servidor."""

    def _dep(u: User = Depends(usuario)) -> User:
        if not set(claves) & set(u.role_keys):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu perfil no tiene permiso para esta acción.")
        return u

    return _dep
