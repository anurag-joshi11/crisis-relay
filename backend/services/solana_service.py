from __future__ import annotations

import hashlib
import json

try:
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts
    from solders.instruction import Instruction
    from solders.keypair import Keypair
    from solders.message import MessageV0
    from solders.pubkey import Pubkey
    from solders.transaction import VersionedTransaction
except ImportError:
    Client = None
    TxOpts = None
    Instruction = None
    Keypair = None
    MessageV0 = None
    Pubkey = None
    VersionedTransaction = None

from backend.config import settings

MEMO_PROGRAM_ID = (
    Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
    if Pubkey is not None
    else None
)


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


def submit_receipt(payload_json: str) -> tuple[str | None, str, str | None]:
    if not settings.solana_enabled:
        return None, "DISABLED", None
    if Client is None or TxOpts is None or Instruction is None or Keypair is None or MessageV0 is None or VersionedTransaction is None or MEMO_PROGRAM_ID is None:
        return None, "MISSING_DEPENDENCY", "Solana packages are not installed"
    if not settings.solana_private_key:
        return None, "MISSING_CONFIG", "SOLANA_PRIVATE_KEY is not set"

    try:
        secret = json.loads(settings.solana_private_key)
        payer = Keypair.from_bytes(bytes(secret))
        client = Client(settings.solana_rpc_url)
        latest_blockhash = client.get_latest_blockhash().value.blockhash
        instruction = Instruction(MEMO_PROGRAM_ID, payload_json.encode("utf-8"), [])
        message = MessageV0.try_compile(
            payer.pubkey(),
            [instruction],
            [],
            latest_blockhash,
        )
        transaction = VersionedTransaction(message, [payer])
        response = client.send_transaction(
            transaction,
            opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed"),
        )
        return str(response.value), "CONFIRMED", None
    except Exception as exc:
        return None, "FAILED", str(exc)
