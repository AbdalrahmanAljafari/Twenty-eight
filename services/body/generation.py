from __future__ import annotations

from clients.openrouter import OpenRouterClient
from config.settings import PipelineProfile


async def generate_apose_image(
    image_source: bytes | str,
    prompt: str,
    profile: PipelineProfile,
    client: OpenRouterClient | None = None,
) -> tuple[bytes, str]:
    openrouter = client or OpenRouterClient()
    return await openrouter.generate_image(
        model=profile.generation_model,
        prompt=prompt,
        image_source=image_source,
    )
