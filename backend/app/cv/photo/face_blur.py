"""Face Blur / Privacy Protector (S4-03).

Detects all faces and applies blur, pixelation, black bar, or fill.
GDPR-compliant privacy protection for images.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

_VALID_MODES: frozenset[str] = frozenset(
    {"gaussian_blur", "pixelate", "black_bar", "full_face_fill"}
)


def _detect_faces_mediapipe(img_rgb: np.ndarray[Any, Any]) -> list[dict[str, int]]:
    """Detect all faces using MediaPipe, returns list of pixel bboxes."""
    import mediapipe as mp  # type: ignore[import-untyped,misc]

    h, w = img_rgb.shape[:2]
    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.3) as det:
        results = det.process(img_rgb)

    bboxes: list[dict[str, int]] = []
    if not results.detections:
        return bboxes

    for detection in results.detections:
        rb = detection.location_data.relative_bounding_box
        x1 = max(0, int(rb.xmin * w))
        y1 = max(0, int(rb.ymin * h))
        x2 = min(w, int((rb.xmin + rb.width) * w))
        y2 = min(h, int((rb.ymin + rb.height) * h))
        if x2 > x1 and y2 > y1:
            bboxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

    return bboxes


def _detect_faces_cv2(img_rgb: np.ndarray[Any, Any]) -> list[dict[str, int]]:
    """Fallback Haar-cascade face detection via OpenCV."""
    import cv2  # type: ignore[import-untyped,misc]

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    detections = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    bboxes: list[dict[str, int]] = []
    for x, y, fw, fh in detections:
        bboxes.append({"x1": int(x), "y1": int(y), "x2": int(x + fw), "y2": int(y + fh)})
    return bboxes


def _expand_bbox(
    bbox: dict[str, int], img_w: int, img_h: int, factor: float = 0.15
) -> dict[str, int]:
    """Expand bbox by factor% on each side for more complete blur coverage."""
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
    fw, fh = x2 - x1, y2 - y1
    pad_x = int(fw * factor)
    pad_y = int(fh * factor)
    return {
        "x1": max(0, x1 - pad_x),
        "y1": max(0, y1 - pad_y),
        "x2": min(img_w, x2 + pad_x),
        "y2": min(img_h, y2 + pad_y),
    }


class FaceBlur:
    """Apply privacy-protecting face blur/pixelation to all detected faces."""

    def process(
        self,
        image_bytes: bytes,
        mode: str = "gaussian_blur",
    ) -> dict[str, Any]:
        """Detect faces and apply anonymisation. Returns base64-encoded result."""
        if mode not in _VALID_MODES:
            mode = "gaussian_blur"

        pil_in = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_rgb = np.array(pil_in)
        img_h, img_w = img_rgb.shape[:2]

        # Detect faces
        try:
            bboxes = _detect_faces_mediapipe(img_rgb)
        except Exception:
            bboxes = []

        if not bboxes:
            try:
                bboxes = _detect_faces_cv2(img_rgb)
            except Exception:
                bboxes = []

        pil_out = pil_in.copy()

        for raw_bbox in bboxes:
            bbox = _expand_bbox(raw_bbox, img_w, img_h)
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            face_region = pil_out.crop((x1, y1, x2, y2))
            fw, fh = x2 - x1, y2 - y1

            if mode == "gaussian_blur":
                radius = max(15, min(fw, fh) // 5) | 1  # ensure odd
                blurred = face_region.filter(ImageFilter.GaussianBlur(radius=radius))
                pil_out.paste(blurred, (x1, y1))

            elif mode == "pixelate":
                pixel_size = max(8, min(fw, fh) // 10)
                small = face_region.resize(
                    (max(1, fw // pixel_size), max(1, fh // pixel_size)),
                    Image.Resampling.NEAREST,
                )
                pixelated = small.resize((fw, fh), Image.Resampling.NEAREST)
                pil_out.paste(pixelated, (x1, y1))

            elif mode == "black_bar":
                # Black bar over eye region (top 45-60% of face)
                eye_y1 = y1 + int(fh * 0.30)
                eye_y2 = y1 + int(fh * 0.60)
                bar = Image.new("RGB", (fw, eye_y2 - eye_y1), (0, 0, 0))
                pil_out.paste(bar, (x1, eye_y1))

            elif mode == "full_face_fill":
                fill_region = Image.new("RGB", (fw, fh), (40, 40, 40))
                pil_out.paste(fill_region, (x1, y1))

        buf = io.BytesIO()
        pil_out.save(buf, format="JPEG", quality=92, optimize=True)
        result_b64 = base64.b64encode(buf.getvalue()).decode()

        return {
            "result_image_b64": result_b64,
            "format": "jpeg",
            "faces_detected_count": len(bboxes),
            "mode_applied": mode,
            "face_bboxes": bboxes,
        }
