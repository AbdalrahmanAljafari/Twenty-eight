from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateBodyResponse(BaseModel):
    message: str = "Body A-pose images generated"
    client_id: str
    height_cm: float = Field(..., description="Submitted height in centimeters")
    age: int = Field(..., description="Submitted age in years")
    front_image_size_bytes: int
    side_image_size_bytes: int
    front_apose_path: str
    side_apose_path: str
    front_apose_base64: str
    side_apose_base64: str
    result_path: str
    pipeline: dict[str, str] = Field(default_factory=dict)
    # Populated when run_standardize=true
    standardized: bool = False
    front_crop_path: str | None = None
    side_crop_path: str | None = None
    front_scaled_path: str | None = None
    side_scaled_path: str | None = None
    front_aligned_path: str | None = None
    side_aligned_path: str | None = None
    align_result_path: str | None = None
    sapiens_bboxes: dict[str, Any] | None = None


class StandardizeBodyResponse(BaseModel):
    message: str = "Body images standardized"
    client_id: str
    height_cm: float
    pixels_per_cm: float
    canvas_size: int
    front_crop_path: str
    side_crop_path: str
    front_scaled_path: str
    side_scaled_path: str
    front_aligned_path: str
    side_aligned_path: str
    result_path: str
    views: dict[str, Any] = Field(default_factory=dict)
    sapiens_bboxes: dict[str, Any] | None = None


class VisionBodyResponse(BaseModel):
    message: str = "Body vision pipeline completed"
    client_id: str
    include_matting: bool
    vision_model: str
    matting_model: str | None = None
    front_aligned_path: str
    side_aligned_path: str
    result_path: str
    stages_order: list[str] = Field(default_factory=list)
    stages: dict[str, Any] = Field(default_factory=dict)
    files: dict[str, Any] = Field(default_factory=dict)
