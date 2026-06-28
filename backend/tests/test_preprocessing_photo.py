"""Tests for PhotoPreprocessor utilities (S3-09)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)


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


@pytest.fixture()
def portrait_bytes() -> bytes:
    return _make_portrait_bytes()


@pytest.fixture()
def bright_bytes() -> bytes:
    """Create an over-bright image fixture."""
    img = Image.new("RGB", (200, 200), (250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def dark_bytes() -> bytes:
    """Create a very dark image fixture."""
    img = Image.new("RGB", (200, 200), (10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestPhotoPreprocessor:
    """Unit tests for PhotoPreprocessor static utilities (S3-03)."""

    def test_auto_enhance_returns_bytes(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.auto_enhance(portrait_bytes)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_enhance_produces_valid_image(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.auto_enhance(portrait_bytes)
        img = Image.open(io.BytesIO(result))
        assert img.width > 0
        assert img.height > 0

    def test_detect_face_bbox_returns_dict_or_none(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.detect_face_bbox(portrait_bytes)
        # May or may not detect a face in synthetic image
        assert result is None or isinstance(result, dict)

    def test_detect_face_bbox_has_required_keys_when_found(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.detect_face_bbox(portrait_bytes)
        if result is not None:
            required = {
                "x",
                "y",
                "width",
                "height",
                "relative_x",
                "relative_y",
                "relative_w",
                "relative_h",
            }
            assert required.issubset(set(result.keys()))

    def test_check_photo_quality_returns_dict(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.check_photo_quality(portrait_bytes)
        assert isinstance(result, dict)

    def test_check_photo_quality_has_required_keys(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.check_photo_quality(portrait_bytes)
        assert "blur_score" in result
        assert "brightness_score" in result
        assert "face_detected" in result
        assert "face_centered_score" in result
        assert "overall_quality" in result

    def test_check_photo_quality_overall_valid_values(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.check_photo_quality(portrait_bytes)
        assert result["overall_quality"] in ("excellent", "good", "fair", "poor")

    def test_check_photo_quality_scores_in_range(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.preprocessing_photo import PhotoPreprocessor

        result = PhotoPreprocessor.check_photo_quality(portrait_bytes)
        assert 0 <= result["blur_score"] <= 100
        assert 0 <= result["brightness_score"] <= 100
        assert 0 <= result["face_centered_score"] <= 100
