from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_runner

router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("")
def list_operations(runner=Depends(get_runner)):
    return runner.store.list_operations()


@router.get("/{operation_id}")
def get_operation(operation_id: str, runner=Depends(get_runner)):
    operation = runner.store.get_operation(operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="operation not found")
    return operation


@router.get("/{operation_id}/timeline")
def get_timeline(operation_id: str, runner=Depends(get_runner)):
    timeline = runner.timeline_for_operation(operation_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="operation not found")
    return timeline
