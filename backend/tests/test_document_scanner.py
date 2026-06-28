"""Tests for Document Scanner (S2-08)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def document_bytes() -> bytes:
    return (FIXTURES / "document_sample.jpg").read_bytes()


def _make_jpeg(width: int = 400, height: int = 300, color: str = "white") -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestDocumentScanner:
    """Unit tests for DocumentScanner class."""

    def test_process_returns_expected_keys(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes)
        for key in ["result_image_b64", "format", "mode", "width_px", "height_px", "quality_score"]:
            assert key in result, f"Missing key: {key}"

    def test_mode_original_enhanced(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes, mode="original_enhanced")
        assert result["mode"] == "original_enhanced"

    def test_mode_black_and_white(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes, mode="black_and_white")
        assert result["mode"] == "black_and_white"

    def test_mode_grayscale(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes, mode="grayscale")
        assert result["mode"] == "grayscale"

    def test_invalid_mode_falls_back(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes, mode="nonexistent_mode")
        assert result["mode"] == "original_enhanced"

    def test_result_is_base64(self, document_bytes: bytes) -> None:
        import base64

        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes)
        b64 = result["result_image_b64"]
        decoded = base64.b64decode(b64)
        assert len(decoded) > 0

    def test_dimensions_are_positive(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes)
        assert result["width_px"] > 0
        assert result["height_px"] > 0

    def test_quality_score_range(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process(document_bytes)
        assert 0 <= result["quality_score"] <= 100

    def test_process_pdf_single_page(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        pdf_bytes = DocumentScanner().process_pdf([document_bytes], mode="black_and_white")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_process_pdf_multi_page(self, document_bytes: bytes) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        pages = [document_bytes, _make_jpeg(), _make_jpeg(color="lightblue")]
        pdf_bytes = DocumentScanner().process_pdf(pages, mode="grayscale")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_process_pdf_empty_list(self) -> None:
        from app.cv.tools.document_scanner import DocumentScanner

        result = DocumentScanner().process_pdf([])
        assert result == b""

    def test_angled_document_does_not_crash(self) -> None:
        """Simulated angled document (no perfect quadrilateral) should fallback gracefully."""
        from app.cv.tools.document_scanner import DocumentScanner

        # Skewed white image
        img_bytes = _make_jpeg(600, 800)
        result = DocumentScanner().process(img_bytes)
        assert isinstance(result, dict)
        assert result["width_px"] > 0


class TestDocumentScannerCV:
    """Test low-level CV operations."""

    def test_enhance_bw(self) -> None:
        import numpy as np

        from app.cv.tools.document_scanner import DocumentScanner

        img = np.ones((100, 100, 3), dtype=np.uint8) * 200
        enhanced = DocumentScanner._enhance(img, "black_and_white")
        assert enhanced.shape == img.shape

    def test_enhance_grayscale(self) -> None:
        import numpy as np

        from app.cv.tools.document_scanner import DocumentScanner

        img = np.ones((100, 100, 3), dtype=np.uint8) * 150
        enhanced = DocumentScanner._enhance(img, "grayscale")
        assert enhanced.shape == img.shape

    def test_quality_score_blank_image(self) -> None:
        import numpy as np

        from app.cv.tools.document_scanner import DocumentScanner

        blank = np.ones((100, 100, 3), dtype=np.uint8) * 255
        score = DocumentScanner._quality_score(blank)
        # Blank white image has near-zero sharpness
        assert score == 0
