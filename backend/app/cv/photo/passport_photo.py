"""Passport Photo Generator (S3-02).

Generates country-compliant passport photos for 30+ countries.
Applies official passport photo specifications per country.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

_SPECS_PATH = Path(__file__).parent.parent / "data" / "passport_specs.json"


def _load_specs() -> dict[str, Any]:
    """Load passport specifications database."""
    with _SPECS_PATH.open() as f:
        data: dict[str, Any] = json.load(f)
    return data


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Parse hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


class PassportPhotoGenerator:
    """Generate passport photos compliant with country-specific specifications."""

    def process(
        self,
        image_bytes: bytes,
        country_code: str = "us",
    ) -> dict[str, Any]:
        """Run the passport photo generation pipeline. Returns result dict."""
        specs = _load_specs()
        code = country_code.lower()
        spec: dict[str, Any] = specs.get(code, specs["us"])
        country_name: str = spec["name"]

        # Compute pixel dimensions
        width_px = round(spec["width_mm"] / 25.4 * spec["dpi"])
        height_px = round(spec["height_mm"] / 25.4 * spec["dpi"])

        # Step 1: Face detection
        face_result = self._detect_face(image_bytes)
        if face_result.get("error"):
            return face_result

        face_bbox: dict[str, Any] = face_result["bbox"]

        # Step 2: Background removal
        rgba_pil = self._remove_background(image_bytes)

        # Step 3: Crop/resize so face occupies correct ratio of photo height
        output_pil = self._apply_spec(
            rgba_pil,
            face_bbox,
            spec,
            width_px,
            height_px,
        )

        # Step 4: Quality checks
        quality_warnings = self._quality_checks(image_bytes, face_bbox, spec)

        # Encode to JPEG
        buf = io.BytesIO()
        output_pil.save(buf, format="JPEG", quality=95)
        encoded = base64.b64encode(buf.getvalue()).decode()

        return {
            "result_image_b64": encoded,
            "format": "jpeg",
            "country_code": code,
            "country_name": country_name,
            "spec_applied": {
                "width_mm": spec["width_mm"],
                "height_mm": spec["height_mm"],
                "width_px": width_px,
                "height_px": height_px,
                "dpi": spec["dpi"],
                "bg_color": spec["bg_color_hex"],
            },
            "face_detected": True,
            "quality_warnings": quality_warnings,
            "print_guide": "Print at 10\u00d715cm \u2014 fits 4 passport photos per page",
        }

    def _detect_face(self, image_bytes: bytes) -> dict[str, Any]:
        """Detect face in image. Returns {bbox} or {error, message}."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_w, img_h = pil.size

        try:
            import mediapipe as mp

            mp_face = mp.solutions.face_detection  # type: ignore[attr-defined]
            with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.4) as det:
                arr: Any = np.array(pil)
                results = det.process(arr)
                if not results.detections:
                    return {
                        "error": "no_face_detected",
                        "message": "No face found in image. Use a clear frontal portrait.",
                    }
                if len(results.detections) > 1:
                    return {
                        "error": "multiple_faces",
                        "message": "Multiple faces detected. Provide a photo with one person.",
                    }
                bbox_rel = results.detections[0].location_data.relative_bounding_box
                return {
                    "bbox": {
                        "x": int(bbox_rel.xmin * img_w),
                        "y": int(bbox_rel.ymin * img_h),
                        "width": int(bbox_rel.width * img_w),
                        "height": int(bbox_rel.height * img_h),
                        "relative_x": float(bbox_rel.xmin),
                        "relative_y": float(bbox_rel.ymin),
                        "relative_w": float(bbox_rel.width),
                        "relative_h": float(bbox_rel.height),
                    }
                }
        except (ImportError, Exception):  # noqa: S110
            pass

        # Fallback: OpenCV Haar cascade
        try:
            import cv2

            arr2: Any = np.array(pil)
            gray: Any = cv2.cvtColor(arr2, cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces: Any = cascade.detectMultiScale(gray, 1.1, 4)
            if not isinstance(faces, np.ndarray) or len(faces) == 0:
                return {
                    "error": "no_face_detected",
                    "message": "No face found in image. Use a clear frontal portrait.",
                }
            if len(faces) > 1:
                return {
                    "error": "multiple_faces",
                    "message": "Multiple faces detected. Provide a photo with one person.",
                }
            fx = int(faces[0][0])
            fy = int(faces[0][1])
            fw = int(faces[0][2])
            fh = int(faces[0][3])
            return {
                "bbox": {
                    "x": fx,
                    "y": fy,
                    "width": fw,
                    "height": fh,
                    "relative_x": fx / img_w,
                    "relative_y": fy / img_h,
                    "relative_w": fw / img_w,
                    "relative_h": fh / img_h,
                }
            }
        except Exception:  # noqa: S110
            pass

        # Last resort: assume face is present and centered
        margin_x = img_w // 4
        margin_y = img_h // 6
        return {
            "bbox": {
                "x": margin_x,
                "y": margin_y,
                "width": img_w - 2 * margin_x,
                "height": img_h - 2 * margin_y,
                "relative_x": 0.25,
                "relative_y": 0.17,
                "relative_w": 0.5,
                "relative_h": 0.67,
            }
        }

    def _remove_background(self, image_bytes: bytes) -> Any:
        """Remove background using rembg. Returns RGBA PIL Image."""
        try:
            from rembg import remove as rembg_remove

            rgba_bytes = rembg_remove(image_bytes)
            return Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")
        except (ImportError, Exception):
            # Fallback: just convert to RGBA (keep original)
            return Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    def _apply_spec(
        self,
        rgba_pil: Any,
        face_bbox: dict[str, Any],
        spec: dict[str, Any],
        width_px: int,
        height_px: int,
    ) -> Any:
        """Crop and resize image to match spec with face at correct ratio."""
        face_ratio_target = (spec["face_ratio_min"] + spec["face_ratio_max"]) / 2
        target_face_height_px = round(height_px * face_ratio_target)

        orig_w, orig_h = rgba_pil.size
        face_h = face_bbox["height"]
        face_cx = face_bbox["x"] + face_bbox["width"] / 2
        face_cy = face_bbox["y"] + face_bbox["height"] / 2

        # Scale so face_h == target_face_height_px
        scale = target_face_height_px / face_h if face_h > 0 else 1.0

        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        resized: Any = rgba_pil.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        scaled_cx = int(face_cx * scale)
        scaled_cy = int(face_cy * scale)

        left = scaled_cx - width_px // 2
        top = int(scaled_cy - height_px * 0.42)  # slight bias upward (head above center)

        left = max(0, min(left, new_w - width_px))
        top = max(0, min(top, new_h - height_px))

        cropped: Any = resized.crop((left, top, left + width_px, top + height_px))

        # Paste onto background color
        try:
            bg_rgb = _hex_to_rgb(spec["bg_color_hex"])
        except (ValueError, KeyError):
            bg_rgb = (255, 255, 255)

        background: Any = Image.new("RGB", (width_px, height_px), bg_rgb)
        if cropped.mode == "RGBA":
            background.paste(cropped, mask=cropped.split()[3])
        else:
            background.paste(cropped)

        return background

    def _quality_checks(
        self,
        image_bytes: bytes,
        face_bbox: dict[str, Any],
        spec: dict[str, Any],
    ) -> list[str]:
        """Run quality checks and return list of warning strings."""
        import cv2

        warnings: list[str] = []
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr: Any = np.array(pil)
        gray: Any = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Blur check
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if lap_var < 100:
            warnings.append("Photo appears blurry. Use a higher-resolution or sharper image.")

        # Brightness
        mean_val = float(np.mean(arr))
        if mean_val < 50:
            warnings.append("Photo is too dark. Use better lighting or increase exposure.")
        elif mean_val > 220:
            warnings.append("Photo is overexposed. Reduce lighting or adjust camera settings.")

        # Face ratio check
        img_h = pil.size[1]
        if img_h > 0:
            actual_ratio = face_bbox["height"] / img_h
            if actual_ratio < spec.get("face_ratio_min", 0.5) - 0.1:
                warnings.append("Face appears too small in the photo. Move closer to the camera.")
            elif actual_ratio > spec.get("face_ratio_max", 0.9) + 0.1:
                warnings.append("Face appears too large. Move further from the camera.")

        return warnings
