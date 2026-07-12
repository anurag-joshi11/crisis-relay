from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from backend.schemas.gemini_schema import (
    DraftStatusRequest,
    DraftStatusResponse,
    ExtractRequest,
    ExtractionResult,
    GeminiDraftPayload,
)


DEFAULT_GEMINI_MODEL = "gemini-flash-latest"


class GeminiServiceError(RuntimeError):
    """Base error for Gemini intelligence failures."""


class MissingGeminiCredentialsError(GeminiServiceError):
    """Raised when a live Gemini call is requested without credentials."""


class GeminiResponseValidationError(GeminiServiceError):
    """Raised when Gemini returns JSON that does not match our contract."""


class GeminiClientProtocol(Protocol):
    models: Any


EXTRACTION_INSTRUCTION = """
You are CrisisRelay's semantic incident intelligence boundary.

Convert one fragmented emergency field report into the exact ExtractionResult JSON shape.
Return JSON only. Do not add fields. Use null, false, or [] when information is absent.

Safety rules:
- Never infer ARRIVED from elapsed time, assignment, dispatch, expectation, or unrelated destination outcomes.
- Never infer COMPLETED from REQUESTED, ACKNOWLEDGED, ASSIGNED, or DISPATCHED.
- ARRIVED, COMPLETED, and VERIFIED require explicit evidence in the source text.
- Treat should, probably, likely, must have, I assume, and I think as assumptions.
- When uncertainty, speculation, hearsay, ambiguity, or missing confirmation prevents applying a specific operational transition, emit an assumption instead of a state_event.
- For that assumption, set entity_id to the affected entity when identifiable.
- Set blocked_transition to the canonical state that would otherwise have been applied; prefer names from scenario_context.state_machine when available.
- Do not leave blocked_transition null when the uncertain statement clearly references an identifiable transition such as ARRIVED, COMPLETED, VERIFIED, DISPATCHED, DEPLOYED, or HOLDING.
- Preserve the uncertain statement in assumption.text and explain why it cannot advance state in assumption.reason.
- Do not link outcomes to resources solely because the relationship is temporally plausible.
- Preserve unlinked outcomes as claims, not state transitions.
- Gemini interprets language only; it is not the final operational state authority.

State guidance:
- "assigned" -> ASSIGNED.
- "dispatched", "en route", "rolling out", "wheels-up" -> DISPATCHED.
- "arrived", "on scene", "pulled into" -> ARRIVED only when explicit.
- "holding", "staged and waiting", "paused" -> HOLDING.
- "delayed" -> DELAYED.
- "blocked", "unable to proceed", "cannot enter", "stopped" -> BLOCKED unless a clearer HOLDING or FAILED state applies.
- "turned back", "aborted", "lost propulsion", "cannot continue" -> FAILED.
- "complete", "finished", "connected" -> COMPLETED only when explicit.
- "verified", "confirms", "independently confirmed" -> VERIFIED only when explicit.
- If a reported entity is not found in scenario_context, still extract the event when the text itself identifies an operational entity.
- Canonicalize report-mentioned entities to stable UPPER_SNAKE_CASE IDs: "Engine 6" -> ENGINE_6, "Rescue Four" -> RESCUE_TEAM_4, "generator truck" -> GENERATOR_TRUCK, "supply truck five" -> SUPPLY_TRUCK_5, "Team Bravo" -> TEAM_BRAVO, "Boat two" -> BOAT_2.
- Canonicalize task/outcome entities similarly: "water drop" -> WATER_DROP, "Sector 3 evacuation" -> SECTOR_3_EVACUATION, "road clearance" -> ROAD_CLEARANCE, "Building C search" -> BUILDING_C_SEARCH, "patient transfer" -> PATIENT_TRANSFER, "fire line" -> FIRE_LINE, "decontamination" -> DECONTAMINATION, and "resource request" -> RESOURCE_REQUEST.
- When a task or outcome is explicitly stated but no responsible resource is named in the same report, use the canonical task/outcome entity_id instead of substituting a scenario_context resource_id.
- Explicit task/outcome completion or verification is enough for a state_event on that task/outcome entity_id; do not downgrade it to an assumption or unresolved claim merely because no resource is named.
- When an operation completion is reported and a responsible resource is explicitly identifiable in the same report, use the resource_id as state_event.entity_id and put the operation id in state_event.operation_id.
- Do not use an operation id as state_event.entity_id when the mapped resource_id is known.

Blocker guidance:
- When a report states why an entity cannot proceed, enter, arrive, or complete, emit a blocker.
- If the blocker subject is named in the report, blocker.entity_id must use that subject's canonical entity_id, even when it is not listed in scenario_context.
- If a report says an entity is stopped, stuck, unable to proceed, or cannot continue because of a blocker cause, emit the blocked/failed state_event as well as the blocker.
- blocker.type must describe the cause category, not the lifecycle state. Do not use BLOCKED as blocker.type when the cause is known.
- Use VISIBILITY for smoke, zero visibility, visibility, or unable to enter because of smoke.
- Use DEBRIS for debris, CLOSED_BRIDGE for closed bridges, CHEMICAL_EXPOSURE for chemical exposure risk, POLICE_CLEARANCE for police clearance, ROAD_COLLAPSE for collapsed access roads, FLOODWATER for floodwater, STRUCTURAL_INSTABILITY for structural instability, and MECHANICAL_FAILURE for propulsion or vehicle failure.

Uncertainty and claims:
- For uncertain task/outcome statements, use the canonical task/outcome entity_id in assumption.entity_id when the specific resource is not named.
- For unlinked outcome reports where an outcome is stated but the responsible operational resource is not identified, emit a claim with unresolved=true instead of a state_event.
- A claim must remain unresolved=true when it cannot be safely tied to a specific resource state transition, even if the outcome sounds favorable or complete.
""".strip()


