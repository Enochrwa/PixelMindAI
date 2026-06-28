"""Handwriting OCR CV tool (S2-01).

Converts handwritten notes to digital text with structure detection.
Export formats: .txt, .md (with structure), .docx
"""

from __future__ import annotations

import re
from typing import Any

import cv2
import numpy as np

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor


class HandwritingOCR:
    """Convert handwritten images to structured digital text."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(
        self,
        image_bytes: bytes,
        structure_mode: bool = True,
    ) -> dict[str, Any]:
        """Run handwriting OCR pipeline.

        Args:
            image_bytes: Raw image bytes.
            structure_mode: Detect headings, bullets, numbered lists.

        Returns:
            result dict with raw_text, paragraphs, word_count, language_detected,
            confidence_score, and optionally structured blocks.

        """
        img = self._pre.load_image(image_bytes)
        img = self._heavy_preprocess(img)

        paragraphs = self._process_paragraphs(img)
        raw_text = "\n\n".join(p["text"] for p in paragraphs if p["text"].strip())

        _raw_conf = paragraphs[0]["confidence"] if paragraphs else 0
        avg_conf = int(
            sum(p["confidence"] for p in paragraphs) / len(paragraphs) if paragraphs else 0
        )

        result: dict[str, Any] = {
            "raw_text": raw_text,
            "paragraphs": paragraphs,
            "word_count": len(raw_text.split()),
            "language_detected": self._detect_language(raw_text),
            "confidence_score": avg_conf,
        }

        if structure_mode:
            result["structured_blocks"] = self._detect_structure(paragraphs)

        return result

    # ------------------------------------------------------------------
    # Preprocessing for handwriting
    # ------------------------------------------------------------------

    @staticmethod
    def _heavy_preprocess(img: Any) -> Any:
        """Apply heavy denoising + binarization for handwriting."""
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
        _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Dilate to connect text strokes
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(binarized, kernel, iterations=1)
        return cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)

    # ------------------------------------------------------------------
    # Paragraph detection
    # ------------------------------------------------------------------

    def _process_paragraphs(self, img: Any) -> list[dict[str, Any]]:
        """Detect text paragraphs via contour analysis and OCR each."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Dilate vertically to group lines into paragraphs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (100, 5))
        dilated = cv2.dilate(binary, kernel, iterations=3)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # Fallback: process whole image as single paragraph
            ocr = self._ocr.extract_text(img)
            text: str = str(ocr.get("text", ""))
            conf = int(ocr.get("confidence", 0))
            return [{"text": text, "confidence": conf}]

        # Sort top-to-bottom
        rects = sorted([cv2.boundingRect(c) for c in contours], key=lambda r: r[1])

        paragraphs: list[dict[str, Any]] = []
        h_full, w_full = img.shape[:2]
        for x, y, w, h in rects:
            if h < 20 or w < 50:  # Skip tiny regions
                continue
            # Clamp and expand region slightly
            x1 = max(0, x - 10)
            y1 = max(0, y - 10)
            x2 = min(w_full, x + w + 10)
            y2 = min(h_full, y + h + 10)
            region = img[y1:y2, x1:x2]
            ocr_res = self._ocr.extract_text(region)
            text_block: str = str(ocr_res.get("text", "")).strip()
            if text_block:
                paragraphs.append(
                    {
                        "text": text_block,
                        "confidence": int(ocr_res.get("confidence", 0)),
                    }
                )

        return paragraphs if paragraphs else [{"text": "", "confidence": 0}]

    # ------------------------------------------------------------------
    # Structure detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_structure(
        paragraphs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect headings, bullets, numbered lists from paragraph layout."""
        blocks: list[dict[str, Any]] = []
        for para in paragraphs:
            text = para["text"].strip()
            if not text:
                continue
            lines = text.split("\n")
            block_type = "paragraph"
            if len(lines) == 1 and len(text) < 60 and text.isupper():
                block_type = "heading"
            elif re.match(r"^[\-\*\•]\s+", text):
                block_type = "bullet_list"
            elif re.match(r"^\d+[\.\)]\s+", text):
                block_type = "numbered_list"
            blocks.append({"type": block_type, "text": text, "confidence": para["confidence"]})
        return blocks

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_language(text: str) -> str:
        """Detect language via simple heuristic."""
        fr_words = {"le", "la", "les", "de", "du", "et", "en", "est", "pas", "pour", "qui"}
        words = set(text.lower().split())
        if len(words & fr_words) >= 2:
            return "fr"
        return "en"

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_txt(result: dict[str, Any]) -> str:
        """Export as plain text."""
        return str(result.get("raw_text", ""))

    @staticmethod
    def to_markdown(result: dict[str, Any]) -> str:
        """Export as Markdown using detected structure."""
        blocks = result.get("structured_blocks") or []
        if not blocks:
            return str(result.get("raw_text", ""))

        lines: list[str] = []
        for block in blocks:
            btype = block.get("type", "paragraph")
            text: str = str(block.get("text", ""))
            if btype == "heading":
                lines.append(f"## {text}\n")
            elif btype == "bullet_list":
                for line in text.split("\n"):
                    clean = re.sub(r"^[\-\*\•]\s*", "", line).strip()
                    if clean:
                        lines.append(f"- {clean}")
                lines.append("")
            elif btype == "numbered_list":
                for i, line in enumerate(text.split("\n"), 1):
                    clean = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                    if clean:
                        lines.append(f"{i}. {clean}")
                lines.append("")
            else:
                lines.append(text)
                lines.append("")

        return "\n".join(lines)
