from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from arriera import __version__
from arriera.api import auditoria, auth, busqueda, cajas, captura, estacion, usuarios
from arriera.config import settings
from arriera.db import SessionLocal


def crear_app() -> FastAPI:
    cfg = settings()
    app = FastAPI(
        title="Arriera API",
        version=__version__,
        docs_url="/docs" if cfg.app_env != "production" else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Station-Key"],
    )

    @app.middleware("http")
    async def cabeceras_seguras(request, call_next):
        r = await call_next(request)
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["X-Frame-Options"] = "DENY"
        r.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        r.headers["Cache-Control"] = "no-store"
        return r

    @app.get("/health", tags=["sistema"])
    def salud():
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"estado": "ok"}

    @app.get("/version", tags=["sistema"])
    def version():
        return {"version": __version__, "producto": "Arriera"}

    app.include_router(auth.router)
    app.include_router(usuarios.router)
    app.include_router(auditoria.router)
    app.include_router(cajas.router)
    app.include_router(captura.router)
    app.include_router(estacion.router)
    app.include_router(busqueda.router)
    return app


app = crear_app()
