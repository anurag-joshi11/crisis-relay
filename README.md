# CrisisRelay Command Center

Student 3 branch for the CrisisRelay command center and sponsor integrations. This branch owns the judge-visible dashboard, human approval workflow, ElevenLabs audio adapter, Solana devnet receipt adapter, and DigitalOcean deployment notes.

This branch intentionally builds against the frozen files in `contracts/` so Student 1 and Student 2 can continue independently. It does not implement Gemini extraction, MongoDB state persistence, report ingestion, or the deterministic state engine.

## Student 3 Scope

- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/index.css`
- `frontend/src/mocks/dashboard.json`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/components/*`
- `backend/api/dispatches.py`
- `backend/services/elevenlabs_service.py`
- `backend/services/solana_service.py`
- DigitalOcean deployment documentation

## Environment

Only these variables are needed for this branch:

```bash
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_ENABLED=false
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=
CORS_ORIGINS=http://localhost:5173
VITE_API_URL=http://localhost:8000
VITE_USE_MOCKS=true
```

Keep `VITE_USE_MOCKS=true` while developing independently. Set it to `false` only when integrating with Student 2's backend endpoints.

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

## Integration Notes

- No ElevenLabs or Solana call should happen before human approval.
- Keep `ELEVENLABS_ENABLED=false` until the approval flow is verified.
- ElevenLabs must synthesize only `approved_text`.
- Solana should store only compact identifiers and a SHA-256 hash, never raw reports or sensitive text.
- If Solana is missing credentials or the devnet wallet is unfunded, return `PENDING_SYNC` with no fake signature.
- If ElevenLabs fails, keep the dispatch approved and show audio unavailable.

## DigitalOcean

- Backend source directory: `backend`
- Backend build command: `pip install -r requirements.txt`
- Backend run command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Frontend source directory: `frontend`
- Frontend build command: `npm install && npm run build`
- Set `VITE_API_URL` to the deployed backend URL.
- Store `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `SOLANA_RPC_URL`, and `SOLANA_PRIVATE_KEY` as encrypted environment variables.
- Set `CORS_ORIGINS` to the deployed frontend origin.
