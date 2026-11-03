import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from arriera.config import settings
from arriera.models import Sesion, User


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def crear(db: Session, user: User, mfa_ok: bool, ip: str | None, ua: str | None) -> str:
    token = secrets.token_urlsafe(32)
    ahora = datetime.now(UTC)
    vida = (
        timedelta(hours=settings().sesion_max_horas) if mfa_ok else timedelta(minutes=settings().mfa_pendiente_min)
    )
    db.add(
        Sesion(
            token_hash=_hash(token),
            user_id=user.id,
            mfa_ok=mfa_ok,
            expires_at=ahora + vida,
            ip=ip,
            user_agent=(ua or "")[:300],
        )
    )
    return token


def buscar(db: Session, token: str | None) -> Sesion | None:
    if not token:
        return None
    s = db.scalar(select(Sesion).where(Sesion.token_hash == _hash(token)))
    if s is None or s.revoked_at is not None:
        return None
    ahora = datetime.now(UTC)
    if s.expires_at <= ahora:
        return None
    if s.mfa_ok and s.last_seen_at + timedelta(minutes=settings().sesion_inactividad_min) <= ahora:
        return None
    return s


def tocar(s: Sesion) -> None:
    s.last_seen_at = datetime.now(UTC)


def revocar(s: Sesion) -> None:
    s.revoked_at = datetime.now(UTC)
