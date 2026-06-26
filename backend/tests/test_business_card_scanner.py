"""Tests for Business Card Scanner (S1-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def card_bytes() -> bytes:
    return (FIXTURES / "business_card_sample.jpg").read_bytes()


@pytest.fixture()
def card_bytes_2() -> bytes:
    return (FIXTURES / "business_card_2.jpg").read_bytes()


@pytest.fixture()
def card_bytes_3() -> bytes:
    return (FIXTURES / "business_card_3.jpg").read_bytes()


class TestBusinessCardScanner:
    """Unit tests for BusinessCardScanner class."""

    def test_process_returns_expected_keys(self, card_bytes: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        result = BusinessCardScanner().process(card_bytes)
        expected_keys = {
            "full_name",
            "job_title",
            "company",
            "emails",
            "phones",
            "websites",
            "address",
            "social_handles",
            "confidence_score",
        }
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_emails_is_list(self, card_bytes: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        result = BusinessCardScanner().process(card_bytes)
        assert isinstance(result["emails"], list)

    def test_phones_is_list(self, card_bytes: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        result = BusinessCardScanner().process(card_bytes)
        assert isinstance(result["phones"], list)

    def test_to_vcf_output(self, card_bytes: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        result = scanner.process(card_bytes)
        vcf = scanner.to_vcf(result)
        assert "BEGIN:VCARD" in vcf
        assert "END:VCARD" in vcf
        assert "VERSION:3.0" in vcf

    def test_to_csv_output(self, card_bytes: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        result = scanner.process(card_bytes)
        csv_output = scanner.to_csv(result)
        assert "Name" in csv_output

    def test_bulk_processing(
        self, card_bytes: bytes, card_bytes_2: bytes, card_bytes_3: bytes
    ) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        results = scanner.process_bulk([card_bytes, card_bytes_2, card_bytes_3])
        assert len(results) == 3
        for result in results:
            assert "emails" in result
            assert "phones" in result

    def test_bulk_to_zip_returns_bytes(self, card_bytes: bytes, card_bytes_2: bytes) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        results = scanner.process_bulk([card_bytes, card_bytes_2])
        zip_bytes = scanner.bulk_to_zip(results)
        assert isinstance(zip_bytes, bytes)
        assert zip_bytes[:2] == b"PK"  # ZIP magic bytes


class TestEmailPhoneExtraction:
    """Test regex extraction helpers."""

    @pytest.mark.parametrize(
        ("text", "expected_count"),
        [
            ("Email: john@example.com", 1),
            ("john@test.com and jane@test.org", 2),
            ("no emails here", 0),
        ],
    )
    def test_extract_emails(self, text: str, expected_count: int) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        emails = scanner._extract_emails(text)
        assert len(emails) == expected_count

    @pytest.mark.parametrize(
        "text",
        [
            "+250788123456",
            "+1 (555) 123-4567",
            "Tel: +44 20 7946 0958",
        ],
    )
    def test_extract_phones_finds_numbers(self, text: str) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        phones = scanner._extract_phones(text)
        assert len(phones) >= 1

    def test_to_vcf_valid_format(self) -> None:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()
        result = {
            "full_name": "Jane Smith",
            "job_title": "CTO",
            "company": "TechCo Ltd",
            "emails": ["jane@techco.com"],
            "phones": ["+250788000001"],
            "websites": ["https://techco.com"],
            "address": None,
            "social_handles": {},
        }
        vcf = scanner.to_vcf(result)
        assert "FN:Jane Smith" in vcf
        assert "TITLE:CTO" in vcf
        assert "ORG:TechCo Ltd" in vcf
        assert "EMAIL" in vcf
