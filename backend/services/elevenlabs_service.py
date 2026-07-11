from __future__ import annotations

from backend.config import GENERATED_AUDIO_DIR, settings


def synthesize_approved_text(dispatch_id: str, approved_text: str) -> str | None:
    if not settings.elevenlabs_enabled:
        return None
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        return None

    # Real ElevenLabs synthesis is intentionally deferred to Pass 3.
    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_AUDIO_DIR / f"{dispatch_id}.mp3"
    output.write_bytes(b"")
    return f"/audio/{output.name}"
