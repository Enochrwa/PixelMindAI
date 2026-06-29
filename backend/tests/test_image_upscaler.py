"""Tests for Image Upscaler (S4-01)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    import pytest


def _make_image(w: int = 64, h: int = 64) -> bytes:
    """Create a minimal JPEG image for testing."""
    pil = Image.new("RGB", (w, h), color=(128, 64, 32))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


class TestImageUpscaler:
    """Tests for ImageUpscaler.process()."""

    def test_returns_required_keys(self) -> None:
        """Result dict must contain all expected keys."""
        from app.cv.photo.image_upscaler import ImageUpscaler

        result = ImageUpscaler().process(_make_image())
        required = {
            "result_image_b64",
            "comparison_b64",
            "format",
            "method",
            "original_width",
            "original_height",
            "upscaled_width",
            "upscaled_height",
            "scale_factor",
        }
        assert required.issubset(result.keys())

    def test_scale_factor_is_four(self) -> None:
        """Output dimensions must be 4x the input."""
        from app.cv.photo.image_upscaler import ImageUpscaler

        result = ImageUpscaler().process(_make_image(64, 48))
        assert result["scale_factor"] == 4
        assert result["upscaled_width"] == result["original_width"] * 4
        assert result["upscaled_height"] == result["original_height"] * 4

    def test_result_is_valid_jpeg(self) -> None:
        """Decoded result_image_b64 must be a parseable JPEG."""
        import base64

        from app.cv.photo.image_upscaler import ImageUpscaler

        result = ImageUpscaler().process(_make_image())
        img_bytes = base64.b64decode(result["result_image_b64"])
        pil = Image.open(io.BytesIO(img_bytes))
        assert pil.width > 0
        assert pil.height > 0

    def test_comparison_image_is_wider(self) -> None:
        """Comparison image is a side-by-side — same height, double width."""
        import base64

        from app.cv.photo.image_upscaler import ImageUpscaler

        img_bytes = _make_image(64, 48)
        result = ImageUpscaler().process(img_bytes)
        cmp_bytes = base64.b64decode(result["comparison_b64"])
        cmp_pil = Image.open(io.BytesIO(cmp_bytes))
        # comparison is original_w * 2 wide
        assert cmp_pil.width == result["original_width"] * 2
        assert cmp_pil.height == result["original_height"]

    def test_lanczos_fallback_is_used_when_no_onnx_model(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lanczos fallback is used when ONNX model file is absent."""
        from app.cv.photo import image_upscaler

        monkeypatch.setattr(image_upscaler, "_find_model", lambda: None)
        result = image_upscaler.ImageUpscaler().process(_make_image())
        assert result["method"] == "lanczos_fallback"

    def test_format_is_jpeg(self) -> None:
        """Output format field must be 'jpeg'."""
        from app.cv.photo.image_upscaler import ImageUpscaler

        result = ImageUpscaler().process(_make_image())
        assert result["format"] == "jpeg"
