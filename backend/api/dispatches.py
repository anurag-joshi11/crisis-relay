from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.api.deps import get_runner
from backend.config import CONTRACTS_DIR
from backend.services.elevenlabs_service import synthesize_approved_text
from backend.services.solana_service import build_payload, submit_receipt
from backend.utils import load_json, utc_now

router = APIRouter()

_dispatches = {"DSP-001": load_json(CONTRACTS_DIR / "dispatch_result.json")}
_dispatch_counter = 1


def _dispatch_for(dispatch_id: str) -> dict:
    dispatch = _dispatches.get(dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="dispatch_not_found")
    return dispatch


def _blindspot_for(runner, blindspot_id: str) -> dict:
    blindspot = runner.store.get_blindspot(blindspot_id)
    if not blindspot:
        raise HTTPException(status_code=404, detail="blindspot_not_found")
    return blindspot


def _operation_for(runner, operation_id: str) -> dict:
    operation = runner.store.get_operation(operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="operation_not_found")
    return operation


@router.post("/blindspots/{blindspot_id}/draft-status-request")
def draft_status_request(blindspot_id: str, runner=Depends(get_runner)) -> dict:
    global _dispatch_counter
    blindspot = _blindspot_for(runner, blindspot_id)

    existing = next((item for item in _dispatches.values() if item["blindspot_id"] == blindspot_id), None)
    if existing and existing["approval_status"] == "PENDING":
        return existing

    dispatch = deepcopy(_dispatches["DSP-001"])
    if existing:
        _dispatch_counter += 1
        dispatch["dispatch_id"] = f"DSP-{_dispatch_counter:03d}"
        dispatch["approval_id"] = None
        dispatch["approved_text"] = None
        dispatch["approved_at"] = None
        dispatch["payload_hash"] = None
        dispatch["solana_status"] = "NOT_SUBMITTED"
        dispatch["solana_signature"] = None
        dispatch["solana_error"] = None
        dispatch["audio_url"] = None
        dispatch["audio_status"] = "NOT_GENERATED"
        dispatch["audio_error"] = None
        dispatch["audio_preview_text"] = None
    dispatch["blindspot_id"] = blindspot_id
    dispatch["operation_id"] = blindspot["operation_id"]
    dispatch["approval_status"] = "PENDING"
    _dispatches[dispatch["dispatch_id"]] = dispatch
    return dispatch


@router.post("/dispatches/{dispatch_id}/preview-audio")
def preview_audio(dispatch_id: str, payload: dict | None = Body(default=None)) -> dict:
    dispatch = _dispatch_for(dispatch_id)
    if dispatch["approval_status"] == "APPROVED":
        return dispatch
    if dispatch["approval_status"] == "REJECTED":
        raise HTTPException(status_code=409, detail="dispatch_already_rejected")

    payload = payload or {}
    preview_text = (payload.get("approved_text") or dispatch.get("ai_draft") or "").strip()
    if not preview_text:
        raise HTTPException(status_code=400, detail="preview_text_required")

    if dispatch.get("audio_url") and dispatch.get("audio_preview_text") == preview_text:
        dispatch["audio_status"] = dispatch.get("audio_status") or "AVAILABLE"
        _dispatches[dispatch_id] = dispatch
        return dispatch

    dispatch["approved_text"] = preview_text
    dispatch["audio_status"] = "PENDING"
    dispatch["audio_error"] = None
    dispatch["audio_url"] = None
    dispatch["audio_preview_text"] = preview_text

    audio_url, audio_status, audio_error = synthesize_approved_text(dispatch["dispatch_id"], preview_text)
    dispatch["audio_status"] = audio_status
    dispatch["audio_error"] = audio_error
    if audio_url:
        dispatch["audio_url"] = audio_url

    _dispatches[dispatch_id] = dispatch
    return dispatch


@router.post("/dispatches/{dispatch_id}/approve")
def approve(dispatch_id: str, payload: dict | None = Body(default=None), runner=Depends(get_runner)) -> dict:
    dispatch = _dispatch_for(dispatch_id)

    payload = payload or {}
    approved_text = (payload.get("approved_text") or dispatch.get("ai_draft") or "").strip()
    if not approved_text:
        raise HTTPException(status_code=400, detail="approved_text_required")
    if dispatch["approval_status"] == "REJECTED":
        raise HTTPException(status_code=409, detail="dispatch_already_rejected")
    if dispatch["approval_status"] == "APPROVED":
        return dispatch
    if not dispatch.get("audio_url") or dispatch.get("audio_preview_text") != approved_text:
        raise HTTPException(status_code=409, detail="audio_preview_required_before_approval")
    if dispatch.get("audio_status") != "AVAILABLE":
        raise HTTPException(status_code=409, detail=f"audio_not_ready:{dispatch.get('audio_status')}")

    operation = _operation_for(runner, dispatch["operation_id"])
    approval_id = dispatch.get("approval_id") or f"APR-{dispatch['dispatch_id'].split('-')[-1]}"
    payload_json, payload_hash = build_payload(
        dispatch_id=dispatch["dispatch_id"],
        operation_id=dispatch["operation_id"],
        resource_id=operation["resource_id"],
        approval_id=approval_id,
    )

    dispatch.update(
        {
            "approved_text": approved_text,
            "approval_status": "APPROVED",
            "approval_id": approval_id,
            "approved_at": utc_now().isoformat(),
            "payload_hash": payload_hash,
            "solana_status": "PENDING_SYNC",
            "solana_signature": None,
            "solana_error": None,
        }
    )

    solana_signature, solana_status, solana_error = submit_receipt(payload_json)
    dispatch["solana_status"] = solana_status
    dispatch["solana_error"] = solana_error
    if solana_signature:
        dispatch["solana_signature"] = solana_signature

    _dispatches[dispatch_id] = dispatch
    return dispatch


@router.post("/dispatches/{dispatch_id}/reject")
def reject(dispatch_id: str) -> dict:
    dispatch = _dispatch_for(dispatch_id)
    if dispatch["approval_status"] == "APPROVED":
        raise HTTPException(status_code=409, detail="dispatch_already_approved")
    dispatch["approval_status"] = "REJECTED"
    _dispatches[dispatch_id] = dispatch
    return dispatch
