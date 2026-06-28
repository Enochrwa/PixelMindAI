"""Photo preprocessing utilities (S3-03).

Shared utilities used by Background Remover, Passport Photo, and future photo tools.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance


class PhotoPreprocessor:
    """Shared photo preprocessing utilities for portrait and product images."""

    @staticmethod
    def auto_enhance(image_bytes: bytes) -> bytes:
        """Apply smart brightness + saturation boost for portrait photos."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr: Any = np.array(pil)
        mean_brightness = float(np.mean(arr))

        enhanced: Any = pil
        if mean_brightness < 120:
            enhanced = ImageEnhance.Brightness(enhanced).enhance(1.05)
        enhanced = ImageEnhance.Color(enhanced).enhance(1.1)

        buf = io.BytesIO()
        enhanced.save(buf, format="JPEG", quality=92)
        return buf.getvalue()

    @staticmethod
    def detect_face_bbox(image_bytes: bytes) -> dict[str, Any] | None:
        """Detect primary face bounding box using MediaPipe or OpenCV Haar cascade.

        Returns {x, y, width, height, relative_x, relative_y, relative_w, relative_h}
        or None if no face detected.
        """
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_w, img_h = pil.size

        try:
            import mediapipe as mp

            mp_face = mp.solutions.face_detection  # type: ignore[attr-defined]
            with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.4) as detector:
                import numpy as _np

                arr: Any = _np.array(pil)
                results = detector.process(arr)
                if not results.detections:
                    return None
                det = results.detections[0]
                bbox = det.location_data.relative_bounding_box
                rel_x = float(bbox.xmin)
                rel_y = float(bbox.ymin)
                rel_w = float(bbox.width)
                rel_h = float(bbox.height)
                x = int(rel_x * img_w)
                y = int(rel_y * img_h)
                w = int(rel_w * img_w)
                h = int(rel_h * img_h)
                return {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "relative_x": rel_x,
                    "relative_y": rel_y,
                    "relative_w": rel_w,
                    "relative_h": rel_h,
                }
        except (ImportError, Exception):  # noqa: S110
            pass

        # Fallback: OpenCV Haar cascade
        try:
            import cv2
            import numpy as _np

            arr2: Any = _np.array(pil)
            gray: Any = cv2.cvtColor(arr2, cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces: Any = cascade.detectMultiScale(gray, 1.1, 4)
            if not isinstance(faces, _np.ndarray) or len(faces) == 0:
                return None
            x_c = int(faces[0][0])
            y_c = int(faces[0][1])
            w_c = int(faces[0][2])
            h_c = int(faces[0][3])
            return {
                "x": x_c,
                "y": y_c,
                "width": w_c,
                "height": h_c,
                "relative_x": x_c / img_w,
                "relative_y": y_c / img_h,
                "relative_w": w_c / img_w,
                "relative_h": h_c / img_h,
            }
        except Exception:
            return None

    @staticmethod
    def check_photo_quality(image_bytes: bytes) -> dict[str, Any]:
        """Score photo quality on 4 dimensions.

        Returns {
            blur_score: int (0-100, higher=sharper),
            brightness_score: int (0-100, 50=ideal),
            face_detected: bool,
            face_centered_score: int (0-100),
            overall_quality: 'excellent'|'good'|'fair'|'poor',
        }
        """
        import cv2

        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr: Any = np.array(pil)
        gray: Any = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Blur score: Laplacian variance, clamp to 0-100
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur_score = int(min(100, lap_var / 5))

        # Brightness score: 0=too dark, 50=ideal, 100=too bright
        mean_val = float(np.mean(arr))
        brightness_score = int(mean_val / 2.55)

        # Face detection
        face_bbox = PhotoPreprocessor.detect_face_bbox(image_bytes)
        face_detected = face_bbox is not None

        # Face centering score
        face_centered_score = 0
        if face_bbox:
            img_w, img_h = pil.size
            cx = face_bbox["x"] + face_bbox["width"] / 2
            cy = face_bbox["y"] + face_bbox["height"] / 2
            center_dist_x = abs(cx / img_w - 0.5)
            center_dist_y = abs(cy / img_h - 0.5)
            face_centered_score = int(100 - (center_dist_x + center_dist_y) * 100)
            face_centered_score = max(0, min(100, face_centered_score))

        # Overall quality
        scores = [blur_score, min(100, abs(brightness_score - 50) * -2 + 100)]
        avg = sum(scores) / len(scores)
        if avg >= 75:
            overall_quality = "excellent"
        elif avg >= 55:
            overall_quality = "good"
        elif avg >= 35:
            overall_quality = "fair"
        else:
            overall_quality = "poor"

        return {
            "blur_score": blur_score,
            "brightness_score": brightness_score,
            "face_detected": face_detected,
            "face_centered_score": face_centered_score,
            "overall_quality": overall_quality,
        }
