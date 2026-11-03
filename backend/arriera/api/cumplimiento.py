"""Panel de cumplimiento de la Ley 29733 (adenda 02): quién vio datos sensibles (N3), cuándo y desde dónde.
Para el Oficial de Datos Personales (rol auditor) y administración. Se exporta en CSV."""

import csv
import io
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from arriera.api.deps import Contexto, contexto, requiere_roles
from arriera.audit.cadena import registrar
from arriera.db import get_db
from arriera.models import User

router = APIRouter(prefix="/cumplimiento", tags=["cumplimiento"])

SQL = text(
    """
    WITH accesos AS (
      SELECT e.id, e.ts, e.user_id, e.action, e.ip::text AS ip, d.id AS doc_id
        FROM audit_events e JOIN documents d ON d.id::text = e.object_id
       WHERE e.action = 'documento.visto' AND e.ts >= :desde AND d.sensitivity = 'N3'
      UNION ALL
      SELECT e.id, e.ts, e.user_id, e.action, e.ip::text, d.id
        FROM audit_events e
        JOIN document_pages dp ON dp.batch_page_id::text = e.object_id
        JOIN documents d ON d.id = dp.document_id
       WHERE e.action = 'pagina.vista' AND e.ts >= :desde AND d.sensitivity = 'N3'
    )
    SELECT a.ts, u.name, u.email, a.action, a.ip, t.name AS tipo, b.code AS lote, a.doc_id
      FROM accesos a
      LEFT JOIN users u ON u.id = a.user_id
      JOIN documents d ON d.id = a.doc_id
      JOIN document_types t ON t.id = d.document_type_id
      JOIN batches b ON b.id = d.batch_id
     ORDER BY a.ts DESC
     LIMIT 2000
    """
)
ACCION = {"documento.visto": "Abrió el documento", "pagina.vista": "Vio una página"}


@router.get("/accesos-sensibles")
def accesos(
    dias: int = Query(30, ge=1, le=365),
    formato: str = Query("json", pattern="^(json|csv)$"),
    u: User = Depends(requiere_roles("admin", "auditor")),
    db: Session = Depends(get_db),
    ctx: Contexto = Depends(contexto),
):
    desde = datetime.now(UTC) - timedelta(days=dias)
    filas = db.execute(SQL, {"desde": desde}).mappings().all()
    registrar(
        db,
        "cumplimiento.accesos_consultados",
        user_id=u.id,
        object_type="report",
        object_id="accesos-sensibles",
        ip=ctx.ip,
        details={"dias": dias, "formato": formato, "filas": len(filas)},
    )
    db.commit()
    datos = [
        {
            "fecha": f["ts"].isoformat(timespec="seconds"),
            "usuario": f["name"] or "—",
            "correo": f["email"] or "—",
            "accion": ACCION.get(f["action"], f["action"]),
            "documento": f["tipo"],
            "lote": f["lote"],
            "documento_id": str(f["doc_id"]),
            "ip": f["ip"] or "—",
        }
        for f in filas
    ]
    if formato == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(datos[0]) if datos else ["fecha"])
        w.writeheader()
        w.writerows(datos)
        return Response(
            "﻿" + buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="accesos-sensibles-{dias}d.csv"'},
        )
    por_usuario: dict[str, int] = {}
    for d in datos:
        por_usuario[d["usuario"]] = por_usuario.get(d["usuario"], 0) + 1
    return {
        "dias": dias,
        "total": len(datos),
        "por_usuario": sorted(
            ({"usuario": k, "accesos": v} for k, v in por_usuario.items()), key=lambda x: -x["accesos"]
        ),
        "accesos": datos[:300],
    }
