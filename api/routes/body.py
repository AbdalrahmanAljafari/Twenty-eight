from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from schemas.body import GenerateBodyResponse

router = APIRouter(prefix="/body", tags=["body"])

MIN_HEIGHT_CM = 50.0
MAX_HEIGHT_CM = 300.0
MIN_AGE = 1
MAX_AGE = 120


@router.post("/generate", response_model=GenerateBodyResponse)
async def generate_body(
    front_image: UploadFile = File(..., description="Front body photo"),
    side_image: UploadFile = File(..., description="Side body photo"),
    height_cm: float = Form(..., description="Person height in centimeters"),
    age: int = Form(..., description="Person age in years"),
) -> GenerateBodyResponse:
    if not front_image.content_type or not front_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="front_image must be an image file")
    if not side_image.content_type or not side_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="side_image must be an image file")

    if height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM:
        raise HTTPException(
            status_code=400,
            detail=f"height_cm must be between {MIN_HEIGHT_CM} and {MAX_HEIGHT_CM}",
        )
    if age < MIN_AGE or age > MAX_AGE:
        raise HTTPException(
            status_code=400,
            detail=f"age must be between {MIN_AGE} and {MAX_AGE}",
        )

    front_bytes = await front_image.read()
    side_bytes = await side_image.read()

    if not front_bytes:
        raise HTTPException(status_code=400, detail="front_image is empty")
    if not side_bytes:
        raise HTTPException(status_code=400, detail="side_image is empty")

    return GenerateBodyResponse(
        height_cm=height_cm,
        age=age,
        front_image_size_bytes=len(front_bytes),
        side_image_size_bytes=len(side_bytes),
    )
