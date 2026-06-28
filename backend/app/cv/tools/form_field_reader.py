"""Form Field Reader CV tool (S2-05).

World-first free tool: extract handwritten form responses into structured JSON.
Uses line detection to find form fields and OCR to read values.
"""

from __future__ import annotations

import io
from typing import Any

import cv2
import numpy as np
from PIL import Image

from app.cv.ocr.engine import OCREngine


class FormFieldReader:
    """Extract handwritten responses from form images into structured JSON."""

    def __init__(self) -> None:
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Run the form field reading pipeline.

        Args:
            image_bytes: Raw image bytes of a filled form.

        Returns:
            result dict with fields list, each having bbox, label_text,
            value_text, confidence.

        """
        img = self._load(image_bytes)
        h, w = img.shape[:2]

        # Step 1: Detect form structure (horizontal/vertical lines)
        lines_h, lines_v = self._detect_lines(img)

        # Step 2: Find field boundaries from intersecting lines
        field_regions = self._find_fields(img, lines_h, lines_v)

        # Step 3: OCR each field region
        fields = self._ocr_fields(img, field_regions)

        return {
            "fields": fields,
            "field_count": len(fields),
            "image_width": w,
            "image_height": h,
            "lines_detected": len(lines_h) + len(lines_v),
        }

    # ------------------------------------------------------------------
    # Line detection
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
    def _detect_lines(
        img: Any,
    ) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:
        """Detect horizontal and vertical lines using morphological operations."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        h, w = binary.shape

        def _rect(c: Any) -> tuple[int, int, int, int]:
            x, y, bw, bh = cv2.boundingRect(c)
            return (int(x), int(y), int(bw), int(bh))

        # Horizontal lines
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 10, 1))
        h_lines_img = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
        h_contours, _ = cv2.findContours(h_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        lines_h: list[tuple[int, int, int, int]] = [
            _rect(c) for c in h_contours if _rect(c)[2] > w // 8
        ]

        # Vertical lines
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, h // 10))
        v_lines_img = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
        v_contours, _ = cv2.findContours(v_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        lines_v: list[tuple[int, int, int, int]] = [
            _rect(c) for c in v_contours if _rect(c)[3] > h // 8
        ]

        return lines_h, lines_v

    def _find_fields(
        self,
        img: Any,
        lines_h: list[tuple[int, int, int, int]],
        lines_v: list[tuple[int, int, int, int]],
    ) -> list[dict[str, Any]]:
        """Infer field regions from detected lines.

        Falls back to row-based segmentation when line detection yields too few results.
        """
        h, w = img.shape[:2]
        fields: list[dict[str, Any]] = []

        if len(lines_h) >= 2:
            # Sort horizontal lines top-to-bottom
            h_sorted = sorted(lines_h, key=lambda r: r[1])
            for i in range(len(h_sorted) - 1):
                y1 = h_sorted[i][1] + h_sorted[i][3]
                y2 = h_sorted[i + 1][1]
                if y2 - y1 < 15:  # Too thin
                    continue
                # Check if there's a vertical split (two-column form)
                mid_v = [lv for lv in lines_v if y1 <= lv[1] <= y2 or y1 <= lv[1] + lv[3] <= y2]
                if mid_v:
                    split_x = mid_v[0][0]
                    fields.append({"bbox": (0, y1, split_x, y2 - y1), "zone": "left", "row": i})
                    fields.append(
                        {
                            "bbox": (split_x, y1, w - split_x, y2 - y1),
                            "zone": "right",
                            "row": i,
                        }
                    )
                else:
                    fields.append({"bbox": (0, y1, w, y2 - y1), "zone": "full", "row": i})
        else:
            # Fallback: split into equal-height rows
            rows = max(3, len(lines_h) + 1)
            row_h = h // rows
            for i in range(rows):
                y1 = i * row_h
                y2 = (i + 1) * row_h
                fields.append({"bbox": (0, y1, w, y2 - y1), "zone": "full", "row": i})

        return fields

    def _ocr_fields(
        self,
        img: Any,
        field_regions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """OCR each field region and classify label vs value."""
        result_fields: list[dict[str, Any]] = []
        h_img, w_img = img.shape[:2]

        for region in field_regions:
            x, y, fw, fh = region["bbox"]
            # Clamp
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w_img, x + fw), min(h_img, y + fh)
            if x2 <= x1 or y2 <= y1:
                continue

            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            ocr_res = self._ocr.extract_text(crop)
            raw_text: str = str(ocr_res.get("text", "")).strip()
            confidence: int = int(ocr_res.get("confidence", 0))

            if not raw_text:
                continue

            # Heuristic split: text before ":" or "_______" = label; rest = value
            label, value = self._split_label_value(raw_text)

            result_fields.append(
                {
                    "field_bbox": {
                        "x": x1,
                        "y": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                    },
                    "label_text": label,
                    "value_text": value,
                    "confidence": confidence,
                    "zone": region.get("zone", "full"),
                    "row": region.get("row", 0),
                }
            )

        return result_fields

    @staticmethod
    def _split_label_value(text: str) -> tuple[str, str]:
        """Split a field's text into label and value parts."""
        # "Name: John Smith" → label="Name", value="John Smith"
        if ":" in text:
            parts = text.split(":", 1)
            return parts[0].strip(), parts[1].strip()
        # "Name _______ John" → split at underscores
        import re

        underscore_split = re.split(r"_{3,}", text, maxsplit=1)
        if len(underscore_split) == 2:
            return underscore_split[0].strip(), underscore_split[1].strip()
        # Default: treat whole text as value with empty label
        return "", text
