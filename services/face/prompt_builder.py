from __future__ import annotations

from config.settings import PipelineProfile
from schemas.extraction import ExtractionResult
from services.face.extraction import format_extracted_data
from utils.prompts import build_generation_prompt


def build_portrait_prompt(
    profile: PipelineProfile,
    extraction: ExtractionResult | None = None,
    correction_notes: str | None = None,
) -> str:
    extracted_data = None
    if extraction is not None:
        extracted_data = format_extracted_data(extraction)

    prompt = build_generation_prompt(profile, extracted_data)

    if correction_notes:
        prompt = (
            f"{prompt}\n\n"
            "--- CORRECTIONS REQUIRED FROM PREVIOUS ATTEMPT ---\n"
            f"{correction_notes.strip()}\n"
            "--- END CORRECTIONS ---"
        )

    return prompt
