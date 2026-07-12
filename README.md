# crisis-relay

Student 2 core-engine implementation for CrisisRelay.

## Backend

The FastAPI app lives in `backend/` and persists production state to MongoDB through PyMongo.

Required runtime environment:

```powershell
$env:MONGODB_URI = "mongodb+srv://..."
$env:MONGODB_DATABASE = "crisis_relay"
```

Run locally:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

For isolated demo/testing without MongoDB, set:

```powershell
$env:CRISIS_RELAY_USE_MEMORY = "true"
```

The ground-truth extraction provider is only for tests/demo development while the Student 1 Gemini provider is unavailable. Dashboard responses do not expose ground truth.
