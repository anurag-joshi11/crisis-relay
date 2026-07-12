from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import GENERATED_AUDIO_DIR, settings


def create_app() -> FastAPI:
    app = FastAPI(title="CrisisRelay")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(GENERATED_AUDIO_DIR)), name="audio")

    from backend.api.dispatches import router as dispatches_router

    app.include_router(dispatches_router, prefix="/api")
    return app


app = create_app()
