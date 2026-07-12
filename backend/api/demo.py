from fastapi import APIRouter, Depends

from backend.api.deps import get_runner

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/reset")
def reset_demo(runner=Depends(get_runner)):
    return runner.reset()


@router.post("/next-event")
def next_event(runner=Depends(get_runner)):
    return runner.next_event()


@router.get("/status")
def demo_status(runner=Depends(get_runner)):
    return runner.status()
