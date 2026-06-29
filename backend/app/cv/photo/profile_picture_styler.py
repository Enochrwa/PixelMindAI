"""AI Profile Picture Styler (S4-04).

Removes background and composites the subject onto 4 professional
background styles: Corporate, LinkedIn Studio, Creative, and Minimal.
"""

from __future__ import annotations

import base64
from collections.abc import Callable  # noqa: TC003 — used at runtime in cast()
import io
from typing import Any, cast

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------------------
# Background style generators
# ---------------------------------------------------------------------------


def _gradient(
    size: tuple[int, int], top_rgb: tuple[int, int, int], bot_rgb: tuple[int, int, int]
) -> Image.Image:
    """Generate a vertical linear gradient image."""
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for row in range(h):
        t = row / max(h - 1, 1)
        arr[row, :, 0] = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        arr[row, :, 1] = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        arr[row, :, 2] = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
    return Image.fromarray(arr, "RGB")


def _style_corporate(size: tuple[int, int]) -> Image.Image:
    """Professional grey-blue gradient — boardroom ready."""
    return _gradient(size, (74, 92, 117), (142, 158, 175))


def _style_linkedin(size: tuple[int, int]) -> Image.Image:
    """Warm studio gradient used in LinkedIn portraits."""
    return _gradient(size, (220, 215, 205), (170, 162, 150))


def _style_creative(size: tuple[int, int]) -> Image.Image:
    """Vibrant abstract colourful background."""
    w, h = size
    base = _gradient(size, (63, 94, 251), (252, 70, 107))
    # Add soft diagonal accent blobs
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse([w // 4, -h // 4, w, h // 2], fill=(255, 215, 0, 60))
    draw.ellipse([-w // 4, h // 2, w // 2, h + h // 4], fill=(0, 255, 200, 40))
    base_rgba = base.convert("RGBA")
    base_rgba = Image.alpha_composite(base_rgba, overlay)
    return base_rgba.convert("RGB")


def _style_minimal(size: tuple[int, int], colour_hex: str = "#F0F0F0") -> Image.Image:
    """Plain solid colour — elegant and distraction-free."""
    hex_clean = colour_hex.lstrip("#")
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
    except (ValueError, IndexError):
        r, g, b = 240, 240, 240
    return Image.new("RGB", size, (r, g, b))


_STYLE_BUILDERS = {
    "corporate": _style_corporate,
    "linkedin": _style_linkedin,
    "creative": _style_creative,
    "minimal": _style_minimal,
}


def _remove_background(image_bytes: bytes) -> Image.Image:
    """Remove background, returns RGBA image."""
    try:
        from rembg import remove as rembg_remove  # type: ignore[import-untyped,misc]

        rgba_bytes = rembg_remove(image_bytes)
        return Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")
    except Exception:
        # Fallback: GrabCut
        import cv2  # type: ignore[import-untyped,misc]

        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        h, w = img.shape[:2]
        mask: Any = np.zeros((h, w), np.uint8)
        bgd: Any = np.zeros((1, 65), np.float64)
        fgd: Any = np.zeros((1, 65), np.float64)
        m = min(h, w) // 8
        cv2.grabCut(img, mask, (m, m, w - m * 2, h - m * 2), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        mask2: Any = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
        rgba: Any = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        rgba[:, :, 3] = mask2
        return Image.fromarray(rgba)


def _composite(fg_rgba: Image.Image, bg_rgb: Image.Image) -> Image.Image:
    """Composite foreground RGBA onto background RGB."""
    result = bg_rgb.convert("RGBA")
    result.paste(fg_rgba, mask=fg_rgba.split()[3])
    return result.convert("RGB")


class ProfilePictureStyler:
    """Generate 4 professional-style profile pictures from one selfie."""

    def process(
        self,
        image_bytes: bytes,
        styles: list[str] | None = None,
        minimal_colour_hex: str = "#F0F0F0",
    ) -> dict[str, Any]:
        """Apply requested background styles and return base64-encoded variants."""
        requested_styles = styles if styles else list(_STYLE_BUILDERS.keys())
        requested_styles = [s for s in requested_styles if s in _STYLE_BUILDERS]
        if not requested_styles:
            requested_styles = list(_STYLE_BUILDERS.keys())

        fg_rgba = _remove_background(image_bytes)
        size = fg_rgba.size  # (W, H)

        results: list[dict[str, str]] = []

        for style_name in requested_styles:
            raw_builder = _STYLE_BUILDERS[style_name]
            if style_name == "minimal":
                builder_any = cast("Callable[..., Image.Image]", raw_builder)
                bg = builder_any(size, minimal_colour_hex)
            else:
                bg = cast("Callable[[tuple[int, int]], Image.Image]", raw_builder)(size)

            # Soft vignette for studio effect
            if style_name in {"corporate", "linkedin"}:
                bg_blur = bg.filter(ImageFilter.GaussianBlur(radius=2))
                bg = bg_blur

            output_pil = _composite(fg_rgba, bg)

            buf = io.BytesIO()
            output_pil.save(buf, format="JPEG", quality=93, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()

            results.append({"style_name": style_name, "result_image_b64": b64, "format": "jpeg"})

        return {
            "styles": results,
            "width": size[0],
            "height": size[1],
        }
