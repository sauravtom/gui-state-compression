from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple


def create_placeholder_screenshot(path: str | Path, label: str, size: Tuple[int, int] = (960, 640)) -> str:
    """Create a deterministic placeholder screenshot for synthetic benchmark logs."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw

        image = Image.new("RGB", size, color=(248, 249, 251))
        draw = ImageDraw.Draw(image)
        draw.rectangle((32, 32, size[0] - 32, size[1] - 32), outline=(70, 82, 102), width=3)
        draw.text((56, 58), label[:120], fill=(26, 32, 44))
        image.save(path)
    except Exception:
        path.write_text(f"placeholder screenshot: {label}\n", encoding="utf-8")
    return str(path)


def image_changed_bbox(prev_path: Optional[str], curr_path: Optional[str], threshold: int = 20) -> Optional[list[int]]:
    if not prev_path or not curr_path:
        return None
    try:
        from PIL import Image, ImageChops

        prev = Image.open(prev_path).convert("RGB")
        curr = Image.open(curr_path).convert("RGB")
        if prev.size != curr.size:
            return [0, 0, curr.size[0], curr.size[1]]
        diff = ImageChops.difference(prev, curr)
        mask = diff.convert("L").point(lambda pixel: 255 if pixel > threshold else 0)
        bbox = mask.getbbox()
        if bbox is None:
            return None
        return [int(coord) for coord in bbox]
    except Exception:
        return None
