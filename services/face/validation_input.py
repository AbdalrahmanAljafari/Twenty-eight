from __future__ import annotations

import json
import re

from clients.openrouter import OpenRouterClient
from config.settings import PipelineProfile
from schemas.responses import InputValidationResult
from utils.image import get_image_size, read_image_bytes
from utils.prompts import load_input_validation_prompt

MAX_IMAGE_BYTES = 15 * 1024 * 1024
FACE_INPUT_SIZE = 512


class InputValidationError(ValueError):
    pass


def validate_basic_image_input(source: bytes | str) -> tuple[int, int, int]:
    image_bytes = read_image_bytes(source)
    size_bytes = len(image_bytes)

    if size_bytes == 0:
        raise InputValidationError("Uploaded image is empty")
    if size_bytes > MAX_IMAGE_BYTES:
        raise InputValidationError("Uploaded image exceeds 15MB limit")

    width, height = get_image_size(image_bytes)

    if width != FACE_INPUT_SIZE or height != FACE_INPUT_SIZE:
        raise InputValidationError(
            f"Face image must be {FACE_INPUT_SIZE}x{FACE_INPUT_SIZE} pixels, "
            f"got {width}x{height}"
        )

    return width, height, size_bytes


async def validate_image_input(
    source: bytes | str,
    profile: PipelineProfile,
    client: OpenRouterClient | None = None,
) -> InputValidationResult:
    image_bytes = read_image_bytes(source)
    width, height, size_bytes = validate_basic_image_input(image_bytes)

    openrouter = client or OpenRouterClient()
    raw_text = await openrouter.analyze_image(
        model=profile.validation_model,
        prompt=load_input_validation_prompt(),
        image_source=image_bytes,
    )

    result = parse_input_validation_result(
        raw_text,
        width=width,
        height=height,
        size_bytes=size_bytes,
    )

    if not result.passed:
        message = "; ".join(result.failures) or "Uploaded image failed validation"
        raise InputValidationError(message)

    return result


def parse_input_validation_result(
    text: str,
    *,
    width: int = 0,
    height: int = 0,
    size_bytes: int = 0,
) -> InputValidationResult:
    payload = text.strip()

    if payload.startswith("```"):
        payload = re.sub(r"^```(?:json)?\s*", "", payload)
        payload = re.sub(r"\s*```$", "", payload)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", payload, flags=re.DOTALL)
        if not match:
            return InputValidationResult(
                passed=False,
                score=0,
                failures=["Could not parse input validation response"],
                raw_text=text,
                width=width,
                height=height,
                size_bytes=size_bytes,
            )
        data = json.loads(match.group(0))

    checks = {
        str(key): bool(value)
        for key, value in data.get("checks", {}).items()
    }
    failures = [str(item) for item in data.get("failures", [])]
    warnings = [str(item) for item in data.get("warnings", [])]
    score = int(data.get("score", 0))
    passed = bool(data.get("pass", False))

    critical_checks = (
        "face_present",
        "is_female_face",
        "is_frontal",
        "occlusion_ok",
        "landmarks_visible",
        "framing_ok",
        "lighting_ok",
        "quality_ok",
    )
    if checks and all(checks.get(name, False) for name in critical_checks):
        passed = True
    elif checks and any(not checks.get(name, True) for name in critical_checks):
        passed = False

    if score >= 8 and checks and all(checks.get(name, False) for name in critical_checks):
        passed = True

    return InputValidationResult(
        passed=passed,
        score=score,
        failures=failures,
        warnings=warnings,
        checks=checks,
        raw_text=text,
        width=width,
        height=height,
        size_bytes=size_bytes,
    )
