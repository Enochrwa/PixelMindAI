"""Plant Disease Detector CV tool.

Detects plant diseases using color analysis and texture features.
Falls back to a rule-based approach when ML models are unavailable.
"""

from __future__ import annotations

import io
from typing import Any

import cv2
import numpy as np
from PIL import Image

from app.cv.preprocessing import ImagePreprocessor

# Common disease signatures by HSV color range
DISEASE_PROFILES: list[dict[str, Any]] = [
    {
        "name": "Brown Leaf Blight",
        "lower": np.array([5, 50, 50]),
        "upper": np.array([20, 255, 200]),
        "severity_threshold": 0.05,
    },
    {
        "name": "Yellow Mosaic Virus",
        "lower": np.array([20, 100, 100]),
        "upper": np.array([35, 255, 255]),
        "severity_threshold": 0.08,
    },
    {
        "name": "Powdery Mildew",
        "lower": np.array([0, 0, 200]),
        "upper": np.array([180, 30, 255]),
        "severity_threshold": 0.03,
    },
    {
        "name": "Anthracnose",
        "lower": np.array([0, 20, 20]),
        "upper": np.array([10, 100, 100]),
        "severity_threshold": 0.04,
    },
]


class PlantDiseaseDetector:
    """Detect diseases in plant images."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Analyze plant image for diseases."""
        img = self._pre.load_image(image_bytes)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_img, w_img = img.shape[:2]
        total_pixels = h_img * w_img

        # Compute green (healthy plant) coverage
        green_lower = np.array([35, 50, 50])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        green_ratio = float(np.sum(green_mask > 0)) / total_pixels

        detections: list[dict[str, Any]] = []
        for profile in DISEASE_PROFILES:
            mask = cv2.inRange(hsv, profile["lower"], profile["upper"])
            coverage = float(np.sum(mask > 0)) / total_pixels
            if coverage > profile["severity_threshold"]:
                severity = "low" if coverage < 0.10 else "medium" if coverage < 0.25 else "high"
                detections.append({
                    "disease": profile["name"],
                    "coverage_ratio": round(coverage, 4),
                    "severity": severity,
                })

        overall_health = "healthy" if not detections and green_ratio > 0.3 else \
                         "diseased" if detections else "unknown"

        pil = Image.open(io.BytesIO(image_bytes))
        w, h = pil.size
        return {
            "overall_health": overall_health,
            "green_coverage": round(green_ratio, 4),
            "diseases_detected": detections,
            "disease_count": len(detections),
            "image_dimensions": {"width": w, "height": h},
            "method": "hsv_color_analysis",
            "recommendations": _get_recommendations(detections),
        }


def _get_recommendations(detections: list[dict[str, Any]]) -> list[str]:
    recs: list[str] = []
    if not detections:
        return ["Plant appears healthy. Continue regular care."]
    for d in detections:
        name = d["disease"]
        if "Blight" in name:
            recs.append("Apply copper-based fungicide for blight control.")
        elif "Mosaic" in name:
            recs.append("Remove infected plants; control aphid vectors.")
        elif "Mildew" in name:
            recs.append("Improve air circulation; apply sulfur-based fungicide.")
        elif "Anthracnose" in name:
            recs.append("Remove affected leaves; apply chlorothalonil fungicide.")
    return recs or ["Consult an agronomist for precise diagnosis."]
