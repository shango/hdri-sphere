"""FastAPI app entrypoint.

Production layout: FastAPI handles ``/api/*`` and serves the React build
output (``frontend/dist/``) at ``/``. Development layout: Vite runs on
:5173 with a proxy for ``/api/*``; FastAPI runs separately on :8000 and
permits CORS from the dev origin.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.inpaint import INPAINTERS

from app.routes.download import router as download_router
from app.routes.preview import router as preview_router
from app.routes.process import router as process_router
from app.routes.upload import router as upload_router
from app.schemas import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="HDRI Tool",
        version="0.1.0",
        description="Chrome ball EXR -> equirectangular HDRI conversion.",
    )

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level)

    # CORS: in dev, Vite serves the SPA on :5173 and proxies /api/* to us.
    # The proxy means same-origin in the browser, but we also accept direct
    # cross-origin requests during local debugging.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers — all under /api.
    app.include_router(upload_router, prefix="/api")
    app.include_router(preview_router, prefix="/api")
    app.include_router(process_router, prefix="/api")
    app.include_router(download_router, prefix="/api")

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", inpainters=sorted(INPAINTERS))

    # Mount built React app last so /api takes precedence.
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend",
        "dist",
    )
    if os.path.isdir(frontend_dist):
        app.mount(
            "/",
            StaticFiles(directory=frontend_dist, html=True),
            name="frontend",
        )
    else:
        @app.get("/")
        def root() -> dict:
            return {
                "message": (
                    "Frontend not built. Run 'cd frontend && npm run dev' for "
                    "development, or 'npm run build' to generate dist/."
                )
            }

    return app


app = create_app()
