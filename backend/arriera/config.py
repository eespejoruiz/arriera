from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración por variables de entorno. Nada de secretos en el código."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_timezone: str = "America/Lima"
    database_url: str = "postgresql+psycopg://arriera:arriera@localhost:5432/arriera"
    # Clave AES-256-GCM en base64 (32 bytes) para TOTP, DNI y otros datos cifrados.
    cifrado_key: str = Field(default="", description="base64 de 32 bytes")
    # Clave HMAC en base64 para buscar DNI por hash sin guardarlo en claro.
    dni_hmac_key: str = Field(default="", description="base64")
    cookie_nombre: str = "arriera_sesion"
    cookie_segura: bool = True
    sesion_inactividad_min: int = 30
    sesion_max_horas: int = 12
    mfa_pendiente_min: int = 10
    max_intentos: int = 5
    bloqueo_min: int = 15
    cors_origins: list[str] = ["http://localhost:3000"]
    totp_emisor: str = "Arriera"
    # Almacenamiento: "s3" (MinIO/S3) o "local" (desarrollo y pruebas)
    almacen: str = "local"
    almacen_local_dir: str = "./.almacen"
    s3_endpoint: str = "localhost:9000"
    s3_seguro: bool = False
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "arriera"
    # Captura
    url_publica: str = "http://localhost:3000"
    emparejamiento_min: int = 10
    max_imagen_mb: int = 25
    institucion: str = "FAMENSSALUD (DEMO)"
    # OCR: "tesseract" (local, DATOS DEMO y modo local), "azure" (prebuilt-read con la cuenta del cliente) o "ninguno"
    ocr_proveedor: str = "tesseract"
    ocr_idiomas: str = "spa+eng+por"  # paquetes de Tesseract; Azure detecta el idioma solo
    azure_di_endpoint: str = ""
    azure_di_key: str = ""
    azure_di_version: str = "2024-11-30"
    azure_di_usd_mil: float = 1.5  # referencia del spec; verificar el precio vigente
    ocr_confianza_minima: float = 0.35  # debajo de esto, la página se marca ilegible


@lru_cache
def settings() -> Settings:
    return Settings()
