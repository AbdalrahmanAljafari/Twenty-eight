from __future__ import annotations

from dataclasses import dataclass

from utils.image import get_image_size, read_image_bytes

MAX_IMAGE_BYTES = 15 * 1024 * 1024
FACE_INPUT_SIZE = 512


class InputValidationError(ValueError):
    pass


@dataclass
class InputValidationResult:
    width: int
    height: int
    size_bytes: int


def validate_image_input(source: bytes | str) -> InputValidationResult:
    image_bytes = read_image_bytes(source)
    size_bytes = len(image_bytes)

    if size_bytes == 0:
        raise InputValidationError("Uploaded image is empty")
    if size_bytes > MAX_IMAGE_BYTES:
        raise InputValidationError("Uploaded image exceeds 15MB limit")

    width, height = get_image_size(image_bytes)

    if width != FACE_INPUT_SIZE or height != FACE_INPUT_SIZE:
        raise InputValidationError(
            f"Face image must be {FACE_INPUT_SIZE}x{FACE_INPUT_SIZE} pixels, "
            f"got {width}x{height}"
        )

    return InputValidationResult(width=width, height=height, size_bytes=size_bytes)
