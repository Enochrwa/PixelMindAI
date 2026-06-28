"""Menu Scanner & Digitizer CV tool (S2-02).

Converts physical restaurant menus to structured digital data.
Export: JSON, flat CSV (category/name/desc/price), POS-compatible CSV.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor


class MenuScanner:
    """Extract structured menu data from restaurant menu photos."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(
        self,
        image_bytes: bytes,
        export_format: str = "json",  # noqa: ARG002
        pos_format: bool = False,
    ) -> dict[str, Any]:
        """Run the full menu scanning pipeline.

        Args:
            image_bytes: Raw image bytes.
            export_format: Preferred export format hint.
            pos_format: If True, include POS-compatible field names.

        Returns:
            Structured menu data.

        """
        img = self._pre.load_image(image_bytes)
        img = self._pre.enhance_contrast(img)

        ocr_result = self._ocr.extract_text(img)
        text: str = str(ocr_result.get("text", ""))
        confidence: int = int(ocr_result.get("confidence", 0))

        restaurant_name = self._extract_restaurant_name(text)
        currency = self._detect_currency(text)
        categories = self._extract_categories(text)

        result: dict[str, Any] = {
            "restaurant_name": restaurant_name,
            "currency": currency,
            "categories": categories,
            "total_items": sum(len(cat["items"]) for cat in categories),
            "confidence_score": confidence,
            "raw_text": text,
        }

        if pos_format:
            result["pos_export"] = self._to_pos_list(categories, currency)

        return result

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_restaurant_name(self, text: str) -> str:
        """First non-empty line typically contains the restaurant name."""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        return lines[0] if lines else ""

    @staticmethod
    def _detect_currency(text: str) -> str:
        """Detect currency from menu text."""
        patterns = {
            "RWF": ["RWF", "Frw", "RF"],
            "KES": ["KES", "Ksh"],
            "USD": ["USD", "$"],
            "EUR": ["EUR", "€"],
            "GBP": ["GBP", "£"],
            "UGX": ["UGX", "USh"],
            "TZS": ["TZS", "TSh"],
        }
        for code, symbols in patterns.items():
            if any(sym in text for sym in symbols):
                return code
        return "USD"

    def _extract_categories(self, text: str) -> list[dict[str, Any]]:
        """Extract menu categories and items.

        Strategy: Use bounding-box height heuristic via line analysis.
        Longer, ALL-CAPS, or short lines without prices = categories.
        Lines with price patterns = items.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        price_pattern = re.compile(r"(\d{1,6}(?:[.,]\d{1,2})?)\s*$")

        categories: list[dict[str, Any]] = []
        current_category: dict[str, Any] | None = None

        for line in lines:
            if len(line) < 3:
                continue

            price_match = price_pattern.search(line)
            if price_match:
                # This is a menu item
                raw_price = price_match.group(1).replace(",", ".")
                name = price_pattern.sub("", line).strip().rstrip("-").strip()
                if not name:
                    continue

                item: dict[str, Any] = {
                    "name": name,
                    "description": "",
                    "price": float(raw_price),
                }

                if current_category is None:
                    # Create a default category
                    current_category = {"name": "General", "items": []}
                    categories.append(current_category)

                current_category["items"].append(item)
            else:
                # Potential category heading: short, no price, likely uppercase/title
                is_heading = (
                    len(line) < 60
                    and not re.search(r"\d{3,}", line)
                    and (line.isupper() or line.istitle() or len(line.split()) <= 4)
                )
                if is_heading:
                    current_category = {"name": line, "items": []}
                    categories.append(current_category)
                else:
                    # Treat as item description for previous item
                    if current_category and current_category["items"]:
                        last_item = current_category["items"][-1]
                        if not last_item["description"]:
                            last_item["description"] = line

        return categories

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_csv(result: dict[str, Any]) -> str:
        """Export as flat CSV (category/name/description/price)."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Category", "Item", "Description", "Price", "Currency"])
        currency = result.get("currency", "")
        for cat in result.get("categories", []):
            for item in cat.get("items", []):
                writer.writerow(
                    [
                        cat.get("name", ""),
                        item.get("name", ""),
                        item.get("description", ""),
                        item.get("price", ""),
                        currency,
                    ]
                )
        return output.getvalue()

    @staticmethod
    def to_pos_csv(result: dict[str, Any]) -> str:
        """Export as POS-compatible CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["PLU", "Description", "Category", "Price", "Currency", "Tax_Rate", "Active"]
        )
        currency = result.get("currency", "")
        plu = 1001
        for cat in result.get("categories", []):
            for item in cat.get("items", []):
                writer.writerow(
                    [
                        str(plu),
                        item.get("name", ""),
                        cat.get("name", ""),
                        item.get("price", ""),
                        currency,
                        "0.18",  # Standard VAT
                        "1",
                    ]
                )
                plu += 1
        return output.getvalue()

    @staticmethod
    def _to_pos_list(
        categories: list[dict[str, Any]],
        currency: str,
    ) -> list[dict[str, Any]]:
        """Build POS-structured list."""
        pos_items = []
        plu = 1001
        for cat in categories:
            for item in cat.get("items", []):
                pos_items.append(
                    {
                        "plu": str(plu),
                        "description": item.get("name", ""),
                        "category": cat.get("name", ""),
                        "price": item.get("price", 0),
                        "currency": currency,
                        "tax_rate": 0.18,
                        "active": True,
                    }
                )
                plu += 1
        return pos_items
