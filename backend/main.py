from __future__ import annotations

from fastapi import FastAPI

from backend.api.intelligence import router as intelligence_router


app = FastAPI(title="CrisisRelay Intelligence Service")
app.include_router(intelligence_router)
