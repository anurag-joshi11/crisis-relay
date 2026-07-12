# CrisisRelay

CrisisRelay is a crisis-operations prototype that turns fragmented field reports into a live operational picture, flags unverified mission states, and routes high-risk decisions through a human approval workflow before any outbound command message is sent.

The project combines:

- a FastAPI backend for ingestion, extraction, state tracking, and dispatch orchestration
- a React command-center UI for reviewing issues and approving updates
- Gemini-powered structured extraction for uncertain field communications
- ElevenLabs voice preview for approved outbound status requests
- optional Solana receipt submission for compact approval logging

## What The System Does

At a high level, CrisisRelay models a live incident as operations moving through states such as:

- `REQUESTED`
- `ACKNOWLEDGED`
- `ASSIGNED`
- `DISPATCHED`
- `ARRIVED`
- `HOLDING`
- `COMPLETED`
- `VERIFIED`

Incoming reports are processed into structured extraction output. The backend then:

1. updates operation state only when the report provides explicit evidence
2. preserves uncertainty as assumptions or unresolved claims instead of forcing unsafe transitions
3. detects overdue or unverified operations as active issues / blindspots
4. lets a human operator review the issue in the command-center UI
5. generates a draft status-check request
6. optionally generates a voice preview with ElevenLabs
7. requires human approval before final dispatch confirmation

## Core Features

### 1. Structured Intelligence Extraction

The `/api/intelligence/extract` endpoint uses Gemini to convert raw report text into a strict `ExtractionResult` schema with:

- `state_events`
- `assumptions`
- `claims`
- `blockers`
- `related_operation`
- `need_still_active`

The extraction layer is intentionally conservative:

- no arrival or completion is inferred from elapsed time alone
- uncertain language does not advance state
- unlinked outcomes remain claims instead of becoming false confirmations
- strict Pydantic validation rejects malformed Gemini responses

### 2. Deterministic State Engine

The core engine tracks operations and resources, applies valid transitions, and opens blindspots when an operation remains unverified too long.

Examples:

- `BUS_7` can remain `DISPATCHED` even if evacuees reach shelter through private vehicles
- `TANKER_2` can move to `HOLDING` with a `VISIBILITY` blocker instead of incorrectly becoming `COMPLETED`
- repeated unmet need can keep an operation flagged as active without inventing a transition

### 3. Command Center UI

The React dashboard provides:

- live field report feed
- active issues sorted by severity
- tracked resources with confirmed latest state
- evidence timeline for the currently reviewed operation
- decision panel for request / reject / follow-up actions
- audit log / decision history

### 4. Human-Gated Outbound Updates

No audio preview or final approval should happen without explicit human review.

The workflow is:

1. select an active issue
2. request a status update draft
3. edit the message if needed
4. generate a voice preview
5. listen and approve only if it is correct

### 5. Optional Sponsor Integrations

- ElevenLabs: synthesizes approved text into an MP3 preview
- Solana: stores a compact approval payload hash / receipt status

If these integrations are disabled or misconfigured, the backend surfaces honest status values such as `DISABLED`, `MISSING_CONFIG`, or `FAILED`.

## Repository Structure

```text
crisis-relay/
├── backend/
│   ├── api/
│   ├── demo/
│   ├── schemas/
│   ├── services/
│   ├── tests/
│   ├── benchmark_extraction.py
│   ├── config.py
│   └── main.py
├── contracts/
│   ├── dashboard_snapshot.json
│   ├── dispatch_result.json
│   └── extraction_result.json
├── dataset/
│   ├── extraction_test_cases.json
│   ├── scenario_metadata.json
│   ├── state_engine_test_cases.json
│   ├── wildfire_scenario.csv
│   └── wildfire_scenario.json
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

## API Overview

### Demo / Scenario Routes

- `GET /api/demo/status`
- `POST /api/demo/reset`
- `POST /api/demo/next-event`

These drive the synthetic wildfire scenario and return:

- current scenario metadata
- latest visible report
- operations
- active blindspots
- selected evidence timeline
- demo progression state

### Core Data Routes

- `GET /api/reports`
- `GET /api/operations`
- `GET /api/operations/{operation_id}`
- `GET /api/operations/{operation_id}/timeline`
- `GET /api/blindspots`

### Intelligence Routes

- `POST /api/intelligence/extract`
- `POST /api/intelligence/draft-status`

### Dispatch / Approval Routes

- `POST /api/blindspots/{blindspot_id}/draft-status-request`
- `POST /api/dispatches/{dispatch_id}/preview-audio`
- `POST /api/dispatches/{dispatch_id}/approve`
- `POST /api/dispatches/{dispatch_id}/reject`

## Local Setup

### Backend

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run the backend:

```bash
./.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## Environment Configuration

