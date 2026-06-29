"""Tests for Face Blur / Privacy Protector (S4-03)."""

from __future__ import annotations

import base64
import io

from PIL import Image
import pytest


def _make_image(w: int = 120, h: int = 160) -> bytes:
    """Create a solid-colour JPEG for testing."""
    pil = Image.new("RGB", (w, h), color=(180, 140, 100))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


class TestFaceBlur:
    """Tests for FaceBlur.process()."""

    def test_returns_required_keys(self) -> None:
        """Result must contain all expected output keys."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image())
        required = {
            "result_image_b64",
            "format",
            "faces_detected_count",
            "mode_applied",
            "face_bboxes",
        }
        assert required.issubset(result.keys())

    def test_result_image_is_valid_jpeg(self) -> None:
        """Decoded result must be a parseable JPEG."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image())
        img_bytes = base64.b64decode(result["result_image_b64"])
        pil = Image.open(io.BytesIO(img_bytes))
        assert pil.width > 0

    def test_faces_detected_count_is_int(self) -> None:
        """faces_detected_count must be a non-negative integer."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image())
        assert isinstance(result["faces_detected_count"], int)
        assert result["faces_detected_count"] >= 0

    def test_face_bboxes_is_list(self) -> None:
        """face_bboxes must be a list."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image())
        assert isinstance(result["face_bboxes"], list)

    @pytest.mark.parametrize(
        "mode",
        ["gaussian_blur", "pixelate", "black_bar", "full_face_fill"],
    )
    def test_all_valid_modes_accepted(self, mode: str) -> None:
        """All four blur modes must succeed and echo the mode back."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image(), mode=mode)
        assert result["mode_applied"] == mode

    def test_invalid_mode_falls_back_to_gaussian(self) -> None:
        """Unknown mode falls back to gaussian_blur."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image(), mode="laser_beam")
        assert result["mode_applied"] == "gaussian_blur"

    def test_format_is_jpeg(self) -> None:
        """Output format must be 'jpeg'."""
        from app.cv.photo.face_blur import FaceBlur

        result = FaceBlur().process(_make_image())
        assert result["format"] == "jpeg"
