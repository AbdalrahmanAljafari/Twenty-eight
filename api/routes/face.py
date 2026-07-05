from functools import lru_cache

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from clients.openrouter import OpenRouterClient
from config.settings import Provider, get_settings
from schemas.responses import GenerateFaceResponse
from services.face import FaceService
from services.face.validation_input import InputValidationError

router = APIRouter(prefix="/face", tags=["face"])


@lru_cache
def get_face_service() -> FaceService:
    settings = get_settings()
    return FaceService(settings=settings, client=OpenRouterClient(settings))


@router.post("/generate", response_model=GenerateFaceResponse)
async def generate_face(
    image: UploadFile = File(...),
    extraction_provider: Provider | None = Form(None),
    generation_provider: Provider | None = Form(None),
    validation_provider: Provider | None = Form(None),
) -> GenerateFaceResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await image.read()
    service = get_face_service()

    try:
        return await service.generate_face_portrait(
            image_bytes,
            extraction_provider=extraction_provider,
            generation_provider=generation_provider,
            validation_provider=validation_provider,
        )
    except InputValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
