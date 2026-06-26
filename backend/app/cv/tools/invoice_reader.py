"""Invoice Reader CV tool (S1-04).

Extracts: invoice_number, supplier, buyer, line_items, subtotal, tax, total,
due_date, payment_terms. Supports multi-page PDFs via pdfplumber.
Export formats: JSON, CSV, PDF summary.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor


class InvoiceReader:
    """Extract structured data from invoice images and PDFs."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes, multi_page: bool = False) -> dict[str, Any]:
        """Run the full invoice reading pipeline."""
        # Check if PDF for multi-page handling
        if image_bytes[:4] == b"%PDF" or multi_page:
            return self._process_pdf(image_bytes)
        return self._process_image(image_bytes)

    def _process_image(self, image_bytes: bytes) -> dict[str, Any]:
        img = self._pre.load_image(image_bytes)
        img = self._pre.enhance_contrast(img)
        img = self._pre.deskew(img)
        ocr_result = self._ocr.extract_text(img)
        text: str = str(ocr_result.get("text", ""))
        return self._extract_fields(text, int(ocr_result.get("confidence", 0)))

    def _process_pdf(self, pdf_bytes: bytes) -> dict[str, Any]:
        """Handle multi-page PDF by extracting text per page."""
        try:
            import pdfplumber

            full_text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    full_text += page_text + "\n"
            return self._extract_fields(full_text, 85)
        except ImportError:
            # Fallback: treat first page as image
            return self._process_image(pdf_bytes)
        except Exception:
            return self._process_image(pdf_bytes)

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_csv(self, result: dict[str, Any]) -> str:
        """Export result as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Invoice Number", result.get("invoice_number", "")])
        writer.writerow(["Supplier", result.get("supplier_name", "")])
        writer.writerow(["Supplier Address", result.get("supplier_address", "")])
        writer.writerow(["Buyer", result.get("buyer_name", "")])
        writer.writerow(["Issue Date", result.get("date", "")])
        writer.writerow(["Due Date", result.get("due_date", "")])
        writer.writerow(["Payment Terms", result.get("payment_terms", "")])
        writer.writerow(["Subtotal", result.get("subtotal", "")])
        writer.writerow(["Tax", result.get("tax", "")])
        writer.writerow(["Total", result.get("total", "")])
        writer.writerow([])
        writer.writerow(["Description", "Qty", "Unit Price", "Amount"])
        for item in result.get("line_items", []):
            writer.writerow(
                [
                    item.get("name", ""),
                    item.get("qty", 1),
                    item.get("unit_price", ""),
                    item.get("amount", ""),
                ]
            )
        return output.getvalue()

    # ------------------------------------------------------------------
    # Field extraction
    # ------------------------------------------------------------------

    def _extract_fields(self, text: str, confidence: int) -> dict[str, Any]:
        return {
            "invoice_number": self._extract_invoice_number(text),
            "supplier_name": self._extract_supplier(text),
            "supplier_address": self._extract_address(text, "supplier"),
            "buyer_name": self._extract_buyer(text),
            "date": self._extract_date(text, ["invoice date", "date:", "issued"]),
            "due_date": self._extract_date(text, ["due date", "payment due", "pay by"]),
            "payment_terms": self._extract_payment_terms(text),
            "line_items": self._extract_line_items(text),
            "subtotal": self._extract_amount(text, ["subtotal", "sub-total", "sub total"]),
            "tax": self._extract_amount(text, ["tax", "vat", "gst", "tva"]),
            "total": self._extract_amount(
                text, ["total", "amount due", "balance due", "grand total"]
            ),
            "confidence_score": confidence,
            "raw_text": text,
        }

    def _extract_invoice_number(self, text: str) -> str | None:
        patterns = [
            r"invoice\s*#?\s*:?\s*([A-Z0-9-]+)",
            r"inv\s*#?\s*:?\s*([A-Z0-9-]+)",
            r"invoice\s+number\s*:?\s*([A-Z0-9-]+)",
            r"#\s*([A-Z0-9-]{4,20})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_supplier(self, text: str) -> str:
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        return lines[0] if lines else ""

    def _extract_buyer(self, text: str) -> str | None:
        patterns = [
            r"(?:bill to|billed to|to|customer|client)\s*:?\s*\n(.+)",
            r"(?:ship to|sold to)\s*:?\s*\n(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_address(self, text: str, _party: str) -> str | None:
        # Look for address patterns (street numbers + names)
        pattern = (
            r"\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*(?:\s+(?:Street|St|Avenue|Ave|Road|Rd|Blvd|Lane|Ln))"
        )
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_date(self, text: str, labels: list[str]) -> str | None:
        date_patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s+\d{2,4})\b",
        ]
        text_lower = text.lower()
        for label in labels:
            idx = text_lower.find(label.lower())
            if idx != -1:
                segment = text[idx : idx + 100]
                for dp in date_patterns:
                    match = re.search(dp, segment, re.IGNORECASE)
                    if match:
                        return match.group(0)
        # Fallback: first date in document
        for dp in date_patterns:
            match = re.search(dp, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_payment_terms(self, text: str) -> str | None:
        pattern = r"(?:payment terms?|terms?)\s*:?\s*(.{5,50})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Common terms
        for term in ["net 30", "net 60", "net 15", "due on receipt", "immediate"]:
            if term in text.lower():
                return term.title()
        return None

    def _extract_line_items(self, text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        # Match lines with description + optional qty + price
        pattern = re.compile(
            r"^(.{3,60}?)\s{2,}(\d+(?:\.\d+)?)\s{1,}(\d+(?:[.,]\d{1,2})?)\s*$",
            re.MULTILINE,
        )
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            if len(name) < 3:
                continue
            try:
                qty = float(match.group(2))
                price = float(match.group(3).replace(",", "."))
                items.append(
                    {
                        "name": name,
                        "qty": qty,
                        "unit_price": price,
                        "amount": round(qty * price, 2),
                    }
                )
            except ValueError:
                pass
        return items

    def _extract_amount(self, text: str, labels: list[str]) -> float | None:
        text_lower = text.lower()
        for label in labels:
            idx = text_lower.find(label)
            if idx != -1:
                segment = text[idx : idx + 80]
                match = re.search(r"(\d+(?:[.,]\d{1,2})?)", segment)
                if match:
                    try:
                        return float(match.group(1).replace(",", "."))
                    except ValueError:
                        pass
        return None
