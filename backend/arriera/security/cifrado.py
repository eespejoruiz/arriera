import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from arriera.config import settings


class ClaveNoConfigurada(RuntimeError):
    pass


def _clave(nombre: str, valor: str) -> bytes:
    if not valor:
        raise ClaveNoConfigurada(f"Falta configurar {nombre} en el entorno.")
    return base64.b64decode(valor)


def cifrar(texto: str, contexto: str) -> str:
    """AES-256-GCM. `contexto` se usa como datos asociados (p. ej. 'totp:<user_id>')."""
    clave = _clave("CIFRADO_KEY", settings().cifrado_key)
    nonce = os.urandom(12)
    ct = AESGCM(clave).encrypt(nonce, texto.encode(), contexto.encode())
    return "v1:" + base64.b64encode(nonce + ct).decode()


def descifrar(token: str, contexto: str) -> str:
    clave = _clave("CIFRADO_KEY", settings().cifrado_key)
    crudo = base64.b64decode(token.removeprefix("v1:"))
    return AESGCM(clave).decrypt(crudo[:12], crudo[12:], contexto.encode()).decode()


def hmac_busqueda(valor: str) -> str:
    """Huella HMAC-SHA256 para buscar un identificador (DNI) sin guardarlo en claro."""
    clave = _clave("DNI_HMAC_KEY", settings().dni_hmac_key)
    return hmac.new(clave, valor.strip().encode(), hashlib.sha256).hexdigest()
