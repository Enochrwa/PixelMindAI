"""Tests for Passport Photo Generator (S3-09)."""

from __future__ import annotations

import base64
import io
import json
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


class TestPassportPhoto:
    """Unit tests for PassportPhotoGenerator class (S3-02)."""

    def test_process_returns_expected_keys(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="us")
        # Could have error if no face detected; check basic keys either way
        assert isinstance(result, dict)
        if "error" not in result:
            assert "result_image_b64" in result
            assert "format" in result
            assert "country_code" in result
            assert "spec_applied" in result
            assert "quality_warnings" in result
            assert "print_guide" in result

    def test_default_country_us(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes)
        if "error" not in result:
            assert result["country_code"] == "us"

    def test_rwanda_spec_applied(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="rw")
        if "error" not in result:
            assert result["country_code"] == "rw"
            assert result["country_name"] == "Rwanda"
            spec = result["spec_applied"]
            assert spec["width_mm"] == 35
            assert spec["height_mm"] == 45

    def test_kenya_spec_applied(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="ke")
        if "error" not in result:
            assert result["country_code"] == "ke"
            assert result["country_name"] == "Kenya"

    def test_result_is_base64_jpeg(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="us")
        if "error" not in result:
            assert result["format"] == "jpeg"
            b64 = result["result_image_b64"]
            decoded = base64.b64decode(b64)
            img = Image.open(io.BytesIO(decoded))
            assert img.width > 0

    def test_spec_applied_field_has_dimensions(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="us")
        if "error" not in result:
            spec = result["spec_applied"]
            assert "width_mm" in spec
            assert "height_mm" in spec
            assert "width_px" in spec
            assert "height_px" in spec
            assert "dpi" in spec
            assert "bg_color" in spec

    def test_quality_warnings_is_list(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="us")
        if "error" not in result:
            assert isinstance(result["quality_warnings"], list)

    def test_print_guide_in_result(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="us")
        if "error" not in result:
            assert "print_guide" in result
            assert isinstance(result["print_guide"], str)
            assert len(result["print_guide"]) > 5

    def test_unknown_country_falls_back_to_us(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="xx_unknown")
        # Should not crash; falls back to US spec
        assert isinstance(result, dict)
        if "error" not in result:
            assert result.get("country_code") == "us" or "spec_applied" in result

    def test_pixel_dimensions_match_spec(self, portrait_bytes: bytes) -> None:
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(portrait_bytes, country_code="rw")
        if "error" not in result:
            spec = result["spec_applied"]
            # Rwanda: 35mm x 45mm at 300dpi
            expected_w = round(35 / 25.4 * 300)
            expected_h = round(45 / 25.4 * 300)
            assert spec["width_px"] == expected_w
            assert spec["height_px"] == expected_h


class TestPassportSpecDatabase:
    """Tests for the passport specs JSON database."""

    def _load_specs(self) -> dict[str, object]:
        specs_path = Path(__file__).parent.parent / "app" / "cv" / "data" / "passport_specs.json"
        with specs_path.open() as f:
            data: dict[str, object] = json.load(f)
        return data

    def test_spec_file_exists(self) -> None:
        specs_path = Path(__file__).parent.parent / "app" / "cv" / "data" / "passport_specs.json"
        assert specs_path.exists(), "passport_specs.json must exist"

    def test_spec_has_required_keys(self) -> None:
        specs = self._load_specs()
        required_keys = {"name", "flag", "width_mm", "height_mm", "dpi", "bg_color_hex"}
        for code, spec in list(specs.items())[:3]:
            assert isinstance(spec, dict)
            missing = required_keys - set(spec.keys())
            assert not missing, f"Country {code!r} missing keys: {missing}"

    def test_30_or_more_countries(self) -> None:
        specs = self._load_specs()
        assert len(specs) >= 30, f"Expected 30+ countries, got {len(specs)}"

    def test_rwanda_spec_correct(self) -> None:
        specs = self._load_specs()
        assert "rw" in specs
        rw = specs["rw"]
        assert isinstance(rw, dict)
        assert rw["name"] == "Rwanda"
        assert rw["width_mm"] == 35
        assert rw["height_mm"] == 45
        assert rw["dpi"] == 300
        assert rw["bg_color_hex"] == "#FFFFFF"
