from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_runner

router = APIRouter(prefix="/api/blindspots", tags=["blindspots"])


@router.get("")
def list_blindspots(status: str | None = None, runner=Depends(get_runner)):
    return runner.store.list_blindspots(status)


@router.get("/{blindspot_id}")
def get_blindspot(blindspot_id: str, runner=Depends(get_runner)):
    blindspot = runner.store.get_blindspot(blindspot_id)
    if not blindspot:
        raise HTTPException(status_code=404, detail="blindspot not found")
    return blindspot
