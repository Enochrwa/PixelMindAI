"""Video Thumbnail Extractor — Sprint 5 (S5-05).

Extracts 20 evenly-spaced frames from a video file, scores each with
ThumbnailAnalyzer, and returns the top 5 by CTR score.

Limits: 50 MB (free), 100 MB (paid) -- enforced at the API layer.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

_NUM_FRAMES = 20
_TOP_N = 5


class VideoThumbnailExtractor:
    """Extract and score the best thumbnail frames from a video."""

    def process(self, video_bytes: bytes) -> dict[str, Any]:
        """Return top-N scored frames from *video_bytes*."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            return self._extract_and_score(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # ------------------------------------------------------------------

    def _extract_and_score(self, video_path: str) -> dict[str, Any]:
        try:
            import cv2  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError("opencv-python-headless is required") from exc

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video file", "frames": []}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        duration_s = total_frames / fps if fps > 0 else 0.0

        if total_frames <= 0:
            cap.release()
            return {"error": "Video has no frames", "frames": []}

        # Pick evenly-spaced frame indices
        step = max(1, total_frames // _NUM_FRAMES)
        frame_indices = [i * step for i in range(_NUM_FRAMES) if i * step < total_frames]

        from app.cv.creator.thumbnail_analyzer import ThumbnailAnalyzer

        analyzer = ThumbnailAnalyzer()
        scored_frames: list[dict[str, Any]] = []

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert BGR → RGB → JPEG bytes
            from PIL import Image

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=85)
            frame_bytes = buf.getvalue()

            try:
                analysis = analyzer.process(frame_bytes)
                ctr_score = analysis.get("ctr_score", 0.0)
            except Exception:
                ctr_score = 0.0

            timestamp_s = round(idx / fps, 2) if fps > 0 else 0.0
            b64 = base64.b64encode(frame_bytes).decode()

            scored_frames.append(
                {
                    "frame_index": idx,
                    "timestamp_seconds": timestamp_s,
                    "timestamp_formatted": _fmt_ts(timestamp_s),
                    "ctr_score": ctr_score,
                    "image_b64": b64,
                }
            )

        cap.release()

        # Sort by CTR score; keep top N
        scored_frames.sort(key=lambda x: x["ctr_score"], reverse=True)
        top_frames = scored_frames[:_TOP_N]

        recommended = top_frames[0] if top_frames else None

        return {
            "total_frames_extracted": len(scored_frames),
            "duration_seconds": round(duration_s, 2),
            "fps": round(fps, 2),
            "frames": top_frames,
            "recommended_frame": {
                "frame_index": recommended["frame_index"],
                "timestamp_seconds": recommended["timestamp_seconds"],
                "timestamp_formatted": recommended["timestamp_formatted"],
                "ctr_score": recommended["ctr_score"],
                "image_b64": recommended["image_b64"],
            }
            if recommended
            else None,
        }


def _fmt_ts(seconds: float) -> str:
    """Format seconds as MM:SS."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"
