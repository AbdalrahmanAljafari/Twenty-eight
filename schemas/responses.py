from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from config.settings import Provider


class GenerateFaceRequest(BaseModel):
    extraction_provider: Provider | None = None
    generation_provider: Provider | None = None
    validation_provider: Provider | None = None


class PortraitQAResult(BaseModel):
    passed: bool
    score: int = 0
    failures: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    raw_text: str = ""


class InputValidationResult(BaseModel):
    passed: bool
    score: int = 0
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)
    raw_text: str = ""
    width: int = 0
    height: int = 0
    size_bytes: int = 0


class GenerateFaceResponse(BaseModel):
    client_id: str
    portrait_path: str
    portrait_base64: str
    source_path: str
    result_path: str
    extracted: dict[str, Any]
    portrait_qa: PortraitQAResult
    pipeline: dict[str, str]
    attempts: int
