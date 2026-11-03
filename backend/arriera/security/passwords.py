from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id con parámetros OWASP (m=19 MiB, t=2, p=1).
_ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
# Hash señuelo para que un correo inexistente tarde lo mismo que uno real.
_SENUELO = _ph.hash("arriera-senuelo-no-es-una-clave")


def hashear(clave: str) -> str:
    return _ph.hash(clave)


def verificar(hash_guardado: str | None, clave: str) -> bool:
    try:
        return _ph.verify(hash_guardado or _SENUELO, clave) and hash_guardado is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def clave_valida(clave: str) -> str | None:
    """Devuelve un mensaje si la clave no cumple la política; None si está bien."""
    if len(clave) < 12:
        return "La contraseña debe tener al menos 12 caracteres."
    if clave.lower() == clave or clave.upper() == clave or not any(c.isdigit() for c in clave):
        return "Usa mayúsculas, minúsculas y al menos un número."
    return None
