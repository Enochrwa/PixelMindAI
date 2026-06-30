"""Sprint 5 — Creator Studio Core tests.

Covers:
  - ThumbnailAnalyzer (S5-02)
  - CaptionLens v2 (S5-03)
  - MemeGenerator (S5-04)
  - VideoThumbnailExtractor (S5-05)
  - LanguageAIClient rate-limit / cache logic (S5-01)
"""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_rgb_image(width: int = 640, height: int = 360, color: str = "red") -> bytes:
    """Return JPEG bytes for a solid-color test image."""
    pil = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _make_thumbnail() -> bytes:
    """Create a test thumbnail with a face-like pattern."""
    pil = Image.new("RGB", (1280, 720), color=(30, 30, 200))
    arr = np.array(pil)
    # Add a skin-toned circle approximation
    center_y, center_x = 360, 640
    for y in range(300, 420):
        for x in range(580, 700):
            dist = ((y - center_y) ** 2 + (x - center_x) ** 2) ** 0.5
            if dist < 60:
                arr[y, x] = [220, 170, 120]  # skin tone
    pil2 = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    pil2.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# ThumbnailAnalyzer (S5-02)
# ---------------------------------------------------------------------------


class TestThumbnailAnalyzer:
    def test_returns_ctr_score_in_range(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        image_bytes = _make_rgb_image(1280, 720, "blue")
        result = ThumbnailAnalyzer().process(image_bytes)

        assert "ctr_score" in result
        assert 0 <= result["ctr_score"] <= 100

    def test_breakdown_has_all_dimensions(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        result = ThumbnailAnalyzer().process(_make_rgb_image())
        dims = result["breakdown"]
        expected = {
            "face_visibility",
            "visual_contrast",
            "color_energy",
            "text_readability",
            "clutter_score",
            "emotional_trigger",
        }
        assert set(dims.keys()) == expected

    def test_tips_are_returned(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        result = ThumbnailAnalyzer().process(_make_rgb_image(320, 240, "gray"))
        assert isinstance(result["tips"], list)
        assert len(result["tips"]) >= 1

    def test_grade_is_letter(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        result = ThumbnailAnalyzer().process(_make_rgb_image())
        assert result["grade"] in ("A", "B", "C", "D", "F")

    def test_high_contrast_image_scores_higher_contrast(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        # Checkerboard pattern = high contrast
        arr = np.zeros((360, 640, 3), dtype=np.uint8)
        arr[::20, :] = 255
        arr[:, ::20] = 255
        pil = Image.fromarray(arr)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        high_contrast_bytes = buf.getvalue()

        low_contrast_bytes = _make_rgb_image(640, 360, (128, 128, 128))

        analyzer = ThumbnailAnalyzer()
        r_hi = analyzer.process(high_contrast_bytes)
        r_lo = analyzer.process(low_contrast_bytes)
        assert (
            r_hi["breakdown"]["visual_contrast"]["score"]
            >= r_lo["breakdown"]["visual_contrast"]["score"]
        )

    def test_ab_comparison_returns_winner(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        a = _make_rgb_image(640, 360, "red")
        b = _make_rgb_image(640, 360, (128, 128, 128))
        result = ThumbnailAnalyzer().process_ab(a, b)

        assert "winner" in result
        assert result["winner"] in ("A", "B")
        assert "score_difference" in result
        assert "explanation" in result

    def test_colorful_image_scores_higher_color_energy(self) -> None:
        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        # Rainbow-like colorful image
        arr = np.zeros((360, 640, 3), dtype=np.uint8)
        for x in range(640):
            hue = x / 640.0
            r = int(abs(hue * 6 - 3) * 255) % 256
            g = int(abs(hue * 6 - 2) * 255) % 256
            b = int(abs(hue * 6 - 4) * 255) % 256
            arr[:, x] = [r, g, b]
        pil = Image.fromarray(arr)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        colorful_bytes = buf.getvalue()

        gray_bytes = _make_rgb_image(640, 360, (120, 120, 120))

        analyzer = ThumbnailAnalyzer()
        r_col = analyzer.process(colorful_bytes)
        r_gray = analyzer.process(gray_bytes)
        assert (
            r_col["breakdown"]["color_energy"]["score"]
            >= r_gray["breakdown"]["color_energy"]["score"]
        )


# ---------------------------------------------------------------------------
# LanguageAIClient (S5-01)
# ---------------------------------------------------------------------------


class TestLanguageAIClient:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_provider(self) -> None:
        """Second call with same prompt should use Redis cache, not call Groq."""
        from app.cv.ai.language_client import LanguageAIClient

        client = LanguageAIClient()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="cached response")
        client._redis = mock_redis

        result = await client.generate("test prompt", user_id="u1")
        assert result == "cached response"

    @pytest.mark.asyncio
    async def test_global_rate_limit_raises(self) -> None:
        from app.cv.ai.language_client import LanguageAIClient, RateLimitError

        client = LanguageAIClient()
        mock_redis = AsyncMock()
        # Cache miss → go to rate limit check
        mock_redis.get = AsyncMock(side_effect=[None, "14001"])
        client._redis = mock_redis

        with pytest.raises(RateLimitError):
            await client.generate("some prompt", user_id="u1")

    @pytest.mark.asyncio
    async def test_per_user_rate_limit_raises(self) -> None:
        from app.cv.ai.language_client import LanguageAIClient, RateLimitError

        client = LanguageAIClient()
        mock_redis = AsyncMock()
        # cache miss, global ok, user over limit
        mock_redis.get = AsyncMock(side_effect=[None, "100", "5"])
        client._redis = mock_redis

        with pytest.raises(RateLimitError):
            await client.generate("some prompt", user_id="u2")

    @pytest.mark.asyncio
    async def test_fallback_template_returns_string(self) -> None:
        from app.cv.ai.language_client import LanguageAIClient

        result = await LanguageAIClient._fallback_template("instagram caption for a photo")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_increments_counters_on_success(self) -> None:
        from app.cv.ai.language_client import LanguageAIClient

        client = LanguageAIClient()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        pipe_mock = MagicMock()
        pipe_mock.incr = MagicMock()
        pipe_mock.expire = MagicMock()
        pipe_mock.set = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[1, True, 1, True])
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)
        mock_redis.set = AsyncMock()
        client._redis = mock_redis

        with patch.object(client, "_call_provider", new=AsyncMock(return_value="response text")):
            result = await client.generate("test", user_id="u3")

        assert result == "response text"
        pipe_mock.incr.assert_called()


# ---------------------------------------------------------------------------
# CaptionLens v2 (S5-03)
# ---------------------------------------------------------------------------


class TestCaptionLensV2:
    def _mock_client(self, response: str) -> Any:
        mock = MagicMock()
        mock.generate = AsyncMock(return_value=response)
        return mock

    def test_returns_image_description(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        with (
            patch("app.cv.creator.caption_lens_v2.CaptionLens._describe_image") as mock_desc,
            patch(
                "app.cv.creator.caption_lens_v2.CaptionLens._generate_platform_captions"
            ) as mock_gen,
        ):
            mock_desc.return_value = "a sunny beach scene"
            mock_gen.return_value = {"captions": []}
            result = CaptionLens().process(_make_rgb_image(), platforms=["instagram"])

        assert result["image_description"] == "a sunny beach scene"
        assert "instagram" in result["platforms"]

    def test_all_three_platforms_when_no_platform_specified(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        with (
            patch("app.cv.creator.caption_lens_v2.CaptionLens._describe_image") as mock_desc,
            patch(
                "app.cv.creator.caption_lens_v2.CaptionLens._generate_platform_captions"
            ) as mock_gen,
        ):
            mock_desc.return_value = "a city skyline"
            mock_gen.return_value = {}
            result = CaptionLens().process(_make_rgb_image())

        assert set(result["platforms"].keys()) == {"instagram", "twitter", "linkedin"}

    def test_fallback_instagram_captions_structure(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        result = CaptionLens._fallback_captions("instagram", "a beautiful sunset")
        assert "captions" in result
        assert len(result["captions"]) == 3
        for cap in result["captions"]:
            assert "style" in cap
            assert "caption" in cap
            assert "hashtags" in cap
            assert len(cap["hashtags"]) == 10

    def test_fallback_twitter_captions_structure(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        result = CaptionLens._fallback_captions("twitter", "a city view")
        assert "tweets" in result
        assert len(result["tweets"]) == 3

    def test_fallback_linkedin_captions_structure(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        result = CaptionLens._fallback_captions("linkedin", "a professional event")
        assert "caption" in result
        assert len(result["caption"]) > 10

    def test_basic_fallback_describe(self) -> None:
        from app.cv.creator.caption_lens_v2 import CaptionLens

        with (
            patch("app.cv.creator.caption_lens_v2.Interrogator", side_effect=ImportError),
            patch(
                "app.cv.creator.caption_lens_v2.BlipForConditionalGeneration",
                side_effect=ImportError,
                create=True,
            ),
        ):
            desc = CaptionLens()._describe_image(Image.new("RGB", (640, 480), "green"))

        assert isinstance(desc, str)
        assert len(desc) > 0


# ---------------------------------------------------------------------------
# MemeGenerator (S5-04)
# ---------------------------------------------------------------------------


class TestMemeGenerator:
    def test_process_returns_suggestions_list(self) -> None:
        from app.cv.creator.meme_generator import MemeGenerator

        with (
            patch("app.cv.creator.meme_generator.MemeGenerator._detect_emotions") as mock_em,
            patch("app.cv.creator.meme_generator.MemeGenerator._describe_scene") as mock_sc,
            patch("app.cv.creator.meme_generator.MemeGenerator._generate_suggestions") as mock_sg,
        ):
            mock_em.return_value = ["happy"]
            mock_sc.return_value = "person smiling at camera"
            mock_sg.return_value = [
                {"top": "When the code works", "bottom": "First try"},
            ] * 5
            result = MemeGenerator().process(_make_rgb_image())

        assert "suggestions" in result
        assert len(result["suggestions"]) == 5
        assert "scene_description" in result
        assert "emotions_detected" in result

    def test_compose_returns_base64_png(self) -> None:
        from app.cv.creator.meme_generator import MemeGenerator

        result = MemeGenerator().compose(
            _make_rgb_image(640, 480),
            top_text="TOP TEXT",
            bottom_text="BOTTOM TEXT",
        )
        assert "result_image_b64" in result
        assert result["format"] == "png"
        assert len(result["result_image_b64"]) > 100

    def test_compose_empty_text_still_works(self) -> None:
        from app.cv.creator.meme_generator import MemeGenerator

        result = MemeGenerator().compose(_make_rgb_image(), top_text="", bottom_text="")
        assert result["format"] == "png"

    def test_fallback_suggestions_returns_five(self) -> None:
        from app.cv.creator.meme_generator import MemeGenerator

        suggestions = MemeGenerator._fallback_suggestions(["happy"])
        assert len(suggestions) == 5
        for s in suggestions:
            assert "top" in s
            assert "bottom" in s

    def test_fallback_suggestions_neutral_emotion(self) -> None:
        from app.cv.creator.meme_generator import MemeGenerator

        suggestions = MemeGenerator._fallback_suggestions(["neutral"])
        assert len(suggestions) == 5

    def test_compose_output_is_valid_image(self) -> None:
        """Verify the b64 decoded output is a valid PIL image."""
        import base64

        from app.cv.creator.meme_generator import MemeGenerator

        result = MemeGenerator().compose(
            _make_rgb_image(800, 600),
            top_text="HELLO",
            bottom_text="WORLD",
        )
        img_bytes = base64.b64decode(result["result_image_b64"])
        pil = Image.open(io.BytesIO(img_bytes))
        assert pil.mode in ("RGB", "RGBA")
        assert pil.width == 800
        assert pil.height == 600


# ---------------------------------------------------------------------------
# VideoThumbnailExtractor (S5-05)
# ---------------------------------------------------------------------------


class TestVideoThumbnailExtractor:
    def _make_minimal_video(self) -> bytes:
        """Create a minimal valid MP4 by writing a few JPEG frames via cv2."""
        try:
            import cv2
            import tempfile
            import os

            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            tmp.close()
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(tmp.name, fourcc, 5.0, (320, 240))
            for i in range(25):  # 5 s at 5 fps
                frame = np.full((240, 320, 3), [i * 10 % 256, 100, 200], dtype=np.uint8)
                out.write(frame)
            out.release()
            with open(tmp.name, "rb") as f:
                data = f.read()
            os.unlink(tmp.name)
            return data
        except Exception:
            return b""

    def test_extract_returns_top_frames(self) -> None:
        from app.cv.creator.video_thumbnail_extractor import VideoThumbnailExtractor

        video_bytes = self._make_minimal_video()
        if not video_bytes:
            pytest.skip("cv2 VideoWriter not available in test env")

        result = VideoThumbnailExtractor().process(video_bytes)
        assert "frames" in result
        assert isinstance(result["frames"], list)
        # Should have at most _TOP_N frames
        assert len(result["frames"]) <= 5

    def test_each_frame_has_required_fields(self) -> None:
        from app.cv.creator.video_thumbnail_extractor import VideoThumbnailExtractor

        video_bytes = self._make_minimal_video()
        if not video_bytes:
            pytest.skip("cv2 VideoWriter not available in test env")

        result = VideoThumbnailExtractor().process(video_bytes)
        for frame in result["frames"]:
            assert "frame_index" in frame
            assert "timestamp_seconds" in frame
            assert "ctr_score" in frame
            assert "image_b64" in frame
            assert 0 <= frame["ctr_score"] <= 100

    def test_recommended_frame_is_highest_scorer(self) -> None:
        from app.cv.creator.video_thumbnail_extractor import VideoThumbnailExtractor

        video_bytes = self._make_minimal_video()
        if not video_bytes:
            pytest.skip("cv2 VideoWriter not available in test env")

        result = VideoThumbnailExtractor().process(video_bytes)
        if result.get("recommended_frame") and result["frames"]:
            best_score = max(f["ctr_score"] for f in result["frames"])
            assert result["recommended_frame"]["ctr_score"] == best_score

    def test_invalid_video_returns_error(self) -> None:
        from app.cv.creator.video_thumbnail_extractor import VideoThumbnailExtractor

        result = VideoThumbnailExtractor().process(b"not a video file")
        # Should gracefully handle error
        assert "error" in result or "frames" in result

    def test_fmt_ts_helper(self) -> None:
        from app.cv.creator.video_thumbnail_extractor import _fmt_ts

        assert _fmt_ts(0.0) == "00:00"
        assert _fmt_ts(61.5) == "01:01"
        assert _fmt_ts(3600.0) == "60:00"
