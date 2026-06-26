"""Integration tests for OCR API endpoints (S1-08)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def make_mock_user() -> MagicMock:
    user = MagicMock()
    user.id = "test-user-id"
    user.credits_remaining = 100
    user.plan = "free"
    user.is_active = True
    return user


def make_mock_file(file_id: str = "test-file-id") -> MagicMock:
    f = MagicMock()
    f.id = file_id
    f.user_id = "test-user-id"
    f.r2_key = f"uploads/{file_id}.jpg"
    f.mime_type = "image/jpeg"
    f.size_bytes = 50000
    return f


def make_mock_job(job_id: str = "test-job-id", tool: str = "receipt-scanner") -> MagicMock:
    job = MagicMock()
    job.id = job_id
    job.user_id = "test-user-id"
    job.tool_slug = tool
    job.status = "QUEUED"
    job.credits_used = 1
    return job


# ------------------------------------------------------------------
# Auth endpoint integration tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint should return 200 without auth."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_receipt_requires_auth(client: AsyncClient) -> None:
    """Process endpoint should return 403/401 without token."""
    response = await client.post(
        "/api/v1/tools/receipt-scanner/process",
        json={"file_id": "some-file-id"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_invoice_requires_auth(client: AsyncClient) -> None:
    """Invoice endpoint should return 401 without token."""
    response = await client.post(
        "/api/v1/tools/invoice-reader/process",
        json={"file_id": "some-file-id"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_biz_card_requires_auth(client: AsyncClient) -> None:
    """Business card endpoint should return 401 without token."""
    response = await client.post(
        "/api/v1/tools/business-card-scanner/process",
        json={"file_id": "some-file-id"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_status_requires_auth(client: AsyncClient) -> None:
    """Job status endpoint should require auth."""
    response = await client.get("/api/v1/jobs/some-job-id")
    assert response.status_code in (401, 403)


# ------------------------------------------------------------------
# OCR tool unit tests (without DB / R2)
# ------------------------------------------------------------------


class TestReceiptScannerUnit:
    """Fast unit tests that don't hit external services."""

    def test_process_with_known_text(self) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        # Test extraction helpers directly (OCR model not needed)
        text = "SHOPRITE\nDate: 2024-06-15\nBread  2500\nMilk   1200\nTotal  3700\nRWF"
        assert scanner._detect_currency(text) == "RWF"
        assert scanner._extract_merchant(text) == "SHOPRITE"
        date = scanner._extract_date(text)
        assert date is not None
        assert "2024" in date

    def test_extract_total_from_text(self) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        text = "Sub-total 3700\nTax 666\nTotal 4366"
        total = scanner._extract_amount(text, ["total", "grand total"])
        assert total is not None
        assert total == 4366.0

    def test_csv_export_format(self) -> None:
        from app.cv.tools.receipt_scanner import ReceiptScanner

        scanner = ReceiptScanner()
        result: dict[str, Any] = {
            "merchant": "Test Shop",
            "date": "2024-06-15",
            "currency": "RWF",
            "line_items": [{"name": "Item A", "qty": 1, "price": 1500.0}],
            "subtotal": 1500.0,
            "tax": 270.0,
            "total": 1770.0,
            "confidence_score": 85,
        }
        csv_out = scanner.to_csv(result)
        assert "Test Shop" in csv_out
        assert "1770.0" in csv_out


class TestInvoiceReaderUnit:
    """Unit tests for invoice reader extraction logic."""

    def test_invoice_number_patterns(self) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        cases = [
            ("Invoice #INV-001", "INV-001"),
            ("Invoice Number: ABC123", "ABC123"),
            ("INV: 2024-06-01", "2024-06-01"),
        ]
        for text, _expected_fragment in cases:
            result = reader._extract_invoice_number(text)
            assert result is not None, f"Failed for text: {text}"

    def test_amount_extraction(self) -> None:
        from app.cv.tools.invoice_reader import InvoiceReader

        reader = InvoiceReader()
        text = "Subtotal: 900.00\nTax: 162.00\nTotal Due: 1,062.00"
        assert reader._extract_amount(text, ["subtotal"]) == 900.0
        assert reader._extract_amount(text, ["tax"]) == 162.0


class TestBusinessCardUnit:
    """Unit tests for business card extraction."""

    def test_email_extraction(self) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        text = "Contact: alice@company.com or bob@example.org"
        emails = scanner._extract_emails(text)
        assert "alice@company.com" in emails
        assert "bob@example.org" in emails

    def test_vcf_structure(self) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        result = {
            "full_name": "Alice Mutoni",
            "job_title": "Product Manager",
            "company": "PixelMind AI",
            "emails": ["alice@pixelmind.ai"],
            "phones": ["+250700000001"],
            "websites": [],
            "address": None,
            "social_handles": {},
        }
        vcf = scanner.to_vcf(result)
        assert "BEGIN:VCARD" in vcf
        assert "Alice Mutoni" in vcf
        assert "alice@pixelmind.ai" in vcf
        assert "END:VCARD" in vcf

    def test_social_handle_detection(self) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        text = "linkedin.com/in/johndoe\ntwitter.com/johndoe_dev"
        social = scanner._extract_social(text)
        assert "linkedin" in social or "twitter" in social
