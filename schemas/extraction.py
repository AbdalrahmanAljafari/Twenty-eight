from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    raw_text: str
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model_text(cls, text: str) -> ExtractionResult:
        parsed = parse_extraction_json(text)
        return cls(raw_text=text.strip(), data=parsed)


def parse_extraction_json(text: str) -> dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            payload = json.loads(match.group(0))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

    return {"summary": text}
