"""Tests for Menu Scanner (S2-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def menu_bytes() -> bytes:
    return (FIXTURES / "menu_sample.jpg").read_bytes()


@pytest.fixture()
def menu_french_bytes() -> bytes:
    return (FIXTURES / "menu_french.jpg").read_bytes()


class TestMenuScanner:
    """Unit tests for MenuScanner class."""

    def test_process_returns_expected_keys(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_bytes)
        for key in ["restaurant_name", "currency", "categories", "total_items", "confidence_score"]:
            assert key in result, f"Missing key: {key}"

    def test_categories_is_list(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_bytes)
        assert isinstance(result["categories"], list)

    def test_total_items_is_int(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_bytes)
        assert isinstance(result["total_items"], int)
        assert result["total_items"] >= 0

    def test_french_menu_detected(self, menu_french_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_french_bytes)
        assert isinstance(result, dict)
        assert "categories" in result

    def test_pos_format_flag(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_bytes, pos_format=True)
        assert "pos_export" in result
        assert isinstance(result["pos_export"], list)

    def test_to_csv_output(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        scanner = MenuScanner()
        result = scanner.process(menu_bytes)
        csv_out = scanner.to_csv(result)
        assert isinstance(csv_out, str)
        assert "Category" in csv_out or "Item" in csv_out

    def test_to_pos_csv_output(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        scanner = MenuScanner()
        result = scanner.process(menu_bytes)
        pos_csv = scanner.to_pos_csv(result)
        assert isinstance(pos_csv, str)
        assert "PLU" in pos_csv

    def test_confidence_score_valid(self, menu_bytes: bytes) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(menu_bytes)
        assert 0 <= result["confidence_score"] <= 100


class TestMenuCurrencyDetection:
    """Test currency detection in menu context."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Prix: RWF 4500", "RWF"),
            ("Price: $ 12.99", "USD"),
            ("Prix: € 8.50", "EUR"),
            ("Amount: KES 350", "KES"),
            ("No currency text here", "USD"),  # fallback
        ],
    )
    def test_detect_currency(self, text: str, expected: str) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner._detect_currency(text)
        assert result == expected


class TestMenuCategoryExtraction:
    """Test category/item extraction logic."""

    def test_extract_categories_with_prices(self) -> None:
        from unittest.mock import patch

        from app.cv.tools.menu_scanner import MenuScanner

        scanner = MenuScanner()
        menu_text = (
            "GOLDEN FORK\nSTARTERS\nSpring Rolls  1500\nSalad  800\nMAINS\nFish  4500\nBeef  6000"
        )
        mock_ocr = {
            "text": menu_text,
            "words": [],
            "confidence": 85,
        }
        with patch.object(scanner._ocr, "extract_text", return_value=mock_ocr):
            import io

            from PIL import Image

            img = Image.new("RGB", (100, 100), "white")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            result = scanner.process(buf.getvalue())

        assert result["restaurant_name"] == "GOLDEN FORK"
        assert len(result["categories"]) >= 1
        # Find items with prices
        all_items = [item for cat in result["categories"] for item in cat["items"]]
        assert len(all_items) >= 1

    def test_pos_list_has_plu(self) -> None:
        from app.cv.tools.menu_scanner import MenuScanner

        categories = [
            {"name": "Starters", "items": [{"name": "Salad", "price": 1500.0}]},
            {"name": "Mains", "items": [{"name": "Fish", "price": 4500.0}]},
        ]
        pos_list = MenuScanner._to_pos_list(categories, "RWF")
        assert len(pos_list) == 2
        assert pos_list[0]["plu"] == "1001"
        assert pos_list[1]["plu"] == "1002"
        assert all(item["currency"] == "RWF" for item in pos_list)
