from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from clients.openrouter import OpenRouterClient
from config.settings import PROJECT_ROOT, Provider, Settings, get_settings
from schemas.responses import GenerateFaceResponse, PortraitQAResult
from services.face.extraction import extract_visual_attributes
from services.face.generation import generate_portrait
from services.face.portrait_qa import run_portrait_qa
from services.face.prompt_builder import build_portrait_prompt
from services.face.validation_input import validate_image_input
from utils.image import to_data_uri

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FACE_OUTPUT_DIRNAME = "face"


def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def generate_client_id() -> str:
    return str(uuid.uuid4())


def save_face_output(
    *,
    client_id: str,
    source_bytes: bytes,
    portrait_bytes: bytes,
    portrait_mime: str,
    extracted: dict,
    portrait_qa: dict,
    pipeline: dict[str, str],
    attempts: int,
    generation_prompt: str,
) -> dict[str, str]:
    ensure_outputs_dir()
    face_dir = OUTPUTS_DIR / client_id / FACE_OUTPUT_DIRNAME
    face_dir.mkdir(parents=True, exist_ok=True)

    source_path = face_dir / "source.jpg"
    portrait_ext = ".png" if "png" in portrait_mime else ".jpg"
    portrait_path = face_dir / f"portrait{portrait_ext}"
    prompt_path = face_dir / "prompt.txt"
    result_path = face_dir / "result.json"

    source_path.write_bytes(source_bytes)
    portrait_path.write_bytes(portrait_bytes)
    prompt_path.write_text(generation_prompt, encoding="utf-8")

    result_payload = {
        "client_id": client_id,
        "feature": FACE_OUTPUT_DIRNAME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "extracted": extracted,
        "portrait_qa": portrait_qa,
        "pipeline": pipeline,
        "attempts": attempts,
        "files": {
            "source": str(source_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "portrait": str(portrait_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "prompt": str(prompt_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        },
    }
    result_path.write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "client_id": client_id,
        "source_path": result_payload["files"]["source"],
        "portrait_path": result_payload["files"]["portrait"],
        "result_path": str(result_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }


class FaceService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: OpenRouterClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or OpenRouterClient(self.settings)

    async def generate_face_portrait(
        self,
        image_bytes: bytes,
        *,
        extraction_provider: Provider | str | None = None,
        generation_provider: Provider | str | None = None,
        validation_provider: Provider | str | None = None,
    ) -> GenerateFaceResponse:
        resolved_client_id = generate_client_id()

        profile = self.settings.get_pipeline_profile(
            extraction_provider=extraction_provider,
            generation_provider=generation_provider,
            validation_provider=validation_provider,
        )

        await validate_image_input(image_bytes, profile, client=self.client)

        extraction = await extract_visual_attributes(
            image_bytes,
            profile,
            client=self.client,
        )

        correction_notes: str | None = None
        portrait_qa_result = PortraitQAResult(passed=False)
        portrait_bytes: bytes | None = None
        portrait_mime = "image/png"
        final_prompt = ""
        attempts = 0
        max_attempts = self.settings.retry_limit

        for attempt in range(1, max_attempts + 1):
            attempts = attempt
            prompt = build_portrait_prompt(
                profile,
                extraction=extraction,
                correction_notes=correction_notes,
            )
            final_prompt = prompt
            portrait_bytes, portrait_mime = await generate_portrait(
                image_bytes,
                prompt,
                profile,
                client=self.client,
            )
            portrait_qa_result = await run_portrait_qa(
                image_bytes,
                portrait_bytes,
                profile,
                client=self.client,
            )
            if portrait_qa_result.passed:
                break
            correction_notes = "\n".join(
                portrait_qa_result.corrections or portrait_qa_result.failures
            )

        if portrait_bytes is None:
            raise RuntimeError("Portrait generation did not produce an image")

        stored = save_face_output(
            client_id=resolved_client_id,
            source_bytes=image_bytes,
            portrait_bytes=portrait_bytes,
            portrait_mime=portrait_mime,
            extracted=extraction.data,
            portrait_qa=portrait_qa_result.model_dump(),
            pipeline={
                "extraction_provider": profile.extraction_provider.value,
                "generation_provider": profile.generation_provider.value,
                "validation_provider": profile.validation_provider.value,
                "extraction_model": profile.extraction_model,
                "generation_model": profile.generation_model,
                "validation_model": profile.validation_model,
            },
            attempts=attempts,
            generation_prompt=final_prompt,
        )

        return GenerateFaceResponse(
            client_id=stored["client_id"],
            portrait_path=stored["portrait_path"],
            portrait_base64=to_data_uri(portrait_bytes, portrait_mime),
            source_path=stored["source_path"],
            result_path=stored["result_path"],
            extracted=extraction.data,
            portrait_qa=portrait_qa_result,
            pipeline={
                "extraction_provider": profile.extraction_provider.value,
                "generation_provider": profile.generation_provider.value,
                "validation_provider": profile.validation_provider.value,
            },
            attempts=attempts,
        )
