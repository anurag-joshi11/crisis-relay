from __future__ import annotations

from pathlib import Path

from backend.config import GENERATED_AUDIO_DIR


def synthesize_approved_text(dispatch_id: str, approved_text: str) -> str:
    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_AUDIO_DIR / f"{dispatch_id}.mp3"
    output.write_bytes(b"")
    return f"/audio/{output.name}"

