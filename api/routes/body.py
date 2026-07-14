from functools import lru_cache

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from clients.openrouter import OpenRouterClient
from config.settings import Provider, get_settings
from schemas.body import GenerateBodyResponse
from services.body import BodyService

router = APIRouter(prefix="/body", tags=["body"])

MIN_HEIGHT_CM = 50.0
MAX_HEIGHT_CM = 300.0
MIN_AGE = 1
MAX_AGE = 120


@lru_cache
def get_body_service() -> BodyService:
    settings = get_settings()
    return BodyService(settings=settings, client=OpenRouterClient(settings))


@router.post("/generate", response_model=GenerateBodyResponse)
async def generate_body(
    front_image: UploadFile = File(..., description="Front body photo"),
    side_image: UploadFile = File(..., description="Side body photo"),
    height_cm: float = Form(..., description="Person height in centimeters"),
    age: int = Form(..., description="Person age in years"),
    client_id: str | None = Form(
        None,
        description="Existing client folder ID (usually from face generation)",
    ),
    generation_provider: Provider | None = Form(None),
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

    service = get_body_service()

    try:
        return await service.generate_body_apose(
            front_bytes,
            side_bytes,
            height_cm=height_cm,
            age=age,
            client_id=client_id,
            generation_provider=generation_provider,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
