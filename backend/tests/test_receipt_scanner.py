"""Tests for Receipt Scanner (S1-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def receipt_bytes() -> bytes:
    return (FIXTURES / "receipt_sample.jpg").read_bytes()


@pytest.fixture()
def blurry_receipt_bytes() -> bytes:
    return (FIXTURES / "receipt_blurry.jpg").read_bytes()


@pytest.fixture()
def cropped_receipt_bytes() -> bytes:
    return (FIXTURES / "receipt_cropped.jpg").read_bytes()


class TestReceiptScanner:
    """Unit tests for ReceiptScanner class."""

    def test_process_returns_expected_keys(self, receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        result = ReceiptScanner().process(receipt_bytes)
        assert "merchant" in result
        assert "date" in result
        assert "currency" in result
        assert "line_items" in result
        assert "subtotal" in result
        assert "tax" in result
        assert "total" in result
        assert "confidence_score" in result
        assert "raw_text" in result

    def test_currency_detection_rwf(self, receipt_bytes: bytes) -> None:
        from unittest.mock import patch

        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        mock_ocr = {
            "text": "KIGALI SUPERMARKET\nDate: 2024-06-15\nBread 1500\nTotal 5074\nRWF",
            "words": [],
            "confidence": 85,
        }
        with patch.object(scanner._ocr, "extract_text", return_value=mock_ocr):
            result = scanner.process(receipt_bytes)
        assert result["currency"] == "RWF"

    def test_process_blurry_receipt(self, blurry_receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        # Should not raise; returns result with potentially lower confidence
        result = ReceiptScanner().process(blurry_receipt_bytes)
        assert isinstance(result, dict)
        assert "merchant" in result

    def test_process_cropped_receipt(self, cropped_receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        result = ReceiptScanner().process(cropped_receipt_bytes)
        assert isinstance(result, dict)

    def test_to_csv_output(self, receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        result = scanner.process(receipt_bytes)
        csv_output = scanner.to_csv(result)
        assert "Field,Value" in csv_output or "Field" in csv_output
        assert isinstance(csv_output, str)

    def test_to_quickbooks_csv_output(self, receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        result = scanner.process(receipt_bytes)
        qb_csv = scanner.to_quickbooks_csv(result)
        assert "Date" in qb_csv
        assert "Currency" in qb_csv

    def test_confidence_is_int_between_0_100(self, receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        result = ReceiptScanner().process(receipt_bytes)
        conf = result["confidence_score"]
        assert isinstance(conf, int)
        assert 0 <= conf <= 100

    def test_line_items_is_list(self, receipt_bytes: bytes) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        result = ReceiptScanner().process(receipt_bytes)
        assert isinstance(result["line_items"], list)


class TestCurrencyDetection:
    """Test currency detection across African currencies."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Total: RWF 5000", "RWF"),
            ("Amount: KES 1200", "KES"),
            ("Total USD 99.99", "USD"),
            ("€ 45.00", "EUR"),
            ("£ 20.00", "GBP"),
            ("UGX 50000", "UGX"),
            ("no currency here", "USD"),  # fallback
        ],
    )
    def test_detect_currency(self, text: str, expected: str) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        assert scanner._detect_currency(text) == expected
