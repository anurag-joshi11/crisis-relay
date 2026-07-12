from fastapi import FastAPI

from backend.api import blindspots, demo, operations, reports

app = FastAPI(title="CrisisRelay Core Engine")
app.include_router(reports.router)
app.include_router(operations.router)
app.include_router(blindspots.router)
app.include_router(demo.router)
