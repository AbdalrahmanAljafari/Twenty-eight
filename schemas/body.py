from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateBodyResponse(BaseModel):
    message: str = "Body pipeline not connected yet"
    height_cm: float = Field(..., description="Submitted height in centimeters")
    age: int = Field(..., description="Submitted age in years")
    front_image_size_bytes: int
    side_image_size_bytes: int
