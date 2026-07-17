from functools import lru_cache
import json

from fastapi import APIRouter, Form, HTTPException

from clients.openrouter import OpenRouterClient
from clients.sapiens import SapiensClient, SapiensError
from config.settings import get_settings
from schemas.body import StandardizeBodyResponse
from services.body import BodyService

router = APIRouter(prefix="/body", tags=["body"])

MIN_HEIGHT_CM = 50.0
MAX_HEIGHT_CM = 300.0


@lru_cache
def get_body_service() -> BodyService:
    settings = get_settings()
    return BodyService(
        settings=settings,
        client=OpenRouterClient(settings),
        sapiens_client=SapiensClient(settings),
    )


def _parse_optional_bbox_json(raw: str | None, field_name: str) -> dict | None:
    if raw is None or not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be valid JSON",
        ) from error
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a JSON object")
    return payload


@router.post("/standardize", response_model=StandardizeBodyResponse)
async def standardize_body(
    client_id: str = Form(..., description="Client folder that already has Apose outputs"),
    front_bbox: str | None = Form(
        None,
        description="Optional JSON bbox. If omitted, Sapiens /api/segmentation is called.",
    ),
    side_bbox: str | None = Form(
        None,
        description="Optional JSON bbox. If omitted, Sapiens /api/segmentation is called.",
    ),
    height_cm: float | None = Form(
        None,
        description="Optional override; defaults to height from Apose result.json",
    ),
) -> StandardizeBodyResponse:
    if height_cm is not None and (height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM):
        raise HTTPException(
            status_code=400,
            detail=f"height_cm must be between {MIN_HEIGHT_CM} and {MAX_HEIGHT_CM}",
        )

    front_bbox_obj = _parse_optional_bbox_json(front_bbox, "front_bbox")
    side_bbox_obj = _parse_optional_bbox_json(side_bbox, "side_bbox")
    if (front_bbox_obj is None) ^ (side_bbox_obj is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both front_bbox and side_bbox, or omit both to use Sapiens",
        )

    service = get_body_service()

    try:
        return await service.standardize_body(
            client_id=client_id,
            front_bbox=front_bbox_obj,
            side_bbox=side_bbox_obj,
            height_cm=height_cm,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SapiensError as error:
        raise HTTPException(status_code=error.status_code or 502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
