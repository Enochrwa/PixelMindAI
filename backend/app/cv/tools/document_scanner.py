"""Document Scanner CV tool (S2-03).

Phone photo of any document → clean, cropped, deskewed PDF.
Enhancement modes: original_enhanced, black_and_white, grayscale.
Multi-page: ZIP of photos → single multi-page PDF.
"""

from __future__ import annotations

import io
from typing import Any

import cv2
import numpy as np
from PIL import Image


class DocumentScanner:
    """Scan, crop, deskew and enhance document photos."""

    MODES = ("original_enhanced", "black_and_white", "grayscale")

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(
        self,
        image_bytes: bytes,
        mode: str = "original_enhanced",
    ) -> dict[str, Any]:
        """Scan a single document photo.

        Args:
            image_bytes: Raw image bytes.
            mode: Enhancement mode — 'original_enhanced', 'black_and_white', 'grayscale'.

        Returns:
            result dict with result_image_b64, mode, dimensions, quality_score.

        """
        import base64

        if mode not in self.MODES:
            mode = "original_enhanced"

        img = self._load(image_bytes)
        warped = self._perspective_crop(img)
        enhanced = self._enhance(warped, mode)

        # Encode output as JPEG base64
        pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=92)
        b64 = base64.b64encode(buf.getvalue()).decode()

        h, w = enhanced.shape[:2]
        return {
            "result_image_b64": b64,
            "format": "jpeg",
            "mode": mode,
            "width_px": w,
            "height_px": h,
            "quality_score": self._quality_score(enhanced),
        }

    def process_pdf(
        self,
        images_bytes: list[bytes],
        mode: str = "black_and_white",
    ) -> bytes:
        """Process multiple images and combine into a multi-page PDF.

        Args:
            images_bytes: List of raw image bytes (one per page).
            mode: Enhancement mode for all pages.

        Returns:
            PDF bytes.

        """
        pil_pages: list[Image.Image] = []
        for img_bytes in images_bytes:
            img = self._load(img_bytes)
            warped = self._perspective_crop(img)
            enhanced = self._enhance(warped, mode)
            pil_pages.append(Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)))

        if not pil_pages:
            return b""

        buf = io.BytesIO()
        first = pil_pages[0].convert("RGB")
        rest = [p.convert("RGB") for p in pil_pages[1:]]
        if rest:
            first.save(buf, format="PDF", save_all=True, append_images=rest)
        else:
            first.save(buf, format="PDF")
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Core CV operations
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
    def _perspective_crop(img: Any) -> Any:
        """Detect document edges and apply perspective transform.

        Falls back to returning the original image if no clear quadrilateral
        is found (e.g. already-flat scan).
        """
        orig = img.copy()
        _h, _w = img.shape[:2]

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 75, 200)

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        doc_contour: Any | None = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                doc_contour = approx
                break

        if doc_contour is None:
            return orig

        pts = doc_contour.reshape(4, 2).astype(np.float32)
        # Order: top-left, top-right, bottom-right, bottom-left
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = pts[np.argmin(s)]
        ordered[2] = pts[np.argmax(s)]
        ordered[1] = pts[np.argmin(diff)]
        ordered[3] = pts[np.argmax(diff)]

        max_w = int(
            max(
                np.linalg.norm(ordered[1] - ordered[0]),
                np.linalg.norm(ordered[2] - ordered[3]),
            )
        )
        max_h = int(
            max(
                np.linalg.norm(ordered[3] - ordered[0]),
                np.linalg.norm(ordered[2] - ordered[1]),
            )
        )

        if max_w < 100 or max_h < 100:
            return orig

        dst = np.array(
            [[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]],
            dtype=np.float32,
        )
        m = cv2.getPerspectiveTransform(ordered, dst)
        warped: Any = cv2.warpPerspective(img, m, (max_w, max_h))
        return warped

    @staticmethod
    def _enhance(img: Any, mode: str) -> Any:
        """Apply enhancement based on selected mode."""
        if mode == "black_and_white":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
        if mode == "grayscale":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        # original_enhanced: CLAHE contrast boost
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_ch, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        return cv2.cvtColor(cv2.merge((l_ch, a, b)), cv2.COLOR_LAB2BGR)

    @staticmethod
    def _quality_score(img: Any) -> int:
        """Estimate scan quality 0-100 via Laplacian variance (sharpness)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        score = min(100, int(lap_var / 5))
        return score
