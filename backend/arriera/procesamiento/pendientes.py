"""Lee con OCR las páginas legibles que quedaron sin leer (por ejemplo, las capturadas antes del Sprint 2).

Uso:  python -m arriera.procesamiento.pendientes
"""

from sqlalchemy import select

from arriera.db import SessionLocal
from arriera.models import Pagina
from arriera.procesamiento.ocr import procesar_ocr


def main() -> None:
    with SessionLocal() as db:
        ids = db.scalars(
            select(Pagina.id).where(
                Pagina.qc_status.in_(["ok", "corregida"]), Pagina.ocr_status.in_(["pendiente", "error"])
            )
        ).all()
    hechas = 0
    for pid in ids:
        with SessionLocal() as db:
            p = procesar_ocr(db, pid)
            db.commit()
            hechas += p.ocr_status in ("ok", "sin_texto")
    print(f"Páginas pendientes: {len(ids)}. Leídas: {hechas}.")


if __name__ == "__main__":
    main()
