from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, HTTPException

from backend.config import CONTRACTS_DIR
from backend.services.elevenlabs_service import synthesize_approved_text
from backend.services.solana_service import build_payload
from backend.utils import load_json, utc_now

router = APIRouter()

_dashboard = load_json(CONTRACTS_DIR / "dashboard_snapshot.json")
_dispatches = {"DSP-001": load_json(CONTRACTS_DIR / "dispatch_result.json")}


def _dispatch_for(dispatch_id: str) -> dict:
    dispatch = _dispatches.get(dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="dispatch_not_found")
    return dispatch


def _operation_for(operation_id: str) -> dict:
    for operation in _dashboard["operations"]:
        if operation["operation_id"] == operation_id:
            return operation
    raise HTTPException(status_code=404, detail="operation_not_found")


@router.post("/blindspots/{blindspot_id}/draft-status-request")
def draft_status_request(blindspot_id: str) -> dict:
    blindspot = next((item for item in _dashboard["blindspots"] if item["blindspot_id"] == blindspot_id), None)
    if not blindspot:
        raise HTTPException(status_code=404, detail="blindspot_not_found")

    existing = next((item for item in _dispatches.values() if item["blindspot_id"] == blindspot_id), None)
    if existing and existing["approval_status"] != "PENDING":
        return existing

    dispatch = deepcopy(_dispatches["DSP-001"])
    dispatch["blindspot_id"] = blindspot_id
    dispatch["operation_id"] = blindspot["operation_id"]
    dispatch["approval_status"] = "PENDING"
    _dispatches[dispatch["dispatch_id"]] = dispatch
    return dispatch


@router.post("/dispatches/{dispatch_id}/approve")
def approve(dispatch_id: str, payload: dict) -> dict:
    dispatch = _dispatch_for(dispatch_id)

    approved_text = (payload.get("approved_text") or "").strip()
    if not approved_text:
        raise HTTPException(status_code=400, detail="approved_text_required")
    if dispatch["approval_status"] == "REJECTED":
        raise HTTPException(status_code=409, detail="dispatch_already_rejected")
    if dispatch["approval_status"] == "APPROVED":
        return dispatch

    operation = _operation_for(dispatch["operation_id"])
    approval_id = dispatch.get("approval_id") or f"APR-{dispatch['dispatch_id'].split('-')[-1]}"
    _, payload_hash = build_payload(
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
            "audio_url": None,
        }
    )

    audio_url = synthesize_approved_text(dispatch["dispatch_id"], approved_text)
    if audio_url:
        dispatch["audio_url"] = audio_url

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
