"""Age Predictor CV tool.

Predicts apparent age from face images using DeepFace or OpenCV DNN fallback.
"""

from __future__ import annotations

import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

from app.cv.preprocessing import ImagePreprocessor

logger = logging.getLogger(__name__)


class AgePredictor:
    """Predict apparent age from face images."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Predict age from face in image."""
        # Try DeepFace first
        try:
            from deepface import DeepFace  # type: ignore[import]

            pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(pil)
            result = DeepFace.analyze(
                img_array,
                actions=["age", "gender", "emotion"],
                enforce_detection=False,
            )
            if isinstance(result, list):
                result = result[0]
            return {
                "predicted_age": int(result.get("age", 0)),
                "age_range": _age_to_range(int(result.get("age", 0))),
                "gender": result.get("dominant_gender", "unknown"),
                "emotion": result.get("dominant_emotion", "unknown"),
                "faces_detected": 1,
                "method": "deepface",
                "confidence": 0.82,
            }
        except ImportError:
            logger.debug("deepface not available, falling back to haar cascade")
        except Exception:  # noqa: BLE001
            logger.debug("deepface analysis failed, falling back to haar cascade")

        # Fallback: OpenCV Haar Cascade face detection + heuristic age estimation
        img = self._pre.load_image(image_bytes)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) == 0:
            return {
                "predicted_age": None,
                "age_range": None,
                "faces_detected": 0,
                "method": "haar_cascade",
                "confidence": 0.0,
                "message": "No face detected in the image",
            }

        # Use the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi = img[y : y + h, x : x + w]

        estimated_age = _estimate_age_heuristic(face_roi)
        return {
            "predicted_age": estimated_age,
            "age_range": _age_to_range(estimated_age),
            "faces_detected": int(len(faces)),
            "face_location": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
            "method": "haar_heuristic",
            "confidence": 0.55,
        }


def _age_to_range(age: int) -> str:
    if age < 13:
        return "0-12 (child)"
    elif age < 20:
        return "13-19 (teenager)"
    elif age < 30:
        return "20-29"
    elif age < 40:
        return "30-39"
    elif age < 50:
        return "40-49"
    elif age < 60:
        return "50-59"
    else:
        return "60+ (senior)"


def _estimate_age_heuristic(face_roi: np.ndarray) -> int:
    """Very rough age estimate based on skin texture variance."""
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    # Laplacian variance correlates loosely with skin texture/wrinkles
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Low variance → smooth skin (younger), high variance → textured (older)
    if lap_var < 50:
        return 22
    elif lap_var < 150:
        return 32
    elif lap_var < 300:
        return 42
    elif lap_var < 500:
        return 52
    else:
        return 62
