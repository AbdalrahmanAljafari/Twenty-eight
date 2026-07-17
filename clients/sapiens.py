from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from config.settings import Settings, get_settings


class SapiensError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SapiensClient:
    def __init__(self, settings: Settings | None = None, timeout: float = 180.0) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout

    @property
    def segmentation_url(self) -> str:
        base = self.settings.sapiens_base_url.rstrip("/")
        path = self.settings.sapiens_segmentation_path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    @property
    def health_url(self) -> str:
        return f"{self.settings.sapiens_base_url.rstrip('/')}/health"

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.health_url)
        if response.status_code >= 400:
            raise SapiensError(
                f"Sapiens health check failed: {response.text}",
                status_code=response.status_code,
            )
        return response.json()

    async def segment(
        self,
        front_image: bytes | Path,
        side_image: bytes | Path,
        *,
        front_filename: str = "front_Apose.png",
        side_filename: str = "side_Apose.png",
        include_visual: bool = False,
    ) -> dict[str, Any]:
        front_bytes, front_name = self._read_image(front_image, front_filename)
        side_bytes, side_name = self._read_image(side_image, side_filename)

        files = {
            "front_image": (front_name, front_bytes, self._guess_mime(front_name)),
            "side_image": (side_name, side_bytes, self._guess_mime(side_name)),
        }
        data = {"include_visual": "true"} if include_visual else None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.segmentation_url, files=files, data=data)

        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                detail = str(payload.get("detail", payload))
            except Exception:
                payload = detail
            raise SapiensError(
                f"Sapiens segmentation failed: {detail}",
                status_code=response.status_code,
                payload=payload,
            )

        payload = response.json()
        self._validate_segmentation_payload(payload)
        return payload

    def extract_bboxes(self, segmentation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        front_bbox = segmentation["front"]["bbox"]
        side_bbox = segmentation["side"]["bbox"]
        return front_bbox, side_bbox

    @staticmethod
    def _read_image(source: bytes | Path, default_name: str) -> tuple[bytes, str]:
        if isinstance(source, bytes):
            return source, default_name
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        return path.read_bytes(), path.name

    @staticmethod
    def _guess_mime(filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(".png"):
            return "image/png"
        if lower.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        if lower.endswith(".webp"):
            return "image/webp"
        return "application/octet-stream"

    @staticmethod
    def _validate_segmentation_payload(payload: dict[str, Any]) -> None:
        for view in ("front", "side"):
            if view not in payload or not isinstance(payload[view], dict):
                raise SapiensError(f"Sapiens response missing '{view}' object")
            bbox = payload[view].get("bbox")
            if not isinstance(bbox, dict):
                raise SapiensError(f"Sapiens response missing '{view}.bbox'")
            required = {"x_min", "y_min", "x_max", "y_max"}
            missing = required - bbox.keys()
            if missing:
                raise SapiensError(
                    f"Sapiens '{view}.bbox' missing keys: {', '.join(sorted(missing))}"
                )
