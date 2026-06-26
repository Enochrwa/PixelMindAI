"""Receipt Scanner CV tool (S1-03).

Extracts: merchant, date, currency, line_items, subtotal, tax, total, confidence.
Supports currencies: USD, EUR, GBP, RWF, KES, UGX, TZS.
Export formats: JSON, CSV, QuickBooks-compatible CSV.
"""

from __future__ import annotations

import contextlib
import csv
import io
import re
from typing import Any

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor

# ISO code → symbols/keywords
CURRENCY_MAP: dict[str, list[str]] = {
    "RWF": ["RWF", "Frw", "RF", "FRw"],
    "KES": ["KES", "Ksh", "K.Sh"],
    "UGX": ["UGX", "USh", "Ush"],
    "TZS": ["TZS", "TSh", "Tsh"],
    "USD": ["USD", "US$", "$"],
    "EUR": ["EUR", "€"],
    "GBP": ["GBP", "£"],
    "NGN": ["NGN", "₦"],
    "ZAR": ["ZAR", "R "],
}


class ReceiptScanner:
    """Extract structured data from receipt images."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Run the full receipt scanning pipeline."""
        img = self._pre.load_image(image_bytes)
        img = self._pre.enhance_contrast(img)
        img = self._pre.deskew(img)

        ocr_result = self._ocr.extract_text(img)
        text: str = str(ocr_result.get("text", ""))
        confidence: int = int(ocr_result.get("confidence", 0))

        currency = self._detect_currency(text)
        line_items = self._extract_line_items(text)

        return {
            "merchant": self._extract_merchant(text),
            "date": self._extract_date(text),
            "currency": currency,
            "line_items": line_items,
            "subtotal": self._extract_amount(text, ["subtotal", "sub-total", "sub total"]),
            "tax": self._extract_amount(text, ["tax", "vat", "tva", "tax amount"]),
            "total": self._extract_amount(text, ["total", "amount due", "grand total", "montant"]),
            "confidence_score": confidence,
            "raw_text": text,
        }

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_csv(self, result: dict[str, Any]) -> str:
        """Export result as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Merchant", result.get("merchant", "")])
        writer.writerow(["Date", result.get("date", "")])
        writer.writerow(["Currency", result.get("currency", "")])
        writer.writerow(["Subtotal", result.get("subtotal", "")])
        writer.writerow(["Tax", result.get("tax", "")])
        writer.writerow(["Total", result.get("total", "")])
        writer.writerow([])
        writer.writerow(["Item", "Price"])
        for item in result.get("line_items", []):
            writer.writerow([item.get("name", ""), item.get("price", "")])
        return output.getvalue()

    def to_quickbooks_csv(self, result: dict[str, Any]) -> str:
        """Export as QuickBooks-compatible accounting CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Description", "Amount", "Currency", "Category"])
        writer.writerow(
            [
                result.get("date", ""),
                result.get("merchant", ""),
                result.get("total", ""),
                result.get("currency", ""),
                "Expense",
            ]
        )
        for item in result.get("line_items", []):
            writer.writerow(
                [
                    result.get("date", ""),
                    item.get("name", ""),
                    item.get("price", ""),
                    result.get("currency", ""),
                    "Line Item",
                ]
            )
        return output.getvalue()

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_merchant(self, text: str) -> str:
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        return lines[0] if lines else ""

    def _extract_date(self, text: str) -> str | None:
        patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _detect_currency(self, text: str) -> str:
        for code, symbols in CURRENCY_MAP.items():
            if any(sym in text for sym in symbols):
                return code
        return "USD"

    def _extract_line_items(self, text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        # Match: "Some Item Name  12.50" or "Some Item  12,50"
        price_pattern = re.compile(r"^(.+?)\s{2,}(\d+(?:[.,]\d{1,2})?)\s*$", re.MULTILINE)
        for match in price_pattern.finditer(text):
            name = match.group(1).strip()
            price_str = match.group(2).replace(",", ".")
            if len(name) > 2 and len(name) < 80:
                with contextlib.suppress(ValueError):
                    items.append({"name": name, "qty": 1, "price": float(price_str)})
        return items

    def _extract_amount(self, text: str, labels: list[str]) -> float | None:
        text_lower = text.lower()
        for label in labels:
            start = 0
            while True:
                idx = text_lower.find(label, start)
                if idx == -1:
                    break
                # Skip sub-total / sub total lines when searching for "total"
                context = text_lower[max(0, idx - 5) : idx]
                if label == "total" and "sub" in context:
                    start = idx + 1
                    continue
                segment = text[idx : idx + 80]
                match = re.search(r"(\d+(?:[.,]\d{1,2})?)", segment)
                if match:
                    try:
                        return float(match.group(1).replace(",", "."))
                    except ValueError:
                        pass
                start = idx + 1
        return None
