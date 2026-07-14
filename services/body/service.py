from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from clients.openrouter import OpenRouterClient
from config.settings import PROJECT_ROOT, Provider, Settings, get_settings
from schemas.body import GenerateBodyResponse
from services.body.generation import generate_apose_image
from utils.image import to_data_uri
from utils.prompts import load_body_apose_prompts

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BODY_OUTPUT_DIRNAME = "body"
APOSE_OUTPUT_DIRNAME = "Apose"


def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def generate_client_id() -> str:
    return str(uuid.uuid4())


def _append_subject_metadata(prompt: str, *, height_cm: float, age: int) -> str:
    return (
        f"{prompt}\n\n"
        "--- SUBJECT METADATA ---\n"
        f"Height: {height_cm:g} cm\n"
        f"Age: {age}\n"
        "--- END SUBJECT METADATA ---"
    )


def save_body_apose_output(
    *,
    client_id: str,
    front_source_bytes: bytes,
    side_source_bytes: bytes,
    front_apose_bytes: bytes,
    front_apose_mime: str,
    side_apose_bytes: bytes,
    side_apose_mime: str,
    height_cm: float,
    age: int,
    pipeline: dict[str, str],
) -> dict[str, str]:
    ensure_outputs_dir()
    apose_dir = OUTPUTS_DIR / client_id / BODY_OUTPUT_DIRNAME / APOSE_OUTPUT_DIRNAME
    apose_dir.mkdir(parents=True, exist_ok=True)

    front_source_path = apose_dir / "source_front.jpg"
    side_source_path = apose_dir / "source_side.jpg"
    front_ext = ".png" if "png" in front_apose_mime else ".jpg"
    side_ext = ".png" if "png" in side_apose_mime else ".jpg"
    front_apose_path = apose_dir / f"front_Apose{front_ext}"
    side_apose_path = apose_dir / f"side_Apose{side_ext}"
    result_path = apose_dir / "result.json"

    front_source_path.write_bytes(front_source_bytes)
    side_source_path.write_bytes(side_source_bytes)
    front_apose_path.write_bytes(front_apose_bytes)
    side_apose_path.write_bytes(side_apose_bytes)

    def rel(path: Path) -> str:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")

    result_payload = {
        "client_id": client_id,
        "feature": BODY_OUTPUT_DIRNAME,
        "stage": APOSE_OUTPUT_DIRNAME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "height_cm": height_cm,
        "age": age,
        "pipeline": pipeline,
        "files": {
            "source_front": rel(front_source_path),
            "source_side": rel(side_source_path),
            "front_Apose": rel(front_apose_path),
            "side_Apose": rel(side_apose_path),
        },
    }
    result_path.write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "client_id": client_id,
        "front_apose_path": result_payload["files"]["front_Apose"],
        "side_apose_path": result_payload["files"]["side_Apose"],
        "result_path": rel(result_path),
    }


class BodyService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: OpenRouterClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or OpenRouterClient(self.settings)

    async def generate_body_apose(
        self,
        front_bytes: bytes,
        side_bytes: bytes,
        *,
        height_cm: float,
        age: int,
        client_id: str | None = None,
        generation_provider: Provider | str | None = None,
    ) -> GenerateBodyResponse:
        resolved_client_id = client_id.strip() if client_id and client_id.strip() else generate_client_id()

        profile = self.settings.get_pipeline_profile(
            generation_provider=generation_provider,
        )

        front_base_prompt, side_base_prompt = load_body_apose_prompts()
        front_prompt = _append_subject_metadata(
            front_base_prompt,
            height_cm=height_cm,
            age=age,
        )
        side_prompt = _append_subject_metadata(
            side_base_prompt,
            height_cm=height_cm,
            age=age,
        )

        front_apose_bytes, front_apose_mime = await generate_apose_image(
            front_bytes,
            front_prompt,
            profile,
            client=self.client,
        )
        side_apose_bytes, side_apose_mime = await generate_apose_image(
            side_bytes,
            side_prompt,
            profile,
            client=self.client,
        )

        pipeline = {
            "generation_provider": profile.generation_provider.value,
            "generation_model": profile.generation_model,
        }

        stored = save_body_apose_output(
            client_id=resolved_client_id,
            front_source_bytes=front_bytes,
            side_source_bytes=side_bytes,
            front_apose_bytes=front_apose_bytes,
            front_apose_mime=front_apose_mime,
            side_apose_bytes=side_apose_bytes,
            side_apose_mime=side_apose_mime,
            height_cm=height_cm,
            age=age,
            pipeline=pipeline,
        )

        return GenerateBodyResponse(
            message="Body A-pose images generated",
            client_id=stored["client_id"],
            height_cm=height_cm,
            age=age,
            front_image_size_bytes=len(front_bytes),
            side_image_size_bytes=len(side_bytes),
            front_apose_path=stored["front_apose_path"],
            side_apose_path=stored["side_apose_path"],
            front_apose_base64=to_data_uri(front_apose_bytes, front_apose_mime),
            side_apose_base64=to_data_uri(side_apose_bytes, side_apose_mime),
            result_path=stored["result_path"],
            pipeline=pipeline,
        )
