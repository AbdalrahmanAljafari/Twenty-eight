from __future__ import annotations

from typing import Any

import httpx

from config.settings import Settings, get_settings
from utils.image import to_data_uri_from_source


class OpenRouterError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class OpenRouterClient:
    def __init__(self, settings: Settings | None = None, timeout: float = 180.0) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout

    @property
    def chat_url(self) -> str:
        return f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "HTTP-Referer": self.settings.openrouter_site_url,
            "X-Title": self.settings.openrouter_app_name,
            "Content-Type": "application/json",
        }

    def _build_user_message(
        self,
        prompt: str,
        image_source: bytes | str | None,
        reference_image_source: bytes | str | None = None,
    ) -> dict[str, Any]:
        if image_source is None and reference_image_source is None:
            return {"role": "user", "content": prompt}

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        for source in (reference_image_source, image_source):
            if source is None:
                continue
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": to_data_uri_from_source(source)},
                }
            )

        return {"role": "user", "content": content}

    async def chat_completion(
        self,
        *,
        model: str,
        prompt: str,
        image_source: bytes | str | None = None,
        reference_image_source: bytes | str | None = None,
        modalities: list[str] | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                self._build_user_message(prompt, image_source, reference_image_source)
            ],
        }

        if modalities:
            payload["modalities"] = modalities

        if extra_payload:
            payload.update(extra_payload)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.chat_url,
                headers=self._headers(),
                json=payload,
            )

        if response.status_code >= 400:
            raise OpenRouterError(
                f"OpenRouter request failed ({response.status_code}): {response.text}",
                status_code=response.status_code,
                payload=self._safe_json(response),
            )

        return response.json()

    async def analyze_image(
        self,
        *,
        model: str,
        prompt: str,
        image_source: bytes | str,
        reference_image_source: bytes | str | None = None,
    ) -> str:
        result = await self.chat_completion(
            model=model,
            prompt=prompt,
            image_source=image_source,
            reference_image_source=reference_image_source,
        )
        text = self.extract_text(result)
        if not text:
            raise OpenRouterError("OpenRouter returned no text for image analysis", payload=result)
        return text

    async def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        image_source: bytes | str,
    ) -> tuple[bytes, str]:
        result = await self.chat_completion(
            model=model,
            prompt=prompt,
            image_source=image_source,
            modalities=["image", "text"],
        )

        image_bytes, mime_type = self.extract_first_image(result)
        if image_bytes is None:
            raise OpenRouterError("OpenRouter returned no generated image", payload=result)

        return image_bytes, mime_type

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @classmethod
    def extract_text(cls, response: dict[str, Any]) -> str:
        choices = response.get("choices") or []
        if not choices:
            return ""

        message = choices[0].get("message") or {}
        content = message.get("content")

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
            return "\n".join(part for part in text_parts if part).strip()

        return ""

    @classmethod
    def extract_first_image(cls, response: dict[str, Any]) -> tuple[bytes | None, str]:
        choices = response.get("choices") or []
        if not choices:
            return None, "image/png"

        message = choices[0].get("message") or {}

        images = message.get("images") or []
        for image in images:
            parsed = cls._parse_image_entry(image)
            if parsed is not None:
                return parsed

        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "image_url":
                    parsed = cls._parse_image_url(part.get("image_url"))
                    if parsed is not None:
                        return parsed

        if isinstance(content, str) and content.startswith("data:image"):
            return cls._parse_data_uri(content)

        return None, "image/png"

    @classmethod
    def _parse_image_entry(cls, image: Any) -> tuple[bytes, str] | None:
        if not isinstance(image, dict):
            return None

        if "image_url" in image:
            return cls._parse_image_url(image.get("image_url"))

        if "url" in image and isinstance(image["url"], str):
            return cls._parse_data_uri(image["url"])

        return None

    @classmethod
    def _parse_image_url(cls, image_url: Any) -> tuple[bytes, str] | None:
        if not isinstance(image_url, dict):
            return None

        url = image_url.get("url")
        if not isinstance(url, str):
            return None

        return cls._parse_data_uri(url)

    @classmethod
    def _parse_data_uri(cls, data_uri: str) -> tuple[bytes, str] | None:
        if not data_uri.startswith("data:image"):
            return None

        from utils.image import data_uri_to_bytes

        try:
            image_bytes, mime_type = data_uri_to_bytes(data_uri)
        except ValueError:
            return None

        return image_bytes, mime_type
