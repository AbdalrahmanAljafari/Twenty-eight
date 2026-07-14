from __future__ import annotations

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
