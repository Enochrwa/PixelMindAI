"""Thumbnail Analyzer — Sprint 5 (S5-02).

Predicts YouTube thumbnail CTR on 6 weighted dimensions:
  1. Face visibility     (25 %)
  2. Visual contrast     (20 %)
  3. Color energy        (15 %)
  4. Text readability    (20 %)
  5. Clutter score       (10 %)
  6. Emotional trigger   (10 %)
"""

from __future__ import annotations

import io
import logging
from typing import Any, ClassVar

import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


class ThumbnailAnalyzer:
    """Analyse a thumbnail image and return a CTR-prediction score."""

    # Dimension weights (must sum to 1.0)
    _WEIGHTS: ClassVar[dict[str, float]] = {
        "face_visibility": 0.25,
        "visual_contrast": 0.20,
        "color_energy": 0.15,
        "text_readability": 0.20,
        "clutter_score": 0.10,
        "emotional_trigger": 0.10,
    }

    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Analyse *image_bytes* and return a structured CTR report."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(pil)

        scores: dict[str, float] = {}
        detail: dict[str, Any] = {}

        # 1 — Face visibility
        fv, fv_detail = self._score_face_visibility(pil, img_array)
        scores["face_visibility"] = fv
        detail["face_visibility"] = fv_detail

        # 2 — Visual contrast
        vc = self._score_visual_contrast(img_array)
        scores["visual_contrast"] = vc
        detail["visual_contrast"] = {"rms_contrast": round(vc, 1)}

        # 3 — Color energy
        ce, ce_detail = self._score_color_energy(img_array)
        scores["color_energy"] = ce
        detail["color_energy"] = ce_detail

        # 4 — Text readability
        tr, tr_detail = self._score_text_readability(pil, img_array)
        scores["text_readability"] = tr
        detail["text_readability"] = tr_detail

        # 5 — Clutter score (inverted: low clutter → high score)
        cl, cl_detail = self._score_clutter(pil)
        scores["clutter_score"] = cl
        detail["clutter_score"] = cl_detail

        # 6 — Emotional trigger
        et, et_detail = self._score_emotional_trigger(pil, img_array)
        scores["emotional_trigger"] = et
        detail["emotional_trigger"] = et_detail

        # Weighted aggregate
        ctr_score = round(sum(scores[k] * self._WEIGHTS[k] for k in self._WEIGHTS), 1)

        tips = self._generate_tips(scores)

        return {
            "ctr_score": ctr_score,
            "breakdown": {
                k: {
                    "score": round(scores[k], 1),
                    "weight_pct": int(self._WEIGHTS[k] * 100),
                    "detail": detail[k],
                }
                for k in self._WEIGHTS
            },
            "tips": tips,
            "grade": self._grade(ctr_score),
        }

    def process_ab(self, image_bytes_a: bytes, image_bytes_b: bytes) -> dict[str, Any]:
        """Compare two thumbnails; return both results + recommendation."""
        result_a = self.process(image_bytes_a)
        result_b = self.process(image_bytes_b)
        winner = "A" if result_a["ctr_score"] >= result_b["ctr_score"] else "B"
        diff = round(abs(result_a["ctr_score"] - result_b["ctr_score"]), 1)
        explanation = f"Thumbnail {winner} scores {diff} points higher. " + (
            "The margin is decisive — go with the winner."
            if diff >= 5
            else "The margin is small — test both with real audiences."
        )
        return {
            "thumbnail_a": result_a,
            "thumbnail_b": result_b,
            "winner": winner,
            "score_difference": diff,
            "explanation": explanation,
        }

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    def _score_face_visibility(
        self,
        pil: Image.Image,
        img_array: np.ndarray,  # noqa: ARG002
    ) -> tuple[float, dict[str, Any]]:
        """Score based on how large and prominent any face is."""
        faces_detected = 0
        largest_face_ratio = 0.0

        try:
            import mediapipe as mp  # type: ignore[import]

            with mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.4
            ) as fd:
                rgb = np.array(pil.convert("RGB"))
                result = fd.process(rgb)
                if result.detections:
                    faces_detected = len(result.detections)
                    for det in result.detections:
                        bb = det.location_data.relative_bounding_box
                        ratio = bb.width * bb.height
                        largest_face_ratio = max(largest_face_ratio, ratio)
        except Exception as _mp_err:
            logger.debug("mediapipe face detection failed, using skin fallback: %s", _mp_err)
            # Fallback: skin-tone heuristic
            hsv_arr = np.array(pil.convert("HSV"))  # type: ignore[arg-type]
            h, s, v = hsv_arr[:, :, 0], hsv_arr[:, :, 1], hsv_arr[:, :, 2]
            skin = (h < 30) & (s > 30) & (v > 80)  # type: ignore[operator]
            skin_ratio = float(np.sum(skin)) / skin.size
            if skin_ratio > 0.05:
                faces_detected = 1
                largest_face_ratio = float(skin_ratio)

        # Score: large face = high score
        if largest_face_ratio >= 0.15:
            score = 100.0
        elif largest_face_ratio > 0.05:
            score = 60.0 + (largest_face_ratio - 0.05) / 0.10 * 40.0
        elif faces_detected > 0:
            score = 40.0
        else:
            score = 10.0

        return min(score, 100.0), {
            "faces_detected": faces_detected,
            "largest_face_area_pct": round(largest_face_ratio * 100, 1),
        }

    def _score_visual_contrast(self, img_array: np.ndarray) -> float:
        """RMS contrast → 0-100 score."""
        gray = np.mean(img_array, axis=2)
        rms = float(np.sqrt(np.mean((gray - np.mean(gray)) ** 2)))
        # rms approx 0-127; map to 0-100
        return min(rms / 80.0 * 100.0, 100.0)

    def _score_color_energy(self, img_array: np.ndarray) -> tuple[float, dict[str, Any]]:
        """Saturation + hue diversity → score."""
        # Convert to HSV-like via PIL for accuracy
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        max_c = np.maximum(np.maximum(r, g), b).astype(float)
        min_c = np.minimum(np.minimum(r, g), b).astype(float)
        delta = max_c - min_c
        sat = np.where(max_c > 0, delta / max_c, 0.0)
        avg_sat = float(np.mean(sat))

        # Hue diversity via unique hue buckets
        hue_bucket = np.floor(np.where(max_c > 10, delta / (max_c + 1e-6) * 6, 0)).astype(int)
        unique_hues = len(np.unique(hue_bucket))
        diversity = min(unique_hues / 6.0, 1.0)

        score = avg_sat * 70.0 + diversity * 30.0
        return min(score * 100.0, 100.0), {
            "avg_saturation": round(avg_sat, 3),
            "hue_diversity_score": round(diversity, 3),
        }

    def _score_text_readability(
        self, pil: Image.Image, img_array: np.ndarray
    ) -> tuple[float, dict[str, Any]]:
        """Detect text presence and estimate readability."""
        text_found = False
        text_area_ratio = 0.0
        contrast_score = 0.0

        try:
            import easyocr  # type: ignore[import]

            reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            w, h = pil.size
            results = reader.readtext(img_array)
            if results:
                text_found = True
                total_area = sum(
                    abs((r[0][2][0] - r[0][0][0]) * (r[0][2][1] - r[0][0][1])) for r in results
                )
                text_area_ratio = total_area / (w * h)
                # Approximate contrast: brightest text region vs background
                contrast_score = float(np.mean([r[2] for r in results])) * 100.0
        except Exception as _ocr_err:
            logger.debug("easyocr unavailable, using edge fallback: %s", _ocr_err)
            # Fallback: edge density as proxy for text
            gray_pil = pil.convert("L")
            edges = gray_pil.filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edges)
            edge_density = float(np.mean(edge_arr > 30))
            if edge_density > 0.05:
                text_found = True
                text_area_ratio = float(edge_density)
                contrast_score = 60.0

        if not text_found:
            return 30.0, {"text_found": False}

        # Reward noticeable but not cluttered text
        area_score = min(text_area_ratio * 500.0, 100.0)
        score = area_score * 0.5 + min(contrast_score, 100.0) * 0.5
        return min(score, 100.0), {
            "text_found": True,
            "text_area_pct": round(text_area_ratio * 100, 2),
            "avg_confidence": round(contrast_score, 1),
        }

    def _score_clutter(self, pil: Image.Image) -> tuple[float, dict[str, Any]]:
        """Estimate visual clutter via edge complexity; less clutter = higher score."""
        small = pil.resize((224, 224))
        edges = np.array(small.convert("L").filter(ImageFilter.FIND_EDGES))
        edge_density = float(np.mean(edges > 20))
        # Low density = clean = high score; inverted
        score = max(0.0, (1.0 - edge_density * 5.0)) * 100.0
        return min(score, 100.0), {"edge_density": round(edge_density, 3)}

    def _score_emotional_trigger(
        self,
        pil: Image.Image,  # noqa: ARG002
        img_array: np.ndarray,
    ) -> tuple[float, dict[str, Any]]:
        """Detect emotional content (faces with strong expressions)."""
        emotion = "neutral"
        emotion_score = 40.0

        # Emotion weight map: high-arousal emotions drive CTR
        emotion_weights: dict[str, float] = {
            "happy": 90.0,
            "surprise": 85.0,
            "fear": 80.0,
            "angry": 75.0,
            "disgust": 65.0,
            "sad": 55.0,
            "neutral": 40.0,
        }

        try:
            from deepface import DeepFace  # type: ignore[import]

            result = DeepFace.analyze(
                img_path=img_array,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            faces = result if isinstance(result, list) else [result]
            if faces:
                dom = faces[0].get("dominant_emotion", "neutral")
                emotion = str(dom)
                emotion_score = emotion_weights.get(emotion, 40.0)
        except Exception as _err:
            logger.debug("deepface emotion detection failed: %s", _err)

        return emotion_score, {"dominant_emotion": emotion}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 80:
            return "A"
        if score >= 65:
            return "B"
        if score >= 50:
            return "C"
        if score >= 35:
            return "D"
        return "F"

    @staticmethod
    def _generate_tips(scores: dict[str, float]) -> list[dict[str, str]]:
        tips: list[dict[str, str]] = []

        if scores["face_visibility"] < 50:
            tips.append(
                {
                    "dimension": "Face Visibility",
                    "issue": "No prominent face detected",
                    "fix": "Add a close-up human face that fills at least 15% of the frame.",
                }
            )
        if scores["visual_contrast"] < 50:
            tips.append(
                {
                    "dimension": "Visual Contrast",
                    "issue": "Low contrast — thumbnail looks flat",
                    "fix": "Increase contrast and brightness to make elements pop.",
                }
            )
        if scores["color_energy"] < 40:
            tips.append(
                {
                    "dimension": "Color Energy",
                    "issue": "Muted or monochromatic colors",
                    "fix": "Use bold, saturated colors (red/yellow/orange) to grab attention.",
                }
            )
        if scores["text_readability"] < 40:
            tips.append(
                {
                    "dimension": "Text Readability",
                    "issue": "No readable text or text is too small",
                    "fix": (
                        "Add a bold title or number (e.g., '5 Tips') in large, contrasting font."
                    ),
                }
            )
        if scores["clutter_score"] < 40:
            tips.append(
                {
                    "dimension": "Clutter",
                    "issue": "Thumbnail is visually cluttered",
                    "fix": "Simplify the composition — focus on one main subject.",
                }
            )
        if scores["emotional_trigger"] < 50:
            tips.append(
                {
                    "dimension": "Emotional Trigger",
                    "issue": "Weak emotional expression",
                    "fix": "Use a surprised or happy expression to increase click impulse.",
                }
            )
        if not tips:
            tips.append(
                {
                    "dimension": "Overall",
                    "issue": "Strong thumbnail!",
                    "fix": "Consider A/B testing against a version with even higher contrast.",
                }
            )
        return tips
