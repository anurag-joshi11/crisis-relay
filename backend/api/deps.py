import os

from fastapi import HTTPException

from backend.demo.scenario_runner import ScenarioRunner
from backend.services.mongodb_service import InMemoryMongoService

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

runner: ScenarioRunner | None = None


def get_runner() -> ScenarioRunner:
    global runner
    if runner:
        return runner
    if os.getenv("CRISIS_RELAY_USE_MEMORY") == "true":
        runner = ScenarioRunner(store=InMemoryMongoService())
        runner.reset()
        return runner
    if not os.getenv("MONGODB_URI"):
        raise HTTPException(
            status_code=503,
            detail="MONGODB_URI is required for the MongoDB-backed core engine.",
        )
    runner = ScenarioRunner()
    return runner
