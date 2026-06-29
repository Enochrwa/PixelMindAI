"""Tests for Deepfake Detector (S4-05)."""

from __future__ import annotations

import io

from PIL import Image


def _make_image(w: int = 128, h: int = 160) -> bytes:
    """Create a solid-colour JPEG for testing."""
    pil = Image.new("RGB", (w, h), color=(180, 150, 120))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


def _make_noisy_image(w: int = 128, h: int = 160) -> bytes:
    """Create a JPEG with random noise (more realistic for FFT tests)."""
    import numpy as np

    arr = (np.random.rand(h, w, 3) * 255).astype("uint8")
    pil = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    pil.save(buf, format="JPEG")
    return buf.getvalue()


class TestDeepfakeDetector:
    """Tests for DeepfakeDetector.process()."""

    def test_returns_required_keys(self) -> None:
        """Result must contain all expected output keys."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        required = {
            "authenticity_score",
            "verdict",
            "faces_detected",
            "evidence",
            "heatmap_b64",
            "disclaimer",
        }
        assert required.issubset(result.keys())

    def test_authenticity_score_in_range(self) -> None:
        """authenticity_score must be 0-100."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert 0 <= result["authenticity_score"] <= 100

    def test_verdict_is_valid_string(self) -> None:
        """Verdict must be one of three valid strings."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert result["verdict"] in {"LIKELY_REAL", "UNCERTAIN", "LIKELY_FAKE"}

    def test_evidence_is_list_of_four(self) -> None:
        """Evidence list must contain exactly 4 signal entries."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) == 4

    def test_each_evidence_has_required_keys(self) -> None:
        """Each evidence item must include type, suspicious_score, description."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        for ev in result["evidence"]:
            assert "type" in ev
            assert "suspicious_score" in ev
            assert "description" in ev

    def test_disclaimer_always_present(self) -> None:
        """Disclaimer must always be returned and be non-empty."""
        from app.cv.photo.deepfake_detector import _DISCLAIMER, DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert result["disclaimer"] == _DISCLAIMER
        assert len(result["disclaimer"]) > 50

    def test_heatmap_is_nonempty_b64(self) -> None:
        """heatmap_b64 must be a non-empty base64 string."""
        import base64

        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert len(result["heatmap_b64"]) > 0
        # Must decode without error
        decoded = base64.b64decode(result["heatmap_b64"])
        assert len(decoded) > 0

    def test_faces_detected_is_int(self) -> None:
        """faces_detected must be a non-negative integer."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_image())
        assert isinstance(result["faces_detected"], int)
        assert result["faces_detected"] >= 0

    def test_noisy_image_does_not_crash(self) -> None:
        """Highly noisy image must complete without raising exceptions."""
        from app.cv.photo.deepfake_detector import DeepfakeDetector

        result = DeepfakeDetector().process(_make_noisy_image())
        assert "authenticity_score" in result

    def test_real_photo_likely_real(self) -> None:
        """A natural gradient image should score as LIKELY_REAL or UNCERTAIN."""
        import numpy as np

        from app.cv.photo.deepfake_detector import DeepfakeDetector

        # Smooth gradient — no GAN artifacts
        arr = np.zeros((160, 128, 3), dtype=np.uint8)
        for i in range(160):
            arr[i, :, :] = int(i / 160 * 200 + 30)
        pil = Image.fromarray(arr, "RGB")
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=95)
        result = DeepfakeDetector().process(buf.getvalue())
        assert result["verdict"] in {"LIKELY_REAL", "UNCERTAIN"}
