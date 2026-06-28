"""Signature Extractor CV tool (S2-04).

Isolates signatures from document images.
Output: PNG with transparent background per signature, ZIP of all.
"""

from __future__ import annotations

import io
from typing import Any
import zipfile

import cv2
import numpy as np
from PIL import Image


class SignatureExtractor:
    """Detect and extract signatures from document images."""

    # Signature heuristics
    _MIN_AREA = 500
    _MAX_AREA_RATIO = 0.60  # Max fraction of total image area
    _MIN_ASPECT = 0.5
    _MAX_ASPECT = 10.0
    _STROKE_DENSITY_MIN = 0.02  # Minimum ink density within bounding box

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Detect and extract all signatures from a document image.

        Returns:
            result dict with signatures list (each has bbox, image_b64, confidence).

        """
        import base64

        img = self._load(image_bytes)
        h_img, w_img = img.shape[:2]
        total_area = h_img * w_img

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = self._binarize(gray)
        sig_regions = self._find_signature_regions(binary, total_area)

        signatures: list[dict[str, Any]] = []
        for x, y, w, h in sig_regions:
            region = img[y : y + h, x : x + w]
            # Create transparent PNG
            rgba = cv2.cvtColor(region, cv2.COLOR_BGR2BGRA)
            # Make white background transparent
            mask = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            _, mask_bin = cv2.threshold(mask, 240, 255, cv2.THRESH_BINARY)
            rgba[:, :, 3] = cv2.bitwise_not(mask_bin)

            pil = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

            # Confidence based on stroke density
            region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            _, ink = cv2.threshold(region_gray, 128, 255, cv2.THRESH_BINARY_INV)
            density = float(np.count_nonzero(ink)) / (w * h)
            confidence = min(100, int(density * 1000))

            signatures.append(
                {
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "image_b64": b64,
                    "format": "png",
                    "confidence": confidence,
                }
            )

        return {
            "signatures": signatures,
            "signature_count": len(signatures),
            "image_width": w_img,
            "image_height": h_img,
        }

    def to_zip(self, result: dict[str, Any]) -> bytes:
        """Package all signature PNGs into a ZIP archive."""
        import base64

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, sig in enumerate(result.get("signatures", []), 1):
                png_bytes = base64.b64decode(sig["image_b64"])
                zf.writestr(f"signature_{i:03d}.png", png_bytes)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load(image_bytes: bytes) -> Any:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        return img

    @staticmethod
    def _binarize(gray: Any) -> Any:
        """Adaptive threshold for robust signature detection."""
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def _find_signature_regions(
        self,
        binary: Any,
        total_area: int,
    ) -> list[tuple[int, int, int, int]]:
        """Find regions that look like signatures based on morphological features."""
        # Dilate to connect signature strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 5))
        dilated = cv2.dilate(binary, kernel, iterations=3)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        sig_regions: list[tuple[int, int, int, int]] = []
        for c in contours:
            bx, by, bw, bh = cv2.boundingRect(c)
            x, y, w, h = int(bx), int(by), int(bw), int(bh)
            area = w * h
            if area < self._MIN_AREA:
                continue
            if area / total_area > self._MAX_AREA_RATIO:
                continue
            aspect = w / max(h, 1)
            if not (self._MIN_ASPECT <= aspect <= self._MAX_ASPECT):
                continue
            # Check stroke density in original binary
            region_bin = binary[y : y + h, x : x + w]
            density = float(np.count_nonzero(region_bin)) / area
            if density < self._STROKE_DENSITY_MIN:
                continue
            sig_regions.append((x, y, w, h))

        # Sort left-to-right, top-to-bottom
        sig_regions.sort(key=lambda r: (r[1], r[0]))
        return sig_regions
