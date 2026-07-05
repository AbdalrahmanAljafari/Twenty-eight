from __future__ import annotations

import json
import re

from clients.openrouter import OpenRouterClient
from config.settings import PipelineProfile
from schemas.responses import SanityCheckResult

SANITY_CHECK_PROMPT = """
The first image is the original uploaded face. The second image is the generated portrait.

Compare the generated portrait against the original uploaded face.

Evaluate:
1. Same person? (identity match score 1-10)
2. Eye color preserved?
3. Skin tone family preserved?
4. Hair type, color, length preserved?
5. Facial landmarks visible and unobstructed?
6. Background is pure white?
7. Pose is frontal and symmetrical?
8. Any hallucinated features (new moles, wrong eye color, invented hair)?

Return JSON only:
{"pass": true/false, "score": N, "failures": [], "corrections": []}

Mark pass=true only if score is 8 or higher and there are no critical identity failures.
"""


async def run_sanity_check(
    source_image: bytes | str,
    generated_image: bytes,
    profile: PipelineProfile,
    client: OpenRouterClient | None = None,
) -> SanityCheckResult:
    openrouter = client or OpenRouterClient()

    raw_text = await openrouter.analyze_image(
        model=profile.validation_model,
        prompt=SANITY_CHECK_PROMPT,
        image_source=generated_image,
        reference_image_source=source_image,
    )

    return parse_sanity_result(raw_text)


def parse_sanity_result(text: str) -> SanityCheckResult:
    payload = text.strip()

    if payload.startswith("```"):
        payload = re.sub(r"^```(?:json)?\s*", "", payload)
        payload = re.sub(r"\s*```$", "", payload)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", payload, flags=re.DOTALL)
        if not match:
            return SanityCheckResult(
                passed=False,
                score=0,
                failures=["Could not parse sanity check response"],
                corrections=["Regenerate with stricter identity preservation"],
                raw_text=text,
            )
        data = json.loads(match.group(0))

    passed = bool(data.get("pass", False))
    score = int(data.get("score", 0))
    failures = [str(item) for item in data.get("failures", [])]
    corrections = [str(item) for item in data.get("corrections", [])]

    if score >= 8 and not failures:
        passed = True

    return SanityCheckResult(
        passed=passed,
        score=score,
        failures=failures,
        corrections=corrections,
        raw_text=text,
    )
