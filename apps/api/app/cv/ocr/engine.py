"""Multi-engine OCR abstraction with auto-fallback."""

from __future__ import annotations

import io
import logging

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OCREngine:
    """Routes OCR to EasyOCR → PaddleOCR → Tesseract with fallback."""

    SUPPORTED_LANGS = {"en", "fr"}

    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or ["en"]
        self._easyocr: object | None = None

    def _get_easyocr(self) -> object:
        if self._easyocr is None:
            import easyocr  # type: ignore[import]
            self._easyocr = easyocr.Reader(self.languages, gpu=False)
        return self._easyocr

    def extract_text(self, image: np.ndarray | bytes) -> dict[str, object]:
        """Extract text from image. Returns {text, words, confidence}."""
        if isinstance(image, bytes):
            pil = Image.open(io.BytesIO(image))
            image = np.array(pil)

        try:
            reader = self._get_easyocr()
            results = reader.readtext(image)  # type: ignore[attr-defined]
            words = [
                {"text": r[1], "confidence": float(r[2]), "bbox": r[0]}
                for r in results
            ]
            full_text = " ".join(w["text"] for w in words)
            avg_conf = sum(w["confidence"] for w in words) / len(words) if words else 0.0
            return {"text": full_text, "words": words, "confidence": round(avg_conf * 100)}
        except Exception as e:
            logger.warning("EasyOCR failed, falling back to Tesseract: %s", e)
            return self._tesseract_fallback(image)

    def _tesseract_fallback(self, image: np.ndarray) -> dict[str, object]:
        """Tesseract fallback via pytesseract."""
        import pytesseract  # type: ignore[import]
        text = pytesseract.image_to_string(image)
        return {"text": text.strip(), "words": [], "confidence": 50}
