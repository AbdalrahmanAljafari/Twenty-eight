from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clients.openrouter import OpenRouterClient
from clients.sapiens import SapiensClient
from config.settings import PROJECT_ROOT, Provider, Settings, get_settings
from schemas.body import GenerateBodyResponse, StandardizeBodyResponse, VisionBodyResponse
from services.body.a_pose import generate_apose_image
from services.body.standardization import run_standardization
from services.body.vision import run_vision_pipeline
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
        "front_apose_abs": str(front_apose_path),
        "side_apose_abs": str(side_apose_path),
    }


class BodyService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: OpenRouterClient | None = None,
        sapiens_client: SapiensClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or OpenRouterClient(self.settings)
        self.sapiens = sapiens_client or SapiensClient(self.settings)

    async def generate_body_apose(
        self,
        front_bytes: bytes,
        side_bytes: bytes,
        *,
        height_cm: float,
        age: int,
        client_id: str | None = None,
        generation_provider: Provider | str | None = None,
        run_standardize: bool = True,
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

        response = GenerateBodyResponse(
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

        if run_standardize:
            aligned = await self.standardize_body(
                client_id=stored["client_id"],
                height_cm=height_cm,
            )
            response.message = "Body A-pose generated and standardized"
            response.standardized = True
            response.front_crop_path = aligned.front_crop_path
            response.side_crop_path = aligned.side_crop_path
            response.front_scaled_path = aligned.front_scaled_path
            response.side_scaled_path = aligned.side_scaled_path
            response.front_aligned_path = aligned.front_aligned_path
            response.side_aligned_path = aligned.side_aligned_path
            response.align_result_path = aligned.result_path
            response.sapiens_bboxes = aligned.sapiens_bboxes
            response.pipeline = {
                **pipeline,
                "sapiens_base_url": self.settings.sapiens_base_url,
                "standardize": "true",
            }

        return response

    def _resolve_apose_paths(self, client_id: str) -> tuple[Path, Path, float | None]:
        apose_dir = OUTPUTS_DIR / client_id / BODY_OUTPUT_DIRNAME / APOSE_OUTPUT_DIRNAME
        if not apose_dir.exists():
            raise FileNotFoundError(f"Apose folder not found for client_id={client_id}")

        front_matches = sorted(apose_dir.glob("front_Apose.*"))
        side_matches = sorted(apose_dir.glob("side_Apose.*"))
        if not front_matches:
            raise FileNotFoundError(f"front_Apose image not found for client_id={client_id}")
        if not side_matches:
            raise FileNotFoundError(f"side_Apose image not found for client_id={client_id}")

        height_cm: float | None = None
        result_path = apose_dir / "result.json"
        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            raw_height = payload.get("height_cm")
            if raw_height is not None:
                height_cm = float(raw_height)

        return front_matches[0], side_matches[0], height_cm

    def _build_standardize_response(
        self,
        stored: dict[str, Any],
        *,
        sapiens_bboxes: dict[str, Any] | None = None,
    ) -> StandardizeBodyResponse:
        files = stored["files"]
        return StandardizeBodyResponse(
            client_id=stored["client_id"],
            height_cm=stored["height_cm"],
            pixels_per_cm=stored["pixels_per_cm"],
            canvas_size=stored["canvas_size"],
            front_crop_path=files["front_crop"],
            side_crop_path=files["side_crop"],
            front_scaled_path=files["front_scaled"],
            side_scaled_path=files["side_scaled"],
            front_aligned_path=files["front_aligned"],
            side_aligned_path=files["side_aligned"],
            result_path=stored["result_path"],
            views=stored["views"],
            sapiens_bboxes=sapiens_bboxes,
        )

    async def standardize_body(
        self,
        *,
        client_id: str,
        front_bbox: dict | None = None,
        side_bbox: dict | None = None,
        height_cm: float | None = None,
        include_visual: bool = False,
    ) -> StandardizeBodyResponse:
        front_path, side_path, stored_height = self._resolve_apose_paths(client_id)
        resolved_height = height_cm if height_cm is not None else stored_height
        if resolved_height is None:
            raise ValueError("height_cm is required when missing from Apose result.json")

        sapiens_payload: dict[str, Any] | None = None
        if front_bbox is None or side_bbox is None:
            sapiens_payload = await self.sapiens.segment(
                front_path,
                side_path,
                front_filename=front_path.name,
                side_filename=side_path.name,
                include_visual=include_visual,
            )
            front_bbox, side_bbox = self.sapiens.extract_bboxes(sapiens_payload)

        stored = run_standardization(
            client_id=client_id,
            front_image_path=front_path,
            side_image_path=side_path,
            front_bbox=front_bbox,
            side_bbox=side_bbox,
            height_cm=resolved_height,
            settings=self.settings,
        )
        bboxes_meta = None
        if sapiens_payload is not None:
            bboxes_meta = {
                "front": sapiens_payload["front"]["bbox"],
                "side": sapiens_payload["side"]["bbox"],
                "front_score": sapiens_payload["front"].get("score"),
                "side_score": sapiens_payload["side"].get("score"),
            }
        else:
            bboxes_meta = {"front": front_bbox, "side": side_bbox}

        return self._build_standardize_response(stored, sapiens_bboxes=bboxes_meta)

    async def run_vision(
        self,
        *,
        client_id: str,
        include_matting: bool = False,
        model: str | None = None,
        matting_model: str | None = None,
    ) -> VisionBodyResponse:
        stored = await run_vision_pipeline(
            client_id=client_id,
            include_matting=include_matting,
            model=model,
            matting_model=matting_model,
            settings=self.settings,
            sapiens_client=self.sapiens,
        )
        return VisionBodyResponse(
            client_id=stored["client_id"],
            include_matting=stored["include_matting"],
            vision_model=stored["vision_model"],
            matting_model=stored["matting_model"],
            front_aligned_path=stored["source"]["front_aligned"],
            side_aligned_path=stored["source"]["side_aligned"],
            result_path=stored["result_path"],
            stages_order=stored["stages_order"],
            stages=stored["stages"],
            files=stored["files"],
        )
