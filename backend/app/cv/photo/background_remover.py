"""Background Remover CV tool (S3-01).

Uses rembg (U2-Net) for background removal with 4 background modes.
Falls back to GrabCut if rembg unavailable.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Parse hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


def _grabcut_remove(image_bytes: bytes) -> tuple[Any, str]:
    """Remove background using OpenCV GrabCut. Returns (RGBA PIL Image, 'grabcut')."""
    import cv2

    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    mask: Any = np.zeros((h, w), np.uint8)
    bgd_model: Any = np.zeros((1, 65), np.float64)
    fgd_model: Any = np.zeros((1, 65), np.float64)
    margin = min(h, w) // 8
    rect = (margin, margin, w - margin * 2, h - margin * 2)
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    mask2: Any = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
    rgba: Any = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    rgba[:, :, 3] = mask2
    return Image.fromarray(rgba), "grabcut"


class BackgroundRemover:
    """Remove background from images with configurable replacement modes."""

    def process(
        self,
        image_bytes: bytes,
        bg_mode: str = "transparent",
        bg_color_hex: str = "#FFFFFF",
        bg_blur_radius: int = 21,
    ) -> dict[str, Any]:
        """Run background removal pipeline. Returns result dict with base64 image."""
        # Step 1: Remove background → RGBA
        rgba_pil: Any
        method: str
        try:
            from rembg import remove as rembg_remove

            rgba_bytes = rembg_remove(image_bytes)
            rgba_pil = Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")
            method = "u2net"
        except (ImportError, Exception):
            rgba_pil, method = _grabcut_remove(image_bytes)

        width_px, height_px = rgba_pil.size

        # Step 2: Apply background mode
        output_pil: Any
        output_format: str

        if bg_mode == "transparent":
            output_pil = rgba_pil
            output_format = "png"

        elif bg_mode == "white":
            background = Image.new("RGB", rgba_pil.size, (255, 255, 255))
            background.paste(rgba_pil, mask=rgba_pil.split()[3])
            output_pil = background
            output_format = "jpeg"

        elif bg_mode == "color":
            try:
                rgb = _hex_to_rgb(bg_color_hex)
            except (ValueError, IndexError):
                rgb = (255, 255, 255)
            background = Image.new("RGB", rgba_pil.size, rgb)
            background.paste(rgba_pil, mask=rgba_pil.split()[3])
            output_pil = background
            output_format = "jpeg"

        elif bg_mode == "blur":
            import cv2

            orig_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            orig_arr: Any = np.array(orig_pil)
            blur_radius = bg_blur_radius if bg_blur_radius % 2 == 1 else bg_blur_radius + 1
            blurred_arr: Any = cv2.GaussianBlur(orig_arr, (blur_radius, blur_radius), 0)
            blurred_pil = Image.fromarray(blurred_arr).convert("RGBA")
            blurred_pil.paste(rgba_pil, mask=rgba_pil.split()[3])
            output_pil = blurred_pil.convert("RGB")
            output_format = "jpeg"

        else:
            # Default to transparent for unknown modes
            output_pil = rgba_pil
            output_format = "png"

        # Encode to base64
        buf = io.BytesIO()
        if output_format == "png":
            output_pil.save(buf, format="PNG")
        else:
            output_pil.save(buf, format="JPEG", quality=92)
        encoded = base64.b64encode(buf.getvalue()).decode()

        return {
            "result_image_b64": encoded,
            "format": output_format,
            "method": method,
            "background_mode": bg_mode,
            "width_px": width_px,
            "height_px": height_px,
        }

    def process_bulk(
        self,
        images_bytes: list[bytes],
        bg_mode: str = "transparent",
        bg_color_hex: str = "#FFFFFF",
    ) -> list[dict[str, Any]]:
        """Process multiple images sequentially. Returns list of result dicts."""
        results: list[dict[str, Any]] = []
        for image_bytes in images_bytes:
            result = self.process(image_bytes, bg_mode=bg_mode, bg_color_hex=bg_color_hex)
            results.append(result)
        return results
