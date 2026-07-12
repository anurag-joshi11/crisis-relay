from fastapi import APIRouter, Depends

from backend.api.deps import get_runner

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
def create_report(report: dict, runner=Depends(get_runner)):
    return runner.ingestion.ingest_report(report)
