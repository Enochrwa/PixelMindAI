"""Resume / LinkedIn Photo Optimizer (S4-02).

Scores a professional headshot on 6 dimensions and returns actionable tips.
Uses MediaPipe FaceDetection, histogram analysis, rembg alpha analysis,
MediaPipe Face Mesh gaze, and DeepFace emotion (with graceful fallbacks).
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Dimension weights (must sum to 100)
# ---------------------------------------------------------------------------
_WEIGHTS: dict[str, int] = {
    "face_visibility": 20,
    "lighting_quality": 20,
    "background_quality": 20,
    "eye_contact": 15,
    "expression": 15,
    "composition": 10,
}


def _score_face_visibility(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str, str]:
    """Check face is detected, centred, and large enough."""
    try:
        import mediapipe as mp  # type: ignore[import-untyped,misc]

        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.4) as det:
            results = det.process(img_rgb)

        if not results.detections:
            return (
                0.0,
                "No face detected in the image.",
                "Ensure your face is clearly visible and centred.",
            )

        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        face_area = bbox.width * bbox.height
        # Ideal: face occupies 25-50% of image area
        if face_area < 0.10:
            score = 30.0
            issue = "Face is too small or far from camera."
            tip = "Move closer so your face fills at least 25% of the frame."
        elif face_area > 0.70:
            score = 60.0
            issue = "Face is cropped or too close."
            tip = "Pull back slightly — your head and shoulders should be visible."
        else:
            score = 100.0
            issue = ""
            tip = "Face size is ideal."
        return score, issue, tip

    except Exception:
        return 70.0, "", "Face detection unavailable — manual review recommended."


def _score_lighting(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str, str]:
    """Analyse brightness and contrast via histogram."""
    gray = np.mean(img_rgb, axis=2)
    mean_brightness = float(np.mean(gray))
    std_brightness = float(np.std(gray))

    issue, tip = "", ""
    score = 100.0

    if mean_brightness < 60:
        score = 30.0
        issue = "Image is too dark."
        tip = "Shoot near a window or add a ring light facing you."
    elif mean_brightness > 210:
        score = 40.0
        issue = "Image is overexposed."
        tip = "Reduce direct light behind you and avoid harsh overhead lighting."
    elif std_brightness < 20:
        score = 50.0
        issue = "Flat, low-contrast lighting."
        tip = "Use a key light at 45° to create gentle shadow definition."
    else:
        score = 100.0

    return score, issue, tip


def _score_background(image_bytes: bytes) -> tuple[float, str, str]:
    """Use rembg alpha channel to evaluate background uniformity."""
    try:
        from rembg import remove as rembg_remove  # type: ignore[import-untyped,misc]

        rgba_bytes = rembg_remove(image_bytes)
        rgba = Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")
        alpha = np.array(rgba)[:, :, 3]

        # Pixels with alpha < 128 are background
        bg_mask = alpha < 128
        bg_pixels = bg_mask.sum()
        total_pixels = alpha.size

        if bg_pixels == 0:
            return 50.0, "Could not isolate background.", "Use a plain, uncluttered background."

        # Load original RGB to assess background colour variance
        orig = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_arr = np.array(orig)
        bg_colours = orig_arr[bg_mask]
        colour_std = float(np.std(bg_colours))

        if colour_std < 15:
            score = 100.0
            issue = ""
            tip = "Background is clean and uniform."
        elif colour_std < 40:
            score = 70.0
            issue = "Background has slight texture or colour variation."
            tip = "Use a solid-colour wall or virtual background for a cleaner look."
        else:
            score = 30.0
            issue = "Busy or cluttered background detected."
            tip = "Use a plain white, grey, or navy background to keep focus on you."

        _ = bg_pixels, total_pixels  # used indirectly
        return score, issue, tip

    except Exception:
        return 65.0, "", "Background analysis unavailable."


def _score_eye_contact(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str, str]:
    """Estimate gaze direction using MediaPipe Face Mesh iris landmarks."""
    try:
        import mediapipe as mp  # type: ignore[import-untyped,misc]

        mp_mesh = mp.solutions.face_mesh
        with mp_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.4,
        ) as mesh:
            results = mesh.process(img_rgb)

        if not results.multi_face_landmarks:
            return 50.0, "Could not analyse eye gaze.", "Look directly into the camera lens."

        lms = results.multi_face_landmarks[0].landmark
        # Iris centres: left iris = 468, right iris = 473
        left_iris = lms[468]
        right_iris = lms[473]
        # Approximate deviation from centre (0.5, 0.5 is straight-ahead)
        avg_x = (left_iris.x + right_iris.x) / 2.0
        avg_y = (left_iris.y + right_iris.y) / 2.0
        dev_x = abs(avg_x - 0.5)
        dev_y = abs(avg_y - 0.5)
        deviation = (dev_x + dev_y) / 2.0

        if deviation < 0.06:
            return 100.0, "", "Great eye contact with the camera."
        elif deviation < 0.12:
            return (
                70.0,
                "Slight off-camera gaze detected.",
                "Look directly at the camera lens, not at your screen.",
            )
        else:
            return (
                30.0,
                "Not making eye contact with camera.",
                "Position your camera at eye level and look at the lens.",
            )

    except Exception:
        return 65.0, "", "Eye-contact analysis unavailable."


def _score_expression(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str, str]:
    """Score expression — neutral/happy scores highest, unhappy lowest."""
    try:
        from deepface import DeepFace  # type: ignore[import-untyped,misc]

        analysis = DeepFace.analyze(
            img_rgb,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )
        if isinstance(analysis, list):
            analysis = analysis[0]

        emotions: dict[str, float] = analysis.get("emotion", {})
        happy = emotions.get("happy", 0.0)
        neutral = emotions.get("neutral", 0.0)
        sad = emotions.get("sad", 0.0)
        angry = emotions.get("angry", 0.0)
        fear = emotions.get("fear", 0.0)

        positive = happy + neutral * 0.7
        negative = sad + angry + fear

        if positive > 60:
            return 100.0, "", "Confident and approachable expression."
        elif positive > 30:
            return (
                70.0,
                "Expression could be warmer.",
                "Try a gentle, natural smile — not too forced.",
            )
        elif negative > 40:
            return (
                30.0,
                "Expression appears tense or unhappy.",
                "Relax your face, take a breath, and try again.",
            )
        else:
            return (
                55.0,
                "Expression is hard to read.",
                "A small, genuine smile projects confidence.",
            )

    except Exception:
        return 65.0, "", "Expression analysis unavailable."


def _score_composition(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str, str]:
    """Check head/shoulders framing — top-third rule."""
    try:
        import mediapipe as mp  # type: ignore[import-untyped,misc]

        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.4) as det:
            results = det.process(img_rgb)

        if not results.detections:
            return (
                50.0,
                "Could not evaluate composition.",
                "Centre yourself in the frame with head-and-shoulders framing.",
            )

        bbox = results.detections[0].location_data.relative_bounding_box
        face_centre_y = bbox.ymin + bbox.height / 2.0

        # Ideal: face centre in top third (0.20-0.45)
        if 0.20 <= face_centre_y <= 0.50:
            return 100.0, "", "Framing follows the portrait composition rule."
        elif face_centre_y < 0.20:
            return (
                50.0,
                "Face is cut off at the top.",
                "Adjust camera angle or reframe so your full head is visible.",
            )
        else:
            return (
                60.0,
                "Too much headroom above you.",
                "Move up in the frame — your face should be in the upper third.",
            )

    except Exception:
        return 65.0, "", "Composition analysis unavailable."


class ResumePhotoOptimizer:
    """Score a professional headshot on 6 dimensions and provide actionable tips."""

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Analyse photo and return score breakdown with improvement tips."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_rgb = np.array(pil)

        dimensions: dict[str, dict[str, Any]] = {}
        tips: list[dict[str, str]] = []

        scorers = [
            ("face_visibility", _score_face_visibility, (img_rgb,)),
            ("lighting_quality", _score_lighting, (img_rgb,)),
            ("background_quality", _score_background, (image_bytes,)),
            ("eye_contact", _score_eye_contact, (img_rgb,)),
            ("expression", _score_expression, (img_rgb,)),
            ("composition", _score_composition, (img_rgb,)),
        ]

        weighted_total = 0.0
        for key, fn, args in scorers:  # type: ignore[assignment]
            raw_score, issue, tip = fn(*args)
            weight = _WEIGHTS[key]
            weighted_contrib = raw_score * weight / 100.0
            weighted_total += weighted_contrib
            dimensions[key] = {
                "score": round(raw_score),
                "weight": weight,
                "weighted_score": round(weighted_contrib, 1),
            }
            if issue:
                tips.append({"dimension": key, "issue": issue, "fix_suggestion": tip})

        total_score = round(min(100.0, weighted_total))

        if total_score >= 85:
            verdict = "Excellent professional photo."
        elif total_score >= 65:
            verdict = "Good photo with room for improvement."
        elif total_score >= 45:
            verdict = "Acceptable but several issues need attention."
        else:
            verdict = "Photo needs significant improvement before use professionally."

        return {
            "total_score": total_score,
            "verdict": verdict,
            "breakdown": dimensions,
            "tips": tips,
        }
