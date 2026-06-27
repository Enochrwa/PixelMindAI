"""Background Remover CV tool.

Uses rembg (U2-Net) for background removal. Falls back to GrabCut if rembg unavailable.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image


class BackgroundRemover:
    """Remove background from images."""

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Remove image background. Returns base64-encoded PNG result."""
        import base64

        try:
            from rembg import remove

            output_bytes = remove(image_bytes)
            encoded = base64.b64encode(output_bytes).decode()
            return {
                "result_image_b64": encoded,
                "format": "png",
                "method": "u2net",
                "background_removed": True,
            }
        except ImportError:
            # Fallback: GrabCut with OpenCV
            import cv2

            pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            h, w = img.shape[:2]
            mask = np.zeros((h, w), np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            margin = min(h, w) // 8
            rect = (margin, margin, w - margin * 2, h - margin * 2)
            cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
            rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
            rgba[:, :, 3] = mask2
            result_pil = Image.fromarray(rgba)
            buf = io.BytesIO()
            result_pil.save(buf, format="PNG")
            encoded = base64.b64encode(buf.getvalue()).decode()
            return {
                "result_image_b64": encoded,
                "format": "png",
                "method": "grabcut",
                "background_removed": True,
            }
