from functools import lru_cache

from fastapi import APIRouter, Form, HTTPException

from clients.openrouter import OpenRouterClient
from clients.sapiens import SapiensClient, SapiensError
from config.settings import get_settings
from schemas.body import VisionBodyResponse
from services.body import BodyService

router = APIRouter(prefix="/body", tags=["body"])


@lru_cache
def get_body_service() -> BodyService:
    settings = get_settings()
    return BodyService(
        settings=settings,
        client=OpenRouterClient(settings),
        sapiens_client=SapiensClient(settings),
    )


@router.post("/vision", response_model=VisionBodyResponse)
async def body_vision(
    client_id: str = Form(..., description="Client folder that already has Align/03_canvas outputs"),
    include_matting: bool = Form(
        False,
        description="If true, run POST /matting after pose→seg→normal",
    ),
    model: str | None = Form(
        None,
        description="Sapiens model for pose/seg/normal (default from SAPIENS_VISION_MODEL)",
    ),
    matting_model: str | None = Form(
        None,
        description="Sapiens model for matting (default from SAPIENS_MATTING_MODEL, usually 1b)",
    ),
) -> VisionBodyResponse:
    service = get_body_service()
    try:
        return await service.run_vision(
            client_id=client_id,
            include_matting=include_matting,
            model=model,
            matting_model=matting_model,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SapiensError as error:
        raise HTTPException(status_code=error.status_code or 502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
