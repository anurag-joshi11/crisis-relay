# CrisisRelay

CrisisRelay combines the core-engine backend with the command-center UI and sponsor integrations.

## Overview

- Student 1 handles Gemini extraction and report generation.
- Student 2 handles the core-engine, state flow, and persistence.
- Student 3 handles the command-center UI, human approval flow, ElevenLabs audio, Solana receipt submission, and deployment notes.

## Backend

The FastAPI app lives in `backend/`.

It includes:

- report, operation, blindspot, demo, and intelligence routes
- command-center dispatch routes
- CORS handling
- `/audio` static hosting for generated MP3 files

### Runtime options

For the core engine:

```powershell
$env:MONGODB_URI = "mongodb+srv://..."
$env:MONGODB_DATABASE = "crisis_relay"
```

For the command center:

```powershell
$env:ELEVENLABS_API_KEY=
$env:ELEVENLABS_VOICE_ID=
$env:ELEVENLABS_MODEL_ID=eleven_multilingual_v2
$env:ELEVENLABS_ENABLED=false
$env:SOLANA_ENABLED=false
$env:SOLANA_RPC_URL=https://api.devnet.solana.com
$env:SOLANA_PRIVATE_KEY=
$env:CORS_ORIGINS=http://localhost:5173
```

For mock UI mode:

```powershell
$env:VITE_API_URL=http://localhost:8000
$env:VITE_USE_MOCKS=true
$env:VITE_REAL_APPROVALS=false
```

For isolated demo/testing without MongoDB:

```powershell
$env:CRISIS_RELAY_USE_MEMORY = "true"
```

## Local Commands

Backend:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Command Center Notes

- No ElevenLabs or Solana call should happen before human validation.
- Generate the voice preview first, then approve only after listening.
- ElevenLabs should synthesize only `approved_text`.
- Solana should store only compact identifiers and a SHA-256 hash.
- If Solana is disabled, missing credentials, or fails, surface the exact status without a fake signature.
- If ElevenLabs fails, keep the dispatch in preview mode and show the audio error.

## Deployment Notes

- Backend source directory: repository root
- Backend build command: `pip install -r requirements.txt`
- Backend run command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Frontend source directory: `frontend`
- Frontend build command: `npm install && npm run build`
- Set `VITE_API_URL` to the deployed backend URL.
- Store `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `SOLANA_RPC_URL`, and `SOLANA_PRIVATE_KEY` as encrypted environment variables.
- Set `CORS_ORIGINS` to the deployed frontend origin.
