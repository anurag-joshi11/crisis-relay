from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.gemini_schema import (
    DraftStatusRequest,
    DraftStatusResponse,
    ExtractRequest,
    ExtractionResult,
)
from backend.services.gemini_service import (
    GeminiIntelligenceService,
    GeminiResponseValidationError,
    GeminiServiceError,
    MissingGeminiCredentialsError,
)


router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def get_gemini_service() -> GeminiIntelligenceService:
    return GeminiIntelligenceService()


@router.post("/extract", response_model=ExtractionResult)
def extract_report(
    request: ExtractRequest,
    service: GeminiIntelligenceService = Depends(get_gemini_service),
) -> ExtractionResult:
    try:
        return service.extract_report(request)
    except MissingGeminiCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GeminiResponseValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini response failed contract validation: {exc}",
        ) from exc
    except GeminiServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/draft-status", response_model=DraftStatusResponse)
def draft_status(
    request: DraftStatusRequest,
    service: GeminiIntelligenceService = Depends(get_gemini_service),
) -> DraftStatusResponse:
    try:
        return service.draft_status(request)
    except GeminiResponseValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini response failed contract validation: {exc}",
        ) from exc
    except GeminiServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
