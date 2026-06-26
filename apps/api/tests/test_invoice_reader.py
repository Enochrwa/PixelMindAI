"""Tests for Invoice Reader (S1-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def invoice_bytes() -> bytes:
    return (FIXTURES / "invoice_sample.jpg").read_bytes()


class TestInvoiceReader:
    """Unit tests for InvoiceReader class."""

    def test_process_returns_expected_keys(self, invoice_bytes: bytes) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        result = InvoiceReader().process(invoice_bytes)
        expected_keys = {
            "invoice_number",
            "supplier_name",
            "supplier_address",
            "buyer_name",
            "date",
            "due_date",
            "payment_terms",
            "line_items",
            "subtotal",
            "tax",
            "total",
            "confidence_score",
        }
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_process_simple_invoice(self, invoice_bytes: bytes) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        result = InvoiceReader().process(invoice_bytes)
        assert isinstance(result, dict)
        assert isinstance(result["line_items"], list)

    def test_to_csv_includes_headers(self, invoice_bytes: bytes) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        result = reader.process(invoice_bytes)
        csv_output = reader.to_csv(result)
        assert "Invoice Number" in csv_output
        assert "Supplier" in csv_output
        assert "Total" in csv_output

    def test_confidence_score_is_valid(self, invoice_bytes: bytes) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        result = InvoiceReader().process(invoice_bytes)
        conf = result["confidence_score"]
        assert isinstance(conf, int)
        assert 0 <= conf <= 100

    def test_multipage_flag_does_not_crash(self, invoice_bytes: bytes) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        # multi_page=True on a JPEG should fallback gracefully
        result = InvoiceReader().process(invoice_bytes, multi_page=True)
        assert isinstance(result, dict)


class TestInvoiceFieldExtraction:
    """Test individual extraction methods."""

    def test_extract_invoice_number(self) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        text = "Invoice #INV-2024-001\nDate: 2024-06-15"
        result = reader._extract_invoice_number(text)
        assert result is not None
        assert "INV" in result

    def test_extract_date_finds_iso_format(self) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        text = "Invoice Date: 2024-06-15\nSome more text"
        result = reader._extract_date(text, ["invoice date"])
        assert result is not None
        assert "2024" in result

    def test_extract_payment_terms(self) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        text = "Payment Terms: Net 30\nOther info"
        result = reader._extract_payment_terms(text)
        assert result is not None

    @pytest.mark.parametrize(
        "text",
        [
            "Subtotal 900.00\nTax 162.00\nTotal 1062.00",
            "Sub-Total: 900\nTax: 162\nGrand Total: 1062",
        ],
    )
    def test_extract_amount(self, text: str) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        total = reader._extract_amount(text, ["total", "grand total"])
        assert total is not None
        assert total > 0
