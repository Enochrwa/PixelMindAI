"""Tests for Background Remover (S3-09)."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Generate synthetic fixtures programmatically (no binary blobs committed)
# ---------------------------------------------------------------------------


def _make_portrait_bytes() -> bytes:
    """Generate a synthetic portrait fixture."""
    portrait_path = FIXTURES / "portrait_sample.jpg"
    if not portrait_path.exists():
        img = Image.new("RGB", (400, 500), (210, 170, 130))
        draw = ImageDraw.Draw(img)
        draw.ellipse([130, 60, 270, 200], fill=(245, 220, 180))
        draw.ellipse([150, 85, 190, 110], fill=(80, 50, 30))
        draw.ellipse([210, 85, 250, 110], fill=(80, 50, 30))
        img.save(portrait_path, quality=90)
    return portrait_path.read_bytes()


def _make_product_bytes() -> bytes:
    """Generate a synthetic product fixture."""
    product_path = FIXTURES / "product_sample.jpg"
    if not product_path.exists():
        img = Image.new("RGB", (400, 400), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 300], fill=(220, 60, 60))
        img.save(product_path, quality=90)
    return product_path.read_bytes()


@pytest.fixture()
def portrait_bytes() -> bytes:
    return _make_portrait_bytes()


class TestBackgroundRemover:
    """Unit tests for BackgroundRemover class (S3-01)."""

    def test_process_returns_expected_keys(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes)
        assert "result_image_b64" in result
        assert "format" in result
        assert "method" in result
        assert "background_mode" in result
        assert "width_px" in result
        assert "height_px" in result

    def test_transparent_mode(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes, bg_mode="transparent")
        assert result["background_mode"] == "transparent"
        assert result["format"] == "png"

    def test_white_mode_returns_jpeg(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes, bg_mode="white")
        assert result["background_mode"] == "white"
        assert result["format"] == "jpeg"

    def test_color_mode(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(
            portrait_bytes, bg_mode="color", bg_color_hex="#FF0000"
        )
        assert result["background_mode"] == "color"
        assert result["format"] == "jpeg"

    def test_blur_mode(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes, bg_mode="blur", bg_blur_radius=21)
        assert result["background_mode"] == "blur"
        assert "result_image_b64" in result

    def test_result_image_b64_is_valid(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes)
        b64 = result["result_image_b64"]
        assert isinstance(b64, str)
        assert len(b64) > 100
        # Decode and verify it's a valid image
        decoded = base64.b64decode(b64)
        img = Image.open(io.BytesIO(decoded))
        assert img.width > 0
        assert img.height > 0

    def test_dimensions_reported(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes)
        assert isinstance(result["width_px"], int)
        assert isinstance(result["height_px"], int)
        assert result["width_px"] > 0
        assert result["height_px"] > 0

    def test_method_field_present(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(portrait_bytes)
        assert result["method"] in ("u2net", "grabcut")

    def test_process_bulk_returns_list(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        results = BackgroundRemover().process_bulk([portrait_bytes, portrait_bytes])
        assert isinstance(results, list)

    def test_process_bulk_count_matches(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        inputs = [portrait_bytes, portrait_bytes, portrait_bytes]
        results = BackgroundRemover().process_bulk(inputs)
        assert len(results) == 3

    def test_invalid_hex_does_not_crash(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        # Should not raise; should fall back to white
        result = BackgroundRemover().process(
            portrait_bytes, bg_mode="color", bg_color_hex="INVALID"
        )
        assert "result_image_b64" in result

    def test_small_image_does_not_crash(self) -> None:
        from app.cv.photo.background_remover import BackgroundRemover

        small = Image.new("RGB", (10, 10), (100, 100, 100))
        buf = io.BytesIO()
        small.save(buf, format="JPEG")
        result = BackgroundRemover().process(buf.getvalue())
        assert "result_image_b64" in result
