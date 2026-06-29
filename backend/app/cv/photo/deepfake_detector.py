"""Deepfake Detector (S4-05).

Multi-signal deepfake detection without requiring FaceForensics++ model:
  1. FFT frequency analysis — GAN artifacts in high frequencies
  2. Facial boundary consistency — edge coherence at face borders
  3. Eye reflection consistency — specular highlight symmetry
  4. Noise pattern analysis — sensor noise vs GAN noise patterns

Always includes a disclaimer: AI analysis only, not forensic evidence.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image

_DISCLAIMER = (
    "AI analysis only — not a forensic instrument. "
    "This tool provides a probability estimate based on statistical signals. "
    "Consult qualified digital forensics experts for legal or official matters."
)


def _fft_artifact_score(img_gray: np.ndarray[Any, Any]) -> tuple[float, str]:
    """Score based on FFT frequency spectrum.

    GAN-generated images often have characteristic grid-like high-frequency
    artifacts at Nyquist-related frequencies due to upsampling operations.
    Returns a score 0-100 where higher = more suspicious.
    """
    fft = np.fft.fft2(img_gray.astype(np.float32))
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.log1p(np.abs(fft_shift))

    h, w = magnitude.shape
    cy, cx = h // 2, w // 2

    # Sample cross patterns at typical GAN upsampling frequencies
    cross_band = 8
    top_q = magnitude[cy - cross_band : cy + cross_band, :].mean()
    side_q = magnitude[:, cx - cross_band : cx + cross_band].mean()
    overall = magnitude.mean()

    # Ratio of cross-pattern energy to overall energy
    cross_ratio = ((top_q + side_q) / 2.0) / (overall + 1e-8)

    # Real cameras produce smoother frequency distributions
    # GANs tend to produce slight cross-pattern boost
    if cross_ratio > 1.15:
        score = min(100.0, (cross_ratio - 1.0) * 200.0)
        desc = "Unusual frequency cross-pattern detected (common in GAN upsampling)."
    else:
        score = 0.0
        desc = "Frequency spectrum consistent with natural image."
    return score, desc


def _boundary_consistency_score(
    img_rgb: np.ndarray[Any, Any], bboxes: list[dict[str, int]]
) -> tuple[float, str]:
    """Analyse edge coherence at detected face boundaries."""
    import cv2  # type: ignore[import-untyped,misc]

    if not bboxes:
        return 0.0, "No faces detected — boundary analysis skipped."

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150).astype(np.float32) / 255.0

    scores: list[float] = []
    for bbox in bboxes[:3]:  # Limit to 3 faces
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        # Sample edge density inside vs just outside the face bounding box
        pad = 10
        inner = edges[y1:y2, x1:x2].mean() if (y2 > y1 and x2 > x1) else 0.0
        outer_y1 = max(0, y1 - pad)
        outer_x1 = max(0, x1 - pad)
        outer_y2 = min(edges.shape[0], y2 + pad)
        outer_x2 = min(edges.shape[1], x2 + pad)
        outer_region = edges[outer_y1:outer_y2, outer_x1:outer_x2]
        outer = (
            float(
                np.ma.masked_inside(
                    outer_region,
                    float(y1 - outer_y1) / max(outer_y2 - outer_y1, 1),
                    float(y2 - outer_y1) / max(outer_y2 - outer_y1, 1),
                ).mean()
            )
            if outer_region.size > 0
            else 0.0
        )

        # Large discontinuity in edge density = suspicious blending
        if inner > 0 and outer > 0:
            ratio = abs(inner - outer) / (inner + outer + 1e-8)
            scores.append(ratio)

    if not scores:
        return 0.0, "Boundary consistency looks natural."

    avg_ratio = float(np.mean(scores))
    if avg_ratio > 0.35:
        return min(
            80.0, avg_ratio * 150.0
        ), "Edge discontinuity at face boundary — possible compositing."
    return 0.0, "Face boundary edges appear consistent."


def _eye_reflection_score(
    img_rgb: np.ndarray[Any, Any], bboxes: list[dict[str, int]]
) -> tuple[float, str]:
    """Check for mismatched specular highlights in both eyes."""
    import cv2  # type: ignore[import-untyped,misc]

    if not bboxes:
        return 0.0, "No faces to analyse for eye reflections."

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    suspicious = 0
    checked = 0

    for bbox in bboxes[:2]:
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        fw, fh = x2 - x1, y2 - y1
        if fw < 20 or fh < 20:
            continue

        # Approximate eye regions (upper 35-55% of face)
        eye_y1 = y1 + int(fh * 0.30)
        eye_y2 = y1 + int(fh * 0.55)
        left_eye = gray[eye_y1:eye_y2, x1 : x1 + fw // 2]
        right_eye = gray[eye_y1:eye_y2, x1 + fw // 2 : x2]

        if left_eye.size == 0 or right_eye.size == 0:
            continue

        # Bright pixel count as proxy for specular highlights
        thresh = 220
        left_bright = float(np.sum(left_eye > thresh))
        right_bright = float(np.sum(right_eye > thresh))
        checked += 1

        # Real photos have roughly symmetric highlights in both eyes
        total = left_bright + right_bright
        if total > 0:
            asym = abs(left_bright - right_bright) / total
            if asym > 0.70:
                suspicious += 1

    if checked == 0:
        return 0.0, "Eye regions too small to analyse."

    ratio = suspicious / checked
    if ratio > 0.5:
        return 55.0, "Significant eye reflection asymmetry — common in AI face generation."
    return 0.0, "Eye reflections appear symmetric (consistent with real photo)."


def _noise_pattern_score(img_rgb: np.ndarray[Any, Any]) -> tuple[float, str]:
    """Analyse local noise patterns for GAN vs camera sensor signatures."""
    import cv2  # type: ignore[import-untyped,misc]

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    # Compute local variance in small patches — real cameras have sensor noise;
    # GANs produce smoother local patches (too-perfect skin texture)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = gray - blurred
    local_std = float(np.std(noise))

    # Suspiciously low noise in skin-toned regions can indicate GAN smoothing
    # We sample the centre-ish region (likely face/skin)
    h, w = gray.shape
    centre_patch = noise[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    centre_std = float(np.std(centre_patch))

    if centre_std < 1.5 and local_std > 3.0:
        return 45.0, "Unusually smooth centre region — possible AI skin generation."
    return 0.0, "Noise patterns are consistent with natural image capture."


def _detect_faces(img_rgb: np.ndarray[Any, Any]) -> list[dict[str, int]]:
    """Lightweight face detection for analysis bboxes."""
    try:
        import mediapipe as mp  # type: ignore[import-untyped,misc]

        mp_face = mp.solutions.face_detection
        h, w = img_rgb.shape[:2]
        with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.3) as det:
            results = det.process(img_rgb)
        if not results.detections:
            return []
        bboxes: list[dict[str, int]] = []
        for d in results.detections:
            rb = d.location_data.relative_bounding_box
            bboxes.append(
                {
                    "x1": max(0, int(rb.xmin * w)),
                    "y1": max(0, int(rb.ymin * h)),
                    "x2": min(w, int((rb.xmin + rb.width) * w)),
                    "y2": min(h, int((rb.ymin + rb.height) * h)),
                }
            )
        return bboxes
    except Exception:
        return []


def _build_heatmap(
    img_rgb: np.ndarray[Any, Any],
    bboxes: list[dict[str, int]],
    evidence: list[dict[str, Any]],
) -> str:
    """Build a simple annotated heatmap and return as base64 JPEG."""
    import cv2  # type: ignore[import-untyped,misc]

    annotated = img_rgb.copy()
    if bboxes:
        for bbox in bboxes:
            cv2.rectangle(
                annotated,
                (bbox["x1"], bbox["y1"]),
                (bbox["x2"], bbox["y2"]),
                (255, 100, 0),
                2,
            )
        cv2.putText(
            annotated,
            "AI Analysis",
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 100, 0),
            2,
        )

    buf = io.BytesIO()
    Image.fromarray(annotated).save(buf, format="JPEG", quality=85)
    _ = evidence  # used for context; rendered separately in frontend
    return base64.b64encode(buf.getvalue()).decode()


class DeepfakeDetector:
    """Estimate likelihood that an image contains AI-generated/manipulated faces."""

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Run all detection signals and return aggregated verdict."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_rgb = np.array(pil)
        gray = np.mean(img_rgb, axis=2)

        bboxes = _detect_faces(img_rgb)

        # Run all signals
        signals: list[tuple[float, str, str]] = [
            (*_fft_artifact_score(gray), "fft_frequency"),  # type: ignore[misc]
            (*_boundary_consistency_score(img_rgb, bboxes), "boundary_consistency"),  # type: ignore[misc]
            (*_eye_reflection_score(img_rgb, bboxes), "eye_reflection"),  # type: ignore[misc]
            (*_noise_pattern_score(img_rgb), "noise_pattern"),  # type: ignore[misc]
        ]

        evidence: list[dict[str, Any]] = []
        signal_scores: list[float] = []

        for score, desc, sig_type in signals:
            signal_scores.append(score)
            evidence.append(
                {"type": sig_type, "suspicious_score": round(score), "description": desc}
            )

        # Aggregate: weight FFT and boundary higher
        weights = [0.30, 0.30, 0.20, 0.20]
        authenticity_score = max(
            0,
            min(100, 100 - int(sum(s * w for s, w in zip(signal_scores, weights, strict=True)))),
        )

        if authenticity_score >= 75:
            verdict = "LIKELY_REAL"
        elif authenticity_score >= 45:
            verdict = "UNCERTAIN"
        else:
            verdict = "LIKELY_FAKE"

        heatmap_b64 = _build_heatmap(img_rgb, bboxes, evidence)

        return {
            "authenticity_score": authenticity_score,
            "verdict": verdict,
            "faces_detected": len(bboxes),
            "evidence": evidence,
            "heatmap_b64": heatmap_b64,
            "disclaimer": _DISCLAIMER,
        }