Use `.env.example` as the starting template.

### Minimum backend demo configuration

```env
CRISIS_RELAY_USE_MEMORY=true
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### Gemini extraction

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

### ElevenLabs

```env
ELEVENLABS_ENABLED=true
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

### Solana

```env
SOLANA_ENABLED=false
SOLANA_RPC_URL=https://api.devnet.solana.com/
SOLANA_PRIVATE_KEY=
```

### Frontend

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_USE_MOCKS=false
VITE_REAL_APPROVALS=true
```

### Important environment notes

- do not put Markdown links inside `.env` values
- avoid trailing slashes in `VITE_API_URL` when possible
- if a variable is exported in your shell as an empty string, it can override `.env`
- restart `uvicorn` after changing environment configuration

## Running Without MongoDB

For the demo and hackathon review flow, the easiest option is the in-memory store:

```env
CRISIS_RELAY_USE_MEMORY=true
```

This avoids MongoDB entirely and uses the synthetic scenario dataset for the full UI flow.

## MongoDB Mode

For persistent storage, set:

```env
CRISIS_RELAY_USE_MEMORY=false
MONGODB_URI=mongodb://...
MONGODB_DATABASE=crisis_relay
```

## Dataset

The synthetic wildfire dataset lives in `dataset/` and includes:

- `wildfire_scenario.json`: 30 chronological field reports
- `wildfire_scenario.csv`: spreadsheet version of the same scenario
- `scenario_metadata.json`: resources, operations, and state machine
- `extraction_test_cases.json`: 60 extraction benchmark cases
- `state_engine_test_cases.json`: deterministic state engine fixtures

See [dataset/README.md](dataset/README.md) for the detailed dataset notes.

## Benchmarking Gemini Extraction

The repository includes a live benchmark runner:

```bash
python -m backend.benchmark_extraction
```

Useful options:

```bash
python -m backend.benchmark_extraction --limit 1
python -m backend.benchmark_extraction --case-id TC-021
python -m backend.benchmark_extraction --delay-seconds 5 --max-rate-limit-retries 3
python -m backend.benchmark_extraction --resume benchmark_results/<run-file>.json
```

The benchmark currently supports:

- persistent JSON output in `benchmark_results/`
- per-case pass/fail details
- rate-limit retry handling
- checkpoint / resume
- per-case API attempt counts

## Testing

Backend test modules include:

- `backend.tests.test_gemini`
- `backend.tests.test_benchmark_extraction`
- `backend.tests.test_scenario`
- `backend.tests.test_api`
- `backend.tests.test_demo_dashboard`
- `backend.tests.test_state_engine`

Common commands:

```bash
python -m unittest backend.tests.test_gemini
python -m unittest backend.tests.test_benchmark_extraction
python -m unittest discover backend/tests
python -m compileall backend
```

## Contracts

Shared JSON contracts live in `contracts/`:

- `extraction_result.json`
- `dashboard_snapshot.json`
- `dispatch_result.json`

These define the integration boundaries between extraction, backend orchestration, and UI rendering.

## Current UI Behavior

The command-center UI is designed around operational caution:

- active issues are sorted by severity
- tracked resources show only confirmed resource states
- evidence timelines update for the selected operation as new reports arrive
- approval state is tracked per issue, not globally
- voice preview is generated only from the current approved text
- duplicate global audio playback has been removed from the dashboard shell

## Known Operational Caveats

- if ElevenLabs is enabled but the API key or voice ID is missing, preview returns `MISSING_CONFIG`
- if Solana is disabled or not configured, approval still works but receipt status reflects the disabled state
- if `VITE_USE_MOCKS=true`, the frontend uses local mock responses instead of the live backend
- if CORS does not include the frontend origin, browser preflight requests will fail

## Deployment Notes

### Backend

- source directory: repository root
- install: `pip install -r backend/requirements.txt`
- run: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend

- source directory: `frontend`
- install/build: `npm install && npm run build`

### Deployment environment variables

At minimum configure:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `ELEVENLABS_ENABLED`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `ELEVENLABS_MODEL_ID`
- `SOLANA_ENABLED`
- `SOLANA_RPC_URL`
- `SOLANA_PRIVATE_KEY`
- `CORS_ORIGINS`
- `VITE_API_URL`

## Safety Note

This is a synthetic hackathon prototype for crisis-information triage and approval workflows. It is not production-certified emergency response software and should not be used as an operational life-safety decision authority without substantial hardening, validation, and human oversight.
