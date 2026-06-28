"""Tests for Handwriting OCR (S2-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def handwriting_bytes() -> bytes:
    return (FIXTURES / "handwriting_sample.jpg").read_bytes()


class TestHandwritingOCR:
    """Unit tests for HandwritingOCR class."""

    def test_process_returns_expected_keys(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes)
        for key in [
            "raw_text",
            "paragraphs",
            "word_count",
            "language_detected",
            "confidence_score",
        ]:
            assert key in result, f"Missing key: {key}"

    def test_structure_mode_adds_blocks(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes, structure_mode=True)
        assert "structured_blocks" in result
        assert isinstance(result["structured_blocks"], list)

    def test_no_structure_mode(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes, structure_mode=False)
        assert "structured_blocks" not in result

    def test_word_count_is_positive(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes)
        assert isinstance(result["word_count"], int)
        assert result["word_count"] >= 0

    def test_confidence_is_valid(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes)
        assert 0 <= result["confidence_score"] <= 100

    def test_language_detected_is_string(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes)
        assert isinstance(result["language_detected"], str)
        assert result["language_detected"] in {"en", "fr"}

    def test_to_txt_export(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        ocr = HandwritingOCR()
        result = ocr.process(handwriting_bytes)
        txt = ocr.to_txt(result)
        assert isinstance(txt, str)

    def test_to_markdown_export(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        ocr = HandwritingOCR()
        result = ocr.process(handwriting_bytes, structure_mode=True)
        md = ocr.to_markdown(result)
        assert isinstance(md, str)

    def test_detect_language_french(self) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        lang = HandwritingOCR._detect_language("le chat est dans la maison et les enfants")
        assert lang == "fr"

    def test_detect_language_english(self) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        lang = HandwritingOCR._detect_language("the quick brown fox jumps over the lazy dog")
        assert lang == "en"

    def test_paragraphs_is_list(self, handwriting_bytes: bytes) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(handwriting_bytes)
        assert isinstance(result["paragraphs"], list)

    def test_process_does_not_raise_on_small_image(self) -> None:
        """Small/minimal images should not crash."""
        import io

        from PIL import Image

        from app.cv.tools.handwriting_ocr import HandwritingOCR

        tiny = Image.new("RGB", (100, 50), "white")
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        result = HandwritingOCR().process(buf.getvalue())
        assert isinstance(result, dict)


class TestHandwritingStructureDetection:
    """Tests for structure detection."""

    def test_heading_detected(self) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        blocks = HandwritingOCR._detect_structure([{"text": "MEETING NOTES", "confidence": 90}])
        assert any(b["type"] == "heading" for b in blocks)

    def test_bullet_list_detected(self) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        blocks = HandwritingOCR._detect_structure(
            [{"text": "- First item\n- Second item", "confidence": 80}]
        )
        assert any(b["type"] == "bullet_list" for b in blocks)

    def test_paragraph_fallback(self) -> None:
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        blocks = HandwritingOCR._detect_structure(
            [{"text": "This is a normal paragraph of text.", "confidence": 75}]
        )
        assert any(b["type"] == "paragraph" for b in blocks)
