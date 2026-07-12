from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StateEvent(StrictBaseModel):
    operation_id: str | None = None
    entity_id: str
    previous_state: str | None = None
    new_state: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class Assumption(StrictBaseModel):
    text: str
    entity_id: str | None = None
    blocked_transition: str | None = None
    reason: str


class Claim(StrictBaseModel):
    text: str
    entity_id: str | None = None
    operation_id: str | None = None
    unresolved: bool = True
    reason: str


class Blocker(StrictBaseModel):
    entity_id: str | None = None
    operation_id: str | None = None
    type: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractionResult(StrictBaseModel):
    incident_type: str | None = None
    severity: str | None = None
    location: str | None = None
    state_events: list[StateEvent] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    blockers: list[Blocker] = Field(default_factory=list)
    related_operation: str | None = None
    need_still_active: bool = False
    transport_source: str | None = None


class OperationContext(StrictBaseModel):
    id: str
    type: str | None = None
    resource_id: str | None = None
    location: str | None = None


class ScenarioContext(StrictBaseModel):
    operations: list[OperationContext] = Field(default_factory=list)
    resources: list[dict[str, Any]] = Field(default_factory=list)
    state_machine: list[str] = Field(default_factory=list)


class ExtractRequest(StrictBaseModel):
    raw_text: str = Field(min_length=1)
    scenario_context: ScenarioContext = Field(default_factory=ScenarioContext)


class DraftStatusRequest(StrictBaseModel):
    resource_id: str | None = None
    operation_id: str | None = None
    current_state: str | None = None
    missing_confirmation: str
    active_need: str | None = None
    location: str | None = None


class DraftStatusResponse(StrictBaseModel):
    draft: str
    draft_source: Literal["GEMINI", "FALLBACK_TEMPLATE"]

    @field_validator("draft")
    @classmethod
    def draft_under_25_words(cls, value: str) -> str:
        words = [word for word in value.split() if word.strip()]
        if len(words) > 25:
            raise ValueError("draft must be 25 words or fewer")
        return value


class GeminiDraftPayload(StrictBaseModel):
    draft: str

    @field_validator("draft")
    @classmethod
    def draft_under_25_words(cls, value: str) -> str:
        words = [word for word in value.split() if word.strip()]
        if len(words) > 25:
            raise ValueError("draft must be 25 words or fewer")
        return value


EXTRACTION_RESPONSE_SCHEMA = ExtractionResult.model_json_schema()
