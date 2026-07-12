from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.config import GENERATED_AUDIO_DIR, settings


def synthesize_approved_text(dispatch_id: str, approved_text: str) -> tuple[str | None, str, str | None]:
    if not settings.elevenlabs_enabled:
        return None, "DISABLED", None
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        return None, "MISSING_CONFIG", None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
    body = {
        "text": approved_text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {
            "stability": 0.72,
            "similarity_boost": 0.72,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "xi-api-key": settings.elevenlabs_api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            audio_bytes = response.read()
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")[:300]
        return None, "FAILED", f"elevenlabs_http_{exc.code}:{error_body}"
    except (URLError, TimeoutError, OSError) as exc:
        return None, "FAILED", f"{type(exc).__name__}:{exc}"

    if not audio_bytes:
        return None, "FAILED", "empty_audio_response"

    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_AUDIO_DIR / f"{dispatch_id}.mp3"
    output.write_bytes(audio_bytes)
    return f"/audio/{output.name}", "AVAILABLE", None
