from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path

from PIL import Image

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def guess_mime_type(path: Path, image_bytes: bytes | None = None) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type:
        return mime_type

    if image_bytes:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return Image.MIME.get(image.format, "image/jpeg")

    return "image/jpeg"


def read_image_bytes(source: Path | bytes) -> bytes:
    if isinstance(source, bytes):
        return source
    return Path(source).read_bytes()


def load_image(source: Path | bytes) -> Image.Image:
    image_bytes = read_image_bytes(source)
    return Image.open(io.BytesIO(image_bytes))


def get_image_size(source: Path | bytes) -> tuple[int, int]:
    with load_image(source) as image:
        return image.size


def to_data_uri(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def to_data_uri_from_source(source: Path | bytes) -> str:
    image_bytes = read_image_bytes(source)
    mime_type = guess_mime_type(Path("image.jpg"), image_bytes)
    if isinstance(source, Path):
        mime_type = guess_mime_type(source, image_bytes)
    return to_data_uri(image_bytes, mime_type)


def data_uri_to_bytes(data_uri: str) -> tuple[bytes, str]:
    if not data_uri.startswith("data:"):
        raise ValueError("Expected a base64 data URI")

    header, encoded = data_uri.split(",", 1)
    mime_type = header.removeprefix("data:").split(";")[0] or "image/png"
    return base64.b64decode(encoded), mime_type
