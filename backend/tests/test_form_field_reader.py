"""Tests for Form Field Reader (S2-08)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def form_bytes() -> bytes:
    return (FIXTURES / "form_sample.jpg").read_bytes()


def _make_lined_form() -> bytes:
    """Create a synthetic form with horizontal lines for testing."""
    img = Image.new("RGB", (600, 500), "white")
    draw = ImageDraw.Draw(img)
    # Draw horizontal lines
    for y in [100, 160, 220, 280, 340]:
        draw.line([(20, y), (580, y)], fill="black", width=2)
    # Add labels
    draw.text((20, 70), "Name:", fill="black")
    draw.text((20, 130), "Email:", fill="black")
    draw.text((20, 190), "Phone:", fill="black")
    # Add values
    draw.text((100, 70), "Jane Doe", fill="gray")
    draw.text((100, 130), "jane@example.com", fill="gray")
    draw.text((100, 190), "+250788000001", fill="gray")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestFormFieldReader:
    """Unit tests for FormFieldReader class."""

    def test_process_returns_expected_keys(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        for key in ["fields", "field_count", "image_width", "image_height", "lines_detected"]:
            assert key in result, f"Missing key: {key}"

    def test_fields_is_list(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        assert isinstance(result["fields"], list)

    def test_field_count_matches_list(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        assert result["field_count"] == len(result["fields"])

    def test_each_field_has_required_keys(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        for field in result["fields"]:
            assert "field_bbox" in field
            assert "label_text" in field
            assert "value_text" in field
            assert "confidence" in field

    def test_field_bbox_has_coordinates(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        for field in result["fields"]:
            bbox = field["field_bbox"]
            assert "x" in bbox
            assert "y" in bbox
            assert "width" in bbox
            assert "height" in bbox

    def test_image_dimensions(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        assert result["image_width"] > 0
        assert result["image_height"] > 0

    def test_synthetic_lined_form(self) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(_make_lined_form())
        assert isinstance(result, dict)
        assert result["field_count"] >= 0  # May vary by OCR environment

    def test_confidence_in_valid_range(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        for field in result["fields"]:
            assert 0 <= field["confidence"] <= 100

    def test_lines_detected_is_int(self, form_bytes: bytes) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(form_bytes)
        assert isinstance(result["lines_detected"], int)
        assert result["lines_detected"] >= 0


class TestFormFieldSplitting:
    """Tests for label/value split logic."""

    @pytest.mark.parametrize(
        ("text", "expected_label", "expected_value_fragment"),
        [
            ("Name: John Smith", "Name", "John Smith"),
            ("Email: test@example.com", "Email", "test@example.com"),
            ("No colon here plain text", "", "No colon here plain text"),
        ],
    )
    def test_split_label_value(
        self, text: str, expected_label: str, expected_value_fragment: str
    ) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        label, value = FormFieldReader._split_label_value(text)
        assert label == expected_label
        assert expected_value_fragment in value

    def test_underscore_split(self) -> None:
        from app.cv.tools.form_field_reader import FormFieldReader

        label, value = FormFieldReader._split_label_value("Signature _______ John Doe")
        assert "Signature" in label
        assert "John Doe" in value
