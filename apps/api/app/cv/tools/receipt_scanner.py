"""Receipt Scanner CV tool."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor

CURRENCY_MAP = {
    "RWF": ["RWF", "Frw", "RF"],
    "KES": ["KES", "Ksh", "K"],
    "UGX": ["UGX", "USh"],
    "TZS": ["TZS", "TSh"],
    "USD": ["$", "USD"],
    "EUR": ["€", "EUR"],
    "GBP": ["£", "GBP"],
}


class ReceiptScanner:
    """Extract structured data from receipt images."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Run the full receipt scanning pipeline."""
        img = self._pre.load_image(image_bytes)
        img = self._pre.enhance_contrast(img)
        img = self._pre.deskew(img)

        ocr_result = self._ocr.extract_text(img)
        text: str = ocr_result["text"]  # type: ignore[assignment]

        return {
            "merchant": self._extract_merchant(text),
            "date": self._extract_date(text),
            "currency": self._detect_currency(text),
            "line_items": self._extract_line_items(text),
            "subtotal": self._extract_amount(text, ["subtotal", "sub-total", "sub total"]),
            "tax": self._extract_amount(text, ["tax", "vat", "tva"]),
            "total": self._extract_amount(text, ["total", "amount due", "grand total"]),
            "confidence": ocr_result["confidence"],
            "raw_text": text,
        }

    def _extract_merchant(self, text: str) -> str:
        lines = text.strip().split("\n")
        return lines[0].strip() if lines else ""

    def _extract_date(self, text: str) -> str | None:
        pattern = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _detect_currency(self, text: str) -> str:
        for code, symbols in CURRENCY_MAP.items():
            if any(sym in text for sym in symbols):
                return code
        return "USD"

    def _extract_line_items(self, text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        price_pattern = re.compile(r"(.+?)\s+(\d+(?:[.,]\d{2})?)\s*$")
        for line in text.split("\n"):
            m = price_pattern.match(line.strip())
            if m:
                items.append({"name": m.group(1).strip(), "price": float(m.group(2).replace(",", "."))})
        return items

    def _extract_amount(self, text: str, labels: list[str]) -> float | None:
        text_lower = text.lower()
        for label in labels:
            idx = text_lower.find(label)
            if idx != -1:
                segment = text[idx: idx + 60]
                m = re.search(r"(\d+(?:[.,]\d{2})?)", segment)
                if m:
                    return float(m.group(1).replace(",", "."))
        return None
