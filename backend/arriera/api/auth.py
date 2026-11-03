from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, sesion_actual, sesion_completa
from arriera.api.schemas import Codigo, Configuracion2FA, Ingreso, RespuestaIngreso, Yo
from arriera.audit.cadena import registrar
from arriera.config import settings
from arriera.db import get_db
from arriera.models import Sesion, User
from arriera.security import cifrado, passwords, sesiones, totp

router = APIRouter(prefix="/auth", tags=["autenticación"])
NO_VALIDO = "Correo o contraseña incorrectos."


def _poner_cookie(resp: Response, token: str) -> None:
    cfg = settings()
    resp.set_cookie(cfg.cookie_nombre, token, httponly=True, secure=cfg.cookie_segura, samesite="lax", path="/")


@router.post("/login", response_model=RespuestaIngreso)
def login(datos: Ingreso, resp: Response, db: Session = Depends(get_db), ctx: Contexto = Depends(contexto)):
    ahora = datetime.now(UTC)
    u = db.scalar(select(User).where(func.lower(User.email) == datos.email.lower()))
    if u is not None and u.locked_until and u.locked_until > ahora:
        registrar(db, "auth.login_bloqueado", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
        db.commit()
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Cuenta bloqueada por intentos fallidos. Intenta en unos minutos."
        )
    if u is None or not u.is_active or not passwords.verificar(u.password_hash if u else None, datos.password):
        if u is not None:
            u.failed_attempts += 1
            det = {"intentos": u.failed_attempts}
            if u.failed_attempts >= settings().max_intentos:
                u.locked_until = ahora + timedelta(minutes=settings().bloqueo_min)
                u.failed_attempts = 0
                det["bloqueado"] = True
            registrar(db, "auth.login_fallido", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent, details=det)
        else:
            registrar(
                db,
                "auth.login_fallido",
                actor_type="system",
                ip=ctx.ip,
                user_agent=ctx.user_agent,
                details={"motivo": "usuario_desconocido"},
            )
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, NO_VALIDO)

    u.failed_attempts = 0
    necesita_2fa = u.requiere_2fa or u.totp_confirmado
    token = sesiones.crear(db, u, mfa_ok=not necesita_2fa, ip=ctx.ip, ua=ctx.user_agent)
    if not necesita_2fa:
        u.last_login_at = ahora
        registrar(db, "auth.login", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
        paso, msg = "listo", "Ingresaste."
    elif u.totp_confirmado:
        registrar(db, "auth.clave_ok", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
        paso, msg = "verificar_2fa", "Ingresa el código de 6 dígitos de tu app autenticadora."
    else:
        registrar(
            db,
            "auth.clave_ok",
            user_id=u.id,
            ip=ctx.ip,
            user_agent=ctx.user_agent,
            details={"configurar_2fa": True},
        )
        paso, msg = "configurar_2fa", "Tu perfil necesita verificación en dos pasos. Configúrala para continuar."
    db.commit()
    _poner_cookie(resp, token)
    return RespuestaIngreso(paso=paso, mensaje=msg)


@router.post("/2fa/configurar", response_model=Configuracion2FA)
def configurar_2fa(
    s: Sesion = Depends(sesion_actual), db: Session = Depends(get_db), ctx: Contexto = Depends(contexto)
):
    u = s.user
    if u.totp_confirmado:
        raise HTTPException(status.HTTP_409_CONFLICT, "La verificación en dos pasos ya está configurada.")
    secreto = totp.nuevo_secreto()
    u.totp_secret_enc = cifrado.cifrar(secreto, f"totp:{u.id}")
    registrar(db, "auth.2fa_configuracion_iniciada", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
    db.commit()
    uri = totp.uri_aprovisionamiento(secreto, u.email)
    return Configuracion2FA(uri=uri, secreto=secreto, qr_svg=totp.qr_svg(uri))


@router.post("/2fa/verificar", response_model=RespuestaIngreso)
def verificar_2fa(
    datos: Codigo,
    resp: Response,
    s: Sesion = Depends(sesion_actual),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    u = s.user
    if not u.totp_secret_enc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Primero configura la verificación en dos pasos.")
    secreto = cifrado.descifrar(u.totp_secret_enc, f"totp:{u.id}")
    if not totp.verificar_codigo(secreto, datos.codigo):
        u.failed_attempts += 1
        if u.failed_attempts >= settings().max_intentos:
            u.locked_until = datetime.now(UTC) + timedelta(minutes=settings().bloqueo_min)
            u.failed_attempts = 0
            sesiones.revocar(s)
        registrar(db, "auth.2fa_fallido", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
        db.commit()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "El código no es válido o ya venció. Revisa la hora de tu teléfono."
        )
    primera_vez = not u.totp_confirmado
    u.totp_confirmado, u.failed_attempts, u.last_login_at = True, 0, datetime.now(UTC)
    sesiones.revocar(s)  # se reemplaza la sesión parcial por una completa
    token = sesiones.crear(db, u, mfa_ok=True, ip=ctx.ip, ua=ctx.user_agent)
    if primera_vez:
        registrar(db, "auth.2fa_activada", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent)
    registrar(db, "auth.login", user_id=u.id, ip=ctx.ip, user_agent=ctx.user_agent, details={"2fa": True})
    db.commit()
    _poner_cookie(resp, token)
    return RespuestaIngreso(paso="listo", mensaje="Ingresaste.")


@router.post("/logout", status_code=204)
def logout(
    resp: Response,
    s: Sesion = Depends(sesion_actual),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    sesiones.revocar(s)
    registrar(db, "auth.logout", user_id=s.user_id, ip=ctx.ip, user_agent=ctx.user_agent)
    db.commit()
    resp.delete_cookie(settings().cookie_nombre, path="/")


@router.get("/me", response_model=Yo)
def yo(s: Sesion = Depends(sesion_completa)):
    u = s.user
    return Yo(id=str(u.id), email=u.email, name=u.name, roles=u.role_keys, requiere_2fa=u.requiere_2fa)
