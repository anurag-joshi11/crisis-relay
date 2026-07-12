from __future__ import annotations

from fastapi import FastAPI

from backend.api import blindspots, demo, operations, reports
from backend.api.intelligence import router as intelligence_router


app = FastAPI(title="CrisisRelay Backend")
app.include_router(reports.router)
app.include_router(operations.router)
app.include_router(blindspots.router)
app.include_router(demo.router)
app.include_router(intelligence_router)
