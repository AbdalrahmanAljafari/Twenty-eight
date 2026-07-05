from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from config.settings import Provider


class GenerateFaceRequest(BaseModel):
    extraction_provider: Provider | None = None
    generation_provider: Provider | None = None
    validation_provider: Provider | None = None


class SanityCheckResult(BaseModel):
    passed: bool
    score: int = 0
    failures: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    raw_text: str = ""


class GenerateFaceResponse(BaseModel):
    client_id: str
    portrait_path: str
    portrait_base64: str
    source_path: str
    result_path: str
    extracted: dict[str, Any]
    sanity_check: SanityCheckResult
    pipeline: dict[str, str]
    attempts: int
