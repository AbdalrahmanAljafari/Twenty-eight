from __future__ import annotations

import json

from clients.openrouter import OpenRouterClient
from config.settings import PipelineProfile
from schemas.extraction import ExtractionResult
from utils.prompts import load_extraction_prompt

EXTRACTION_JSON_SUFFIX = (
    "\n\nReturn your analysis as structured JSON only. "
    "Do not include markdown fences."
)


async def extract_visual_attributes(
    image_source: bytes | str,
    profile: PipelineProfile,
    client: OpenRouterClient | None = None,
) -> ExtractionResult:
    openrouter = client or OpenRouterClient()
    prompt = load_extraction_prompt(profile) + EXTRACTION_JSON_SUFFIX

    raw_text = await openrouter.analyze_image(
        model=profile.extraction_model,
        prompt=prompt,
        image_source=image_source,
    )
    return ExtractionResult.from_model_text(raw_text)


def format_extracted_data(extraction: ExtractionResult) -> str:
    if extraction.data:
        return json.dumps(extraction.data, ensure_ascii=False, indent=2)
    return extraction.raw_text
