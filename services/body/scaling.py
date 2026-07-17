from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


def normalize_bbox(bbox: dict[str, Any]) -> dict[str, int]:
    """Normalize common bbox key styles into x_min/y_min/x_max/y_max/height."""
    if {"x_min", "y_min", "x_max", "y_max"} <= bbox.keys():
        x_min = int(bbox["x_min"])
        y_min = int(bbox["y_min"])
        x_max = int(bbox["x_max"])
        y_max = int(bbox["y_max"])
    elif {"x1", "y1", "x2", "y2"} <= bbox.keys():
        x_min = int(bbox["x1"])
        y_min = int(bbox["y1"])
        x_max = int(bbox["x2"])
        y_max = int(bbox["y2"])
    elif {"left", "top", "right", "bottom"} <= bbox.keys():
        x_min = int(bbox["left"])
        y_min = int(bbox["top"])
        x_max = int(bbox["right"])
        y_max = int(bbox["bottom"])
    else:
        raise ValueError(
            "bbox must include x_min/y_min/x_max/y_max "
            "(or x1/y1/x2/y2, or left/top/right/bottom)"
        )

    if x_max < x_min or y_max < y_min:
        raise ValueError("Invalid bbox: max is less than min")

    height = int(bbox["height"]) if "height" in bbox else (y_max - y_min + 1)
    width = int(bbox["width"]) if "width" in bbox else (x_max - x_min + 1)

    if height <= 0 or width <= 0:
        raise ValueError("Invalid bbox dimensions")

    return {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "width": width,
        "height": height,
    }


class Scaling:
    def __init__(self, pixels_per_cm: float = 10.0, max_canvas_height: int = 2000) -> None:
        self.pixels_per_cm = pixels_per_cm
        self.max_canvas_height = max_canvas_height

    def crop_to_bbox(
        self,
        image_path: str | Path,
        bbox: dict[str, Any],
        output_path: str | Path,
    ) -> dict[str, Any]:
        input_path = Path(image_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        norm = normalize_bbox(bbox)
        image = Image.open(input_path).convert("RGB")
        original_width, original_height = image.size

        cropped = image.crop(
            (
                norm["x_min"],
                norm["y_min"],
                norm["x_max"] + 1,
                norm["y_max"] + 1,
            )
        )
        crop_width, crop_height = cropped.size

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output_file)

        return {
            "saved_image_path": str(output_file),
            "bbox": norm,
            "original_size": {"width": original_width, "height": original_height},
            "cropped_size": {"width": crop_width, "height": crop_height},
        }

    def scale_to_target_height(
        self,
        image_path: str | Path,
        real_height_cm: float,
        output_path: str | Path,
        *,
        body_height_px: float | None = None,
    ) -> dict[str, Any]:
        input_path = Path(image_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if real_height_cm <= 0:
            raise ValueError("Invalid real height (cm)")

        image = Image.open(input_path).convert("RGB")
        original_width, original_height = image.size

        measured_height = float(body_height_px) if body_height_px is not None else float(original_height)
        if measured_height <= 0:
            raise ValueError("Invalid body height in pixels")

        target_height_px = real_height_cm * self.pixels_per_cm
        scale_factor = target_height_px / measured_height

        scaled_width = max(1, round(original_width * scale_factor))
        scaled_height = max(1, round(original_height * scale_factor))
        scaled_image = image.resize((scaled_width, scaled_height), Image.LANCZOS)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        scaled_image.save(output_file)

        error_px = abs(target_height_px - scaled_height)

        return {
            "saved_image_path": str(output_file),
            "scale_factor": scale_factor,
            "original_size": {"width": original_width, "height": original_height},
            "scaled_size": {"width": scaled_width, "height": scaled_height},
            "target_body_height_px": target_height_px,
            "real_height_cm": real_height_cm,
            "pixels_per_cm": self.pixels_per_cm,
            "validation": {
                "expected_height_px": target_height_px,
                "actual_height_px": scaled_height,
                "error_px": error_px,
            },
        }

    def crop_and_scale(
        self,
        image_path: str | Path,
        bbox: dict[str, Any],
        real_height_cm: float,
        crop_output_path: str | Path,
        scale_output_path: str | Path,
    ) -> dict[str, Any]:
        """Crop then scale, saving each stage to its own path."""
        crop_meta = self.crop_to_bbox(image_path, bbox, crop_output_path)
        scale_meta = self.scale_to_target_height(
            crop_meta["saved_image_path"],
            real_height_cm,
            scale_output_path,
            body_height_px=crop_meta["cropped_size"]["height"],
        )
        return {
            "crop": crop_meta,
            "scale": scale_meta,
            "bbox": crop_meta["bbox"],
        }
