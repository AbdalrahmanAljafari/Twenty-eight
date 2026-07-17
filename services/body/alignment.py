from __future__ import annotations

from pathlib import Path

from PIL import Image


class Alignment:
    def __init__(self, canvas_size: int = 2000) -> None:
        self.canvas_width = int(canvas_size)
        self.canvas_height = int(canvas_size)
        self.canvas_size = (self.canvas_width, self.canvas_height)
        self.canvas_center_x = self.canvas_width / 2.0
        self.target_feet_y = self.canvas_height - 1

    def _resize_canvas_if_needed(self, canvas: Image.Image) -> Image.Image:
        if canvas.size != self.canvas_size:
            return canvas.resize(self.canvas_size, Image.LANCZOS)
        return canvas

    def align_single(
        self,
        person_image_path: str | Path,
        canvas_path: str | Path,
        output_path: str | Path,
    ) -> dict[str, object]:
        """Paste an opaque cropped/scaled person onto the canvas.

        After Sapiens bbox crop, the whole person image is the subject, so we
        center horizontally and pin the bottom edge to the canvas floor.
        """
        canvas_file = Path(canvas_path)
        person_file = Path(person_image_path)

        if not canvas_file.exists():
            raise FileNotFoundError(f"Canvas image not found: {canvas_path}")

        if not person_file.exists():
            raise FileNotFoundError(f"Person image not found: {person_image_path}")

        canvas = Image.open(canvas_file).convert("RGB")
        canvas = self._resize_canvas_if_needed(canvas)

        person = Image.open(person_file).convert("RGB")
        person_width, person_height = person.size

        # Full image bounds = person (already cropped by Sapiens bbox).
        body_center_x = person_width / 2.0
        feet_y = person_height - 1

        shift_x = int(self.canvas_center_x - body_center_x)
        shift_y = int(self.target_feet_y - feet_y)

        x1_src, y1_src = 0, 0
        x2_src, y2_src = person_width, person_height

        x1_dst = shift_x
        y1_dst = shift_y
        x2_dst = shift_x + person_width
        y2_dst = shift_y + person_height

        if x1_dst < 0:
            x1_src -= x1_dst
            x1_dst = 0
        if y1_dst < 0:
            y1_src -= y1_dst
            y1_dst = 0
        if x2_dst > self.canvas_width:
            x2_src -= x2_dst - self.canvas_width
            x2_dst = self.canvas_width
        if y2_dst > self.canvas_height:
            y2_src -= y2_dst - self.canvas_height
            y2_dst = self.canvas_height

        x1_src = max(0, x1_src)
        y1_src = max(0, y1_src)
        x2_src = min(person_width, x2_src)
        y2_src = min(person_height, y2_src)

        if x1_src >= x2_src or y1_src >= y2_src:
            raise ValueError("Aligned image falls completely outside the canvas")

        cropped_person = person.crop((x1_src, y1_src, x2_src, y2_src))
        canvas.paste(cropped_person, (x1_dst, y1_dst))

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_file)

        return {
            "saved_image_path": str(output_file),
            "person_size": {"width": person_width, "height": person_height},
            "paste_position": {"x": x1_dst, "y": y1_dst},
            "canvas_size": {
                "width": self.canvas_width,
                "height": self.canvas_height,
            },
        }
