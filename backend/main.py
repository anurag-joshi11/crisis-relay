from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import GENERATED_AUDIO_DIR, settings
from backend.api import blindspots, demo, operations, reports
from backend.api.dispatches import router as dispatches_router
from backend.api.intelligence import router as intelligence_router


def create_app() -> FastAPI:
    app = FastAPI(title="CrisisRelay Backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(GENERATED_AUDIO_DIR)), name="audio")

    app.include_router(dispatches_router, prefix="/api")
    app.include_router(reports.router)
    app.include_router(operations.router)
    app.include_router(blindspots.router)
    app.include_router(demo.router)
    app.include_router(intelligence_router)
    return app


app = create_app()
