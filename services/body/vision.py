from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clients.sapiens import SapiensClient, VisionStage
from config.settings import PROJECT_ROOT, Settings, get_settings

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BODY_OUTPUT_DIRNAME = "body"
ALIGN_OUTPUT_DIRNAME = "Align"
CANVAS_DIRNAME = "03_canvas"
VISION_OUTPUT_DIRNAME = "Vision"

STAGE_DIRS: dict[VisionStage, str] = {
    "pose": "01_pose",
    "seg": "02_seg",
    "normal": "03_normal",
    "matting": "04_matting",
}


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def resolve_aligned_paths(client_id: str) -> tuple[Path, Path]:
    canvas_dir = (
        OUTPUTS_DIR / client_id / BODY_OUTPUT_DIRNAME / ALIGN_OUTPUT_DIRNAME / CANVAS_DIRNAME
    )
    if not canvas_dir.exists():
        raise FileNotFoundError(
            f"Aligned canvas folder not found for client_id={client_id}: {canvas_dir}"
        )

    front_matches = sorted(canvas_dir.glob("front_aligned.*"))
    side_matches = sorted(canvas_dir.glob("side_aligned.*"))
    if not front_matches:
        raise FileNotFoundError(f"front_aligned image not found for client_id={client_id}")
    if not side_matches:
        raise FileNotFoundError(f"side_aligned image not found for client_id={client_id}")
    return front_matches[0], side_matches[0]


def _save_stage_outputs(
    *,
    stage_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    stage_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    for view in ("front", "side"):
        view_payload = payload[view]
        visual_b64 = view_payload["visualization_png_base64"]
        visual_path = stage_dir / f"{view}_visual.png"
        visual_path.write_bytes(base64.b64decode(visual_b64))
        files[f"{view}_visual"] = _rel(visual_path)

        data_path = stage_dir / f"{view}_data.json"
        data_path.write_text(
            json.dumps(view_payload.get("data", {}), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        files[f"{view}_data"] = _rel(data_path)

    meta_path = stage_dir / "result.json"
    meta_payload = {
        "model": payload.get("model"),
        "image_size": {
            "front": payload["front"].get("image_size"),
            "side": payload["side"].get("image_size"),
        },
        "files": files,
    }
    meta_path.write_text(
        json.dumps(meta_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["result"] = _rel(meta_path)
    return files


async def run_vision_pipeline(
    *,
    client_id: str,
    include_matting: bool = False,
    model: str | None = None,
    matting_model: str | None = None,
    settings: Settings | None = None,
    sapiens_client: SapiensClient | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    sapiens = sapiens_client or SapiensClient(cfg)

    front_path, side_path = resolve_aligned_paths(client_id)
    vision_model = model or cfg.sapiens_vision_model
    matt_model = matting_model or cfg.sapiens_matting_model

    vision_dir = OUTPUTS_DIR / client_id / BODY_OUTPUT_DIRNAME / VISION_OUTPUT_DIRNAME
    vision_dir.mkdir(parents=True, exist_ok=True)

    stages: list[VisionStage] = ["pose", "seg", "normal"]
    if include_matting:
        stages.append("matting")

    stage_results: dict[str, Any] = {}
    all_files: dict[str, Any] = {}

    for stage in stages:
        stage_model = matt_model if stage == "matting" else vision_model
        payload = await sapiens.vision_stage(
            stage,
            front_path,
            side_path,
            model=stage_model,
            front_filename=front_path.name,
            side_filename=side_path.name,
        )
        stage_dir = vision_dir / STAGE_DIRS[stage]
        files = _save_stage_outputs(stage_dir=stage_dir, payload=payload)
        stage_results[stage] = {
            "model": payload.get("model", stage_model),
            "directory": _rel(stage_dir),
            "files": files,
            "image_size": {
                "front": payload["front"].get("image_size"),
                "side": payload["side"].get("image_size"),
            },
        }
        all_files[stage] = files

    result_path = vision_dir / "result.json"
    result_payload = {
        "client_id": client_id,
        "feature": BODY_OUTPUT_DIRNAME,
        "stage": VISION_OUTPUT_DIRNAME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "include_matting": include_matting,
        "vision_model": vision_model,
        "matting_model": matt_model if include_matting else None,
        "source": {
            "front_aligned": _rel(front_path),
            "side_aligned": _rel(side_path),
        },
        "stages_order": stages,
        "stages": stage_results,
        "files": all_files,
    }
    result_path.write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "client_id": client_id,
        "include_matting": include_matting,
        "vision_model": vision_model,
        "matting_model": matt_model if include_matting else None,
        "result_path": _rel(result_path),
        "source": result_payload["source"],
        "stages_order": stages,
        "stages": stage_results,
        "files": all_files,
    }
