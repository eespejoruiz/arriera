import io

import pyotp
import segno

from arriera.config import settings


def nuevo_secreto() -> str:
    return pyotp.random_base32()


def uri_aprovisionamiento(secreto: str, email: str) -> str:
    return pyotp.TOTP(secreto).provisioning_uri(name=email, issuer_name=settings().totp_emisor)


def verificar_codigo(secreto: str, codigo: str) -> bool:
    codigo = (codigo or "").strip().replace(" ", "")
    if not (codigo.isdigit() and len(codigo) == 6):
        return False
    return pyotp.TOTP(secreto).verify(codigo, valid_window=1)


def qr_svg(uri: str) -> str:
    """SVG del QR de aprovisionamiento, con los colores de Arriera."""
    buf = io.BytesIO()
    segno.make(uri, error="m").save(
        buf, kind="svg", scale=6, border=2, dark="#14160F", light="#F4F5EE", xmldecl=False
    )
    return buf.getvalue().decode()
