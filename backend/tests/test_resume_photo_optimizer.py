"""Tests for Resume Photo Optimizer (S4-02)."""

from __future__ import annotations

import io

from PIL import Image
import pytest


def _make_portrait(w: int = 200, h: int = 300) -> bytes:
    """Create a plain portrait-sized JPEG for testing."""
    pil = Image.new("RGB", (w, h), color=(200, 180, 160))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


class TestResumePhotoOptimizer:
    """Tests for ResumePhotoOptimizer.process()."""

    def test_returns_required_keys(self) -> None:
        """Result must contain total_score, verdict, breakdown, tips."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        assert "total_score" in result
        assert "verdict" in result
        assert "breakdown" in result
        assert "tips" in result

    def test_total_score_in_range(self) -> None:
        """total_score must be 0-100."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        assert 0 <= result["total_score"] <= 100

    def test_breakdown_contains_six_dimensions(self) -> None:
        """Breakdown must include all 6 scoring dimensions."""
        from app.cv.photo.resume_photo_optimizer import (
            _WEIGHTS,
            ResumePhotoOptimizer,
        )

        result = ResumePhotoOptimizer().process(_make_portrait())
        assert set(result["breakdown"].keys()) == set(_WEIGHTS.keys())

    def test_each_dimension_has_score_and_weight(self) -> None:
        """Each dimension dict must include 'score' and 'weight' keys."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        for _dim, info in result["breakdown"].items():
            assert "score" in info
            assert "weight" in info

    def test_tips_is_list(self) -> None:
        """Tips must be a list (possibly empty)."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        assert isinstance(result["tips"], list)

    def test_tips_have_dimension_and_fix(self) -> None:
        """Any tip must include dimension, issue, and fix_suggestion keys."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        for tip in result["tips"]:
            assert "dimension" in tip
            assert "issue" in tip
            assert "fix_suggestion" in tip

    def test_verdict_is_string(self) -> None:
        """Verdict must be a non-empty string."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        result = ResumePhotoOptimizer().process(_make_portrait())
        assert isinstance(result["verdict"], str)
        assert len(result["verdict"]) > 0

    @pytest.mark.parametrize("brightness", [20, 240])
    def test_dark_and_bright_images_penalised(self, brightness: int) -> None:
        """Very dark or very bright images should score ≤70 for lighting."""
        from app.cv.photo.resume_photo_optimizer import ResumePhotoOptimizer

        pil = Image.new("RGB", (200, 300), color=(brightness, brightness, brightness))
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        result = ResumePhotoOptimizer().process(buf.getvalue())
        lighting_score = result["breakdown"]["lighting_quality"]["score"]
        assert lighting_score <= 70
