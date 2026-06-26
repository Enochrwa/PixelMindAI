"""Multi-engine OCR abstraction with auto-fallback (S1-01).

Primary: EasyOCR (best multi-language + handwriting)
Secondary: PaddleOCR (better structured tables)
Tertiary: pytesseract (fastest for clean printed text)
"""

from __future__ import annotations

import io
import logging

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_LANGS = {"en", "fr"}


class OCREngine:
    """Routes OCR to EasyOCR → PaddleOCR → Tesseract with auto-fallback."""

    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = [lang for lang in (languages or ["en"]) if lang in SUPPORTED_LANGS]
        if not self.languages:
            self.languages = ["en"]
        self._easyocr: object | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_text(self, image: np.ndarray | bytes) -> dict[str, object]:
        """Extract text from image.

        Returns:
            {text: str, words: list[dict], confidence: int (0-100)}

        """
        if isinstance(image, bytes):
            pil = Image.open(io.BytesIO(image))
            image = np.array(pil.convert("RGB"))

        try:
            return self._easyocr_extract(image)
        except Exception as primary_err:
            logger.warning("EasyOCR failed (%s), trying Tesseract", primary_err)
            try:
                return self._tesseract_fallback(image)
            except Exception as fallback_err:
                logger.error("All OCR engines failed: %s", fallback_err)
                return {"text": "", "words": [], "confidence": 0}

    def detect_script(self, image: np.ndarray) -> str:
        """Detect primary script/language before full extraction."""
        try:
            result = self.extract_text(image)
            text = str(result.get("text", ""))
            # Simple heuristic: check for non-ASCII characters
            non_ascii = sum(1 for c in text if ord(c) > 127)
            if non_ascii / max(len(text), 1) > 0.3:
                return "fr"
            return "en"
        except Exception:
            return "en"

    # ------------------------------------------------------------------
    # Internal engines
    # ------------------------------------------------------------------

    def _get_easyocr(self) -> object:
        if self._easyocr is None:
            import easyocr  # type: ignore[import-untyped]

            self._easyocr = easyocr.Reader(self.languages, gpu=False, verbose=False)
        return self._easyocr

    def _easyocr_extract(self, image: np.ndarray) -> dict[str, object]:
        reader = self._get_easyocr()
        results = reader.readtext(image)  # type: ignore[attr-defined]
        words = [{"text": r[1], "confidence": float(r[2]), "bbox": r[0]} for r in results]
        full_text = "\n".join(w["text"] for w in words)
        avg_conf = sum(w["confidence"] for w in words) / len(words) if words else 0.0
        return {"text": full_text, "words": words, "confidence": round(avg_conf * 100)}

    def _tesseract_fallback(self, image: np.ndarray) -> dict[str, object]:
        """Tesseract fallback via pytesseract."""
        import pytesseract  # type: ignore[import-untyped]

        lang_code = "+".join(self.languages)
        text = pytesseract.image_to_string(image, lang=lang_code)
        data = pytesseract.image_to_data(image, lang=lang_code, output_type=pytesseract.Output.DICT)
        words = []
        for i, word in enumerate(data.get("text", [])):
            if word.strip():
                conf = float(data["conf"][i])
                if conf > 0:
                    words.append({"text": word, "confidence": conf / 100.0, "bbox": []})
        avg_conf = sum(w["confidence"] for w in words) / len(words) if words else 0.5
        return {"text": text.strip(), "words": words, "confidence": round(avg_conf * 100)}
