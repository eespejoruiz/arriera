"""Almacenamiento de archivos: MinIO/S3 en servidores, carpeta local en desarrollo y pruebas.

Las URLs de archivos nunca se exponen directo: la API valida permisos y sirve el contenido.
"""

import io
from pathlib import Path
from typing import Protocol

from arriera.config import settings


class Almacen(Protocol):
    def guardar(self, clave: str, datos: bytes, tipo: str) -> None: ...
    def leer(self, clave: str) -> bytes: ...


class AlmacenLocal:
    def __init__(self, raiz: str):
        self.raiz = Path(raiz).resolve()

    def _ruta(self, clave: str) -> Path:
        p = (self.raiz / clave).resolve()
        if self.raiz not in p.parents:
            raise ValueError("Clave de almacenamiento inválida.")
        return p

    def guardar(self, clave: str, datos: bytes, tipo: str) -> None:
        p = self._ruta(clave)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(datos)

    def leer(self, clave: str) -> bytes:
        return self._ruta(clave).read_bytes()


class AlmacenS3:
    def __init__(self):
        from minio import Minio

        c = settings()
        self.bucket = c.s3_bucket
        self.cli = Minio(c.s3_endpoint, access_key=c.s3_access_key, secret_key=c.s3_secret_key, secure=c.s3_seguro)

    def guardar(self, clave: str, datos: bytes, tipo: str) -> None:
        self.cli.put_object(self.bucket, clave, io.BytesIO(datos), len(datos), content_type=tipo)

    def leer(self, clave: str) -> bytes:
        r = self.cli.get_object(self.bucket, clave)
        try:
            return r.read()
        finally:
            r.close()
            r.release_conn()


_almacen: Almacen | None = None


def almacen() -> Almacen:
    global _almacen
    if _almacen is None:
        c = settings()
        _almacen = AlmacenS3() if c.almacen == "s3" else AlmacenLocal(c.almacen_local_dir)
    return _almacen


def reiniciar() -> None:
    global _almacen
    _almacen = None
