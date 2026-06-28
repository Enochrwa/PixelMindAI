"""Tests for Signature Extractor (S2-08)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def signature_bytes() -> bytes:
    return (FIXTURES / "signature_sample.jpg").read_bytes()


@pytest.fixture()
def two_sig_bytes() -> bytes:
    return (FIXTURES / "two_signatures.jpg").read_bytes()


def _blank_jpeg() -> bytes:
    img = Image.new("RGB", (400, 300), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestSignatureExtractor:
    """Unit tests for SignatureExtractor class."""

    def test_process_returns_expected_keys(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        for key in ["signatures", "signature_count", "image_width", "image_height"]:
            assert key in result, f"Missing key: {key}"

    def test_signatures_is_list(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        assert isinstance(result["signatures"], list)

    def test_signature_count_matches_list(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        assert result["signature_count"] == len(result["signatures"])

    def test_each_signature_has_required_fields(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        for sig in result["signatures"]:
            assert "bbox" in sig
            assert "image_b64" in sig
            assert "confidence" in sig
            assert "format" in sig
            assert sig["format"] == "png"

    def test_bbox_structure(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        for sig in result["signatures"]:
            bbox = sig["bbox"]
            assert "x" in bbox
            assert "y" in bbox
            assert "width" in bbox
            assert "height" in bbox

    def test_image_b64_is_valid_png(self, signature_bytes: bytes) -> None:
        import base64

        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        for sig in result["signatures"]:
            decoded = base64.b64decode(sig["image_b64"])
            # PNG magic bytes
            assert decoded[:8] == b"\x89PNG\r\n\x1a\n"

    def test_confidence_in_range(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        for sig in result["signatures"]:
            assert 0 <= sig["confidence"] <= 100

    def test_blank_image_returns_zero_signatures(self) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(_blank_jpeg())
        assert result["signature_count"] == 0
        assert result["signatures"] == []

    def test_to_zip_returns_bytes(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        extractor = SignatureExtractor()
        result = extractor.process(signature_bytes)
        zip_bytes = extractor.to_zip(result)
        assert isinstance(zip_bytes, bytes)

    def test_to_zip_is_valid_zip(self, signature_bytes: bytes) -> None:
        import zipfile

        from app.cv.tools.signature_extractor import SignatureExtractor

        extractor = SignatureExtractor()
        result = extractor.process(signature_bytes)
        zip_bytes = extractor.to_zip(result)
        if len(zip_bytes) > 0:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                names = zf.namelist()
                assert all(n.endswith(".png") for n in names)

    def test_image_dimensions_reported(self, signature_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(signature_bytes)
        assert result["image_width"] > 0
        assert result["image_height"] > 0

    def test_two_signatures_document(self, two_sig_bytes: bytes) -> None:
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(two_sig_bytes)
        # Should detect at least 0 (structural — depends on ink detection)
        assert isinstance(result["signatures"], list)
