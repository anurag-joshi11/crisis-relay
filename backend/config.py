from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT_DIR / "contracts"
GENERATED_AUDIO_DIR = ROOT_DIR / "backend" / "generated_audio"


@dataclass(frozen=True)
class Settings:
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    solana_private_key: str = os.getenv("SOLANA_PRIVATE_KEY", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
