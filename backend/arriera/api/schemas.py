from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Ingreso(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class RespuestaIngreso(BaseModel):
    paso: str  # "listo" | "verificar_2fa" | "configurar_2fa"
    mensaje: str


class Codigo(BaseModel):
    codigo: str = Field(min_length=6, max_length=8)


class Configuracion2FA(BaseModel):
    uri: str
    secreto: str
    qr_svg: str  # SVG del código QR, para mostrar como imagen


class Yo(BaseModel):
    id: str
    email: str
    name: str
    roles: list[str]
    requiere_2fa: bool


class NuevoUsuario(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=256)
    roles: list[str] = Field(min_length=1)


class UsuarioOut(BaseModel):
    id: str
    email: str
    name: str
    roles: list[str]
    is_active: bool
    totp_confirmado: bool


class EventoOut(BaseModel):
    id: int
    ts: datetime
    actor_type: str
    user_id: str | None
    action: str
    object_type: str | None
    object_id: str | None
    ip: str | None
    details: dict
    hash: str


class VerificacionOut(BaseModel):
    integra: bool
    eventos: int
    ultimo_hash: str
    primer_error_id: int | None = None
    motivo: str | None = None
