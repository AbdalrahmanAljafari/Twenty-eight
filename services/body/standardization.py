from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import PROJECT_ROOT, Settings, get_settings
from services.body.alignment import Alignment
from services.body.scaling import Scaling

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BODY_OUTPUT_DIRNAME = "body"
ALIGN_OUTPUT_DIRNAME = "Align"
CROP_DIRNAME = "01_crop"
SCALE_DIRNAME = "02_scale"
CANVAS_DIRNAME = "03_canvas"


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _process_view(
    *,
    view: str,
    image_path: Path,
    bbox: dict[str, Any],
    height_cm: float,
    align_dir: Path,
    scaling: Scaling,
    alignment: Alignment,
    canvas_path: Path,
) -> dict[str, Any]:
    crop_path = align_dir / CROP_DIRNAME / f"{view}_crop.png"
    scale_path = align_dir / SCALE_DIRNAME / f"{view}_scaled.png"
    canvas_out_path = align_dir / CANVAS_DIRNAME / f"{view}_aligned.png"

    crop_meta = scaling.crop_to_bbox(image_path, bbox, crop_path)
    scale_meta = scaling.scale_to_target_height(
        crop_meta["saved_image_path"],
        height_cm,
        scale_path,
        body_height_px=crop_meta["cropped_size"]["height"],
    )
    align_meta = alignment.align_single(
        scale_meta["saved_image_path"],
        canvas_path,
        canvas_out_path,
    )

    return {
        "bbox": crop_meta["bbox"],
        "crop": {
            **crop_meta,
            "saved_image_path": _rel(Path(crop_meta["saved_image_path"])),
        },
        "scale": {
            **scale_meta,
            "saved_image_path": _rel(Path(scale_meta["saved_image_path"])),
        },
        "canvas": {
            **align_meta,
            "saved_image_path": _rel(Path(str(align_meta["saved_image_path"]))),
        },
    }


def run_standardization(
    *,
    client_id: str,
    front_image_path: str | Path,
    side_image_path: str | Path,
    front_bbox: dict[str, Any],
    side_bbox: dict[str, Any],
    height_cm: float,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Crop → scale → canvas for front/side; save every stage under Align/."""
    cfg = settings or get_settings()
    front_path = Path(front_image_path)
    side_path = Path(side_image_path)

    if not front_path.is_absolute():
        front_path = PROJECT_ROOT / front_path
    if not side_path.is_absolute():
        side_path = PROJECT_ROOT / side_path

    if not front_path.exists():
        raise FileNotFoundError(f"Front image not found: {front_path}")
    if not side_path.exists():
        raise FileNotFoundError(f"Side image not found: {side_path}")

    canvas_path = cfg.resolved_align_canvas_path
    if not canvas_path.exists():
        raise FileNotFoundError(f"Canvas image not found: {canvas_path}")

    align_dir = OUTPUTS_DIR / client_id / BODY_OUTPUT_DIRNAME / ALIGN_OUTPUT_DIRNAME
    (align_dir / CROP_DIRNAME).mkdir(parents=True, exist_ok=True)
    (align_dir / SCALE_DIRNAME).mkdir(parents=True, exist_ok=True)
    (align_dir / CANVAS_DIRNAME).mkdir(parents=True, exist_ok=True)

    scaling = Scaling(
        pixels_per_cm=cfg.align_pixels_per_cm,
        max_canvas_height=cfg.align_canvas_size,
    )
    alignment = Alignment(canvas_size=cfg.align_canvas_size)

    front_result = _process_view(
        view="front",
        image_path=front_path,
        bbox=front_bbox,
        height_cm=height_cm,
        align_dir=align_dir,
        scaling=scaling,
        alignment=alignment,
        canvas_path=canvas_path,
    )
    side_result = _process_view(
        view="side",
        image_path=side_path,
        bbox=side_bbox,
        height_cm=height_cm,
        align_dir=align_dir,
        scaling=scaling,
        alignment=alignment,
        canvas_path=canvas_path,
    )

    result_path = align_dir / "result.json"
    result_payload = {
        "client_id": client_id,
        "feature": BODY_OUTPUT_DIRNAME,
        "stage": ALIGN_OUTPUT_DIRNAME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "height_cm": height_cm,
        "pixels_per_cm": cfg.align_pixels_per_cm,
        "canvas_size": cfg.align_canvas_size,
        "canvas_path": _rel(canvas_path),
        "source": {
            "front": _rel(front_path),
            "side": _rel(side_path),
        },
        "views": {
            "front": front_result,
            "side": side_result,
        },
        "files": {
            "front_crop": front_result["crop"]["saved_image_path"],
            "side_crop": side_result["crop"]["saved_image_path"],
            "front_scaled": front_result["scale"]["saved_image_path"],
            "side_scaled": side_result["scale"]["saved_image_path"],
            "front_aligned": front_result["canvas"]["saved_image_path"],
            "side_aligned": side_result["canvas"]["saved_image_path"],
        },
    }
    result_path.write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "client_id": client_id,
        "result_path": _rel(result_path),
        "files": result_payload["files"],
        "views": result_payload["views"],
        "height_cm": height_cm,
        "pixels_per_cm": cfg.align_pixels_per_cm,
        "canvas_size": cfg.align_canvas_size,
    }
