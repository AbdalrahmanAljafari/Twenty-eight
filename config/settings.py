from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_YAML_PATH = Path(__file__).resolve().parent / "models.yaml"


class Provider(str, Enum):
    GEMINI = "gemini"
    GPT = "gpt"


class ProviderProfile:
    """Single-provider stack (legacy helper)."""

    def __init__(
        self,
        name: Provider,
        vlm_model: str,
        generation_model: str,
        extraction_prompt: Path,
        generation_prompt: Path,
    ) -> None:
        self.name = name
        self.vlm_model = vlm_model
        self.generation_model = generation_model
        self.extraction_prompt = extraction_prompt
        self.generation_prompt = generation_prompt

    @property
    def validation_model(self) -> str:
        return self.vlm_model


class PipelineProfile:
    """Resolved providers and models for one pipeline run."""

    def __init__(
        self,
        extraction_provider: Provider,
        generation_provider: Provider,
        validation_provider: Provider,
        extraction_model: str,
        generation_model: str,
        validation_model: str,
        extraction_prompt: Path,
        generation_prompt: Path,
    ) -> None:
        self.extraction_provider = extraction_provider
        self.generation_provider = generation_provider
        self.validation_provider = validation_provider
        self.extraction_model = extraction_model
        self.generation_model = generation_model
        self.validation_model = validation_model
        self.extraction_prompt = extraction_prompt
        self.generation_prompt = generation_prompt

    @property
    def is_mixed(self) -> bool:
        providers = {
            self.extraction_provider,
            self.generation_provider,
            self.validation_provider,
        }
        return len(providers) > 1


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_app_name: str = Field("Body Vision", alias="OPENROUTER_APP_NAME")
    openrouter_site_url: str = Field(
        "http://localhost:9000",
        alias="OPENROUTER_SITE_URL",
    )
    fal_key: str | None = Field(None, alias="FAL_KEY")

    extraction_provider: Provider = Field(..., alias="EXTRACTION_PROVIDER")
    generation_provider: Provider = Field(..., alias="GENERATION_PROVIDER")
    validation_provider: Provider = Field(..., alias="VALIDATION_PROVIDER")

    gemini_vlm_model: str = Field(
        "google/gemini-3.1-pro-preview",
        alias="GEMINI_VLM_MODEL",
    )
    gemini_generation_model: str = Field(
        "google/gemini-3-pro-image-preview",
        alias="GEMINI_GENERATION_MODEL",
    )

    gpt_vlm_model: str = Field(
        "openai/gpt-5.4-image-2",
        alias="GPT_VLM_MODEL",
    )
    gpt_generation_model: str = Field(
        "openai/gpt-5.4-image-2",
        alias="GPT_GENERATION_MODEL",
    )

    retry_max_attempts: int = Field(3, alias="RETRY_MAX_ATTEMPTS")

    @field_validator(
        "extraction_provider",
        "generation_provider",
        "validation_provider",
        mode="before",
    )
    @classmethod
    def normalize_provider_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    def _load_models_yaml(self) -> dict[str, Any]:
        with MODELS_YAML_PATH.open(encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _provider_models(self, provider: Provider) -> tuple[str, str]:
        if provider == Provider.GEMINI:
            return self.gemini_vlm_model, self.gemini_generation_model
        return self.gpt_vlm_model, self.gpt_generation_model

    def _provider_prompts(self, provider: Provider) -> tuple[Path, Path]:
        config = self._load_models_yaml()
        provider_config = config["providers"][provider.value]
        return (
            PROJECT_ROOT / provider_config["extraction_prompt"],
            PROJECT_ROOT / provider_config["generation_prompt"],
        )

    def resolve_provider(self, requested: Provider | str | None) -> Provider | None:
        if requested is None:
            return None
        if isinstance(requested, str):
            return Provider(requested.strip().lower())
        return requested

    def get_pipeline_profile(
        self,
        extraction_provider: Provider | str | None = None,
        generation_provider: Provider | str | None = None,
        validation_provider: Provider | str | None = None,
    ) -> PipelineProfile:
        resolved_extraction = (
            self.resolve_provider(extraction_provider) or self.extraction_provider
        )
        resolved_generation = (
            self.resolve_provider(generation_provider) or self.generation_provider
        )
        resolved_validation = (
            self.resolve_provider(validation_provider) or self.validation_provider
        )

        extraction_vlm, _ = self._provider_models(resolved_extraction)
        _, generation_model = self._provider_models(resolved_generation)
        validation_vlm, _ = self._provider_models(resolved_validation)

        extraction_prompt, _ = self._provider_prompts(resolved_extraction)
        _, generation_prompt = self._provider_prompts(resolved_generation)

        return PipelineProfile(
            extraction_provider=resolved_extraction,
            generation_provider=resolved_generation,
            validation_provider=resolved_validation,
            extraction_model=extraction_vlm,
            generation_model=generation_model,
            validation_model=validation_vlm,
            extraction_prompt=extraction_prompt,
            generation_prompt=generation_prompt,
        )

    def get_provider_profile(self, provider: Provider) -> ProviderProfile:
        vlm_model, generation_model = self._provider_models(provider)
        extraction_prompt, generation_prompt = self._provider_prompts(provider)

        return ProviderProfile(
            name=provider,
            vlm_model=vlm_model,
            generation_model=generation_model,
            extraction_prompt=extraction_prompt,
            generation_prompt=generation_prompt,
        )

    @property
    def retry_limit(self) -> int:
        config = self._load_models_yaml()
        return int(config.get("pipeline", {}).get("retry_max_attempts", self.retry_max_attempts))


@lru_cache
def get_settings() -> Settings:
    return Settings()