DRAFT_STATUS_INSTRUCTION = """
Draft a radio-style status verification request.
The draft must be under 25 words.
Ask only for current status or position.
Do not issue a new deployment order.
Do not assume failure, arrival, completion, or blame.
Return JSON only: {"draft": "..."}.
""".strip()


class GeminiIntelligenceService:
    def __init__(
        self,
        *,
        client: GeminiClientProtocol | None = None,
        model: str | None = None,
        api_key: str | None = None,
        load_env: bool = True,
    ) -> None:
        if load_env:
            _load_dotenv()
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.client = client or self._build_client(api_key=api_key)

    def extract_report(self, request: ExtractRequest) -> ExtractionResult:
        if self.client is None:
            raise MissingGeminiCredentialsError("GEMINI_API_KEY is required for live extraction")

        prompt = self._build_extraction_prompt(request)
        raw_response = self._generate_json(
            prompt,
            response_schema=ExtractionResult,
        )
        try:
            return ExtractionResult.model_validate(raw_response)
        except ValidationError as exc:
            raise GeminiResponseValidationError(str(exc)) from exc

    def draft_status(self, request: DraftStatusRequest) -> DraftStatusResponse:
        if self.client is None:
            return self._fallback_status_draft(request)

        prompt = self._build_status_prompt(request)
        raw_response = self._generate_json(prompt, response_schema=GeminiDraftPayload)
        try:
            draft_payload = GeminiDraftPayload.model_validate(raw_response)
            response = DraftStatusResponse.model_validate(
                {
                    "draft": draft_payload.draft,
                    "draft_source": "GEMINI",
                }
            )
        except (TypeError, ValidationError) as exc:
            raise GeminiResponseValidationError(str(exc)) from exc
        self._reject_deployment_order(response.draft)
        return response

    def _build_client(self, *, api_key: str | None) -> GeminiClientProtocol | None:
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            return None

        try:
            from google import genai
        except ImportError as exc:
            raise GeminiServiceError("google-genai is not installed") from exc

        return genai.Client(api_key=key)

    def _generate_json(self, prompt: str, *, response_schema: type[Any]) -> dict[str, Any]:
        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=response_schema.model_json_schema(),
                ),
            )
        except Exception as exc:
            raise GeminiServiceError(str(exc)) from exc

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, response_schema):
            return parsed.model_dump()

        text = getattr(response, "text", None)
        if not text:
            raise GeminiResponseValidationError("Gemini response did not include JSON text")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiResponseValidationError("Gemini response was not valid JSON") from exc

    def _build_extraction_prompt(self, request: ExtractRequest) -> str:
        safe_context = request.scenario_context.model_dump()
        return "\n\n".join(
            [
                EXTRACTION_INSTRUCTION,
                "Scenario context, without ground truth:",
                json.dumps(safe_context, indent=2, sort_keys=True),
                "Raw field report:",
                request.raw_text,
            ]
        )

    def _build_status_prompt(self, request: DraftStatusRequest) -> str:
        return "\n\n".join(
            [
                DRAFT_STATUS_INSTRUCTION,
                "Status context:",
                json.dumps(request.model_dump(), indent=2, sort_keys=True),
            ]
        )

    def _fallback_status_draft(self, request: DraftStatusRequest) -> DraftStatusResponse:
        subject = request.resource_id or request.operation_id or "Unit"
        location = f" near {request.location}" if request.location else ""
        draft = f"{subject}, confirm current status and position{location}."
        return DraftStatusResponse(draft=draft, draft_source="FALLBACK_TEMPLATE")

    def _reject_deployment_order(self, draft: str) -> None:
        deployment_words = ("deploy", "dispatch", "proceed to", "respond to", "go to")
        lowered = draft.lower()
        if any(word in lowered for word in deployment_words):
            raise GeminiResponseValidationError("status draft must not issue a deployment order")


def _load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
