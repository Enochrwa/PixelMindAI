"""Tests for AI Profile Picture Styler (S4-04)."""

from __future__ import annotations

import base64
import io

from PIL import Image
import pytest


def _make_portrait(w: int = 120, h: int = 160) -> bytes:
    """Create a plain JPEG for testing."""
    pil = Image.new("RGB", (w, h), color=(160, 130, 100))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


class TestProfilePictureStyler:
    """Tests for ProfilePictureStyler.process()."""

    def test_returns_required_keys(self) -> None:
        """Result must contain styles, width, height."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait())
        assert "styles" in result
        assert "width" in result
        assert "height" in result

    def test_default_returns_four_styles(self) -> None:
        """Default call must return all 4 style variants."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait())
        assert len(result["styles"]) == 4

    def test_each_style_has_name_and_image(self) -> None:
        """Each style dict must include style_name and result_image_b64."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait())
        for style in result["styles"]:
            assert "style_name" in style
            assert "result_image_b64" in style
            assert len(style["result_image_b64"]) > 0

    def test_all_four_style_names_present(self) -> None:
        """Default should return corporate, linkedin, creative, minimal."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait())
        names = {s["style_name"] for s in result["styles"]}
        assert names == {"corporate", "linkedin", "creative", "minimal"}

    @pytest.mark.parametrize("style", ["corporate", "linkedin", "creative", "minimal"])
    def test_single_style_request(self, style: str) -> None:
        """Requesting a single style returns exactly one variant."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait(), styles=[style])
        assert len(result["styles"]) == 1
        assert result["styles"][0]["style_name"] == style

    def test_result_images_are_valid_jpeg(self) -> None:
        """All base64 images must decode to valid JPEGs."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait())
        for style in result["styles"]:
            img_bytes = base64.b64decode(style["result_image_b64"])
            pil = Image.open(io.BytesIO(img_bytes))
            assert pil.width > 0

    def test_unknown_style_ignored(self) -> None:
        """Unknown style names are filtered out; result falls back to all defaults."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(_make_portrait(), styles=["unknown_style_xyz"])
        # Should fall back to all 4 defaults when no valid style requested
        assert len(result["styles"]) == 4

    def test_minimal_custom_colour(self) -> None:
        """Minimal style honours custom colour without crashing."""
        from app.cv.photo.profile_picture_styler import ProfilePictureStyler

        result = ProfilePictureStyler().process(
            _make_portrait(),
            styles=["minimal"],
            minimal_colour_hex="#336699",
        )
        assert result["styles"][0]["style_name"] == "minimal"
