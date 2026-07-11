from __future__ import annotations

import hashlib
import json


def build_payload(dispatch_id: str, operation_id: str, resource_id: str, approval_id: str) -> tuple[str, str]:
    payload = {
        "version": "CRISISRELAY_V1",
        "dispatch_id": dispatch_id,
        "operation_id": operation_id,
        "resource_id": resource_id,
        "state": "STATUS_VERIFICATION_REQUESTED",
        "approval_id": approval_id,
    }
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return payload_json, hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

