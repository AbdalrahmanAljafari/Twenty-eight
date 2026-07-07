from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from config.settings import MODELS_YAML_PATH, PipelineProfile, PROJECT_ROOT, ProviderProfile


def resolve_prompt_path(path: Path | str) -> Path:
    prompt_path = Path(path)
    if not prompt_path.is_absolute():
        prompt_path = PROJECT_ROOT / prompt_path
    return prompt_path


@lru_cache(maxsize=32)
def load_prompt_file(path: str) -> str:
    prompt_path = resolve_prompt_path(path)
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def load_prompt(path: Path | str) -> str:
    return load_prompt_file(str(resolve_prompt_path(path)))


def load_extraction_prompt(profile: PipelineProfile | ProviderProfile) -> str:
    return load_prompt(profile.extraction_prompt)


def load_generation_prompt(profile: PipelineProfile | ProviderProfile) -> str:
    return load_prompt(profile.generation_prompt)


@lru_cache(maxsize=1)
def load_input_validation_prompt() -> str:
    with MODELS_YAML_PATH.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)
    prompt_path = config.get("pipeline", {}).get(
        "input_validation_prompt",
        "prompts/validation/face_input_check.txt",
    )
    return load_prompt(prompt_path)


def build_generation_prompt(
    profile: PipelineProfile,
    extracted_data: str | None = None,
) -> str:
    base_prompt = load_generation_prompt(profile)

    if not extracted_data:
        return base_prompt

    return (
        f"{base_prompt}\n\n"
        "--- EXTRACTED VISUAL ATTRIBUTES ---\n"
        f"{extracted_data.strip()}\n"
        "--- END EXTRACTED DATA ---"
    )
