"""Image Upscaler using Real-ESRGAN ONNX (S4-01).

Tiles large images into 256x256 patches with 10px overlap,
processes each patch through the ONNX model, and stitches back.
Falls back to Lanczos bicubic when the ONNX model is unavailable.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

_MODEL_PATHS: list[Path] = [
    Path("/app/models/realesr-general-x4v3.onnx"),
    Path("~/.cache/pixelmind/realesr-general-x4v3.onnx").expanduser(),
    Path(__file__).parent.parent.parent.parent / "infra" / "models" / "realesr-general-x4v3.onnx",
]

_TILE_SIZE: int = 256
_OVERLAP: int = 10
_SCALE: int = 4


def _find_model() -> Path | None:
    """Return the first existing ONNX model path, or None."""
    for p in _MODEL_PATHS:
        if p.exists():
            return p
    return None


def _upscale_lanczos(image: Image.Image, scale: int = _SCALE) -> Image.Image:
    """High-quality Lanczos bicubic fallback upscaler."""
    w, h = image.size
    return image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)


def _preprocess_tile(tile_arr: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Convert HWC uint8 BGR to NCHW float32 in [0, 1]."""
    tile_rgb = tile_arr[:, :, ::-1].astype(np.float32) / 255.0
    return np.transpose(tile_rgb, (2, 0, 1))[np.newaxis, ...]


def _postprocess_tile(output: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Convert NCHW float32 [0,1] back to HWC uint8 RGB."""
    arr = np.squeeze(output, axis=0)  # CHW
    arr = np.clip(arr, 0.0, 1.0)
    arr = np.transpose(arr, (1, 2, 0))  # HWC
    return (arr * 255.0).astype(np.uint8)


def _upscale_onnx(image: Image.Image, model_path: Path) -> Image.Image:
    """Tile-based ONNX upscaling.  Returns 4x upscaled PIL image."""
    import onnxruntime as rt

    session = rt.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )
    input_name: str = session.get_inputs()[0].name

    import cv2  # type: ignore[import-untyped,misc]

    img_bgr: np.ndarray[Any, Any] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    h, w = img_bgr.shape[:2]

    out_h, out_w = h * _SCALE, w * _SCALE
    out_img: np.ndarray[Any, Any] = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    step = _TILE_SIZE - _OVERLAP

    for y in range(0, h, step):
        for x in range(0, w, step):
            # Crop tile (with overlap)
            x1 = min(x, w - _TILE_SIZE) if w >= _TILE_SIZE else 0
            y1 = min(y, h - _TILE_SIZE) if h >= _TILE_SIZE else 0
            x2 = min(x1 + _TILE_SIZE, w)
            y2 = min(y1 + _TILE_SIZE, h)

            tile: np.ndarray[Any, Any] = img_bgr[y1:y2, x1:x2]

            # Pad to _TILE_SIZE if smaller
            th, tw = tile.shape[:2]
            if th < _TILE_SIZE or tw < _TILE_SIZE:
                tile = cv2.copyMakeBorder(
                    tile,
                    0,
                    _TILE_SIZE - th,
                    0,
                    _TILE_SIZE - tw,
                    cv2.BORDER_REFLECT_101,
                )

            inp = _preprocess_tile(tile)
            out_raw: list[np.ndarray[Any, Any]] = session.run(None, {input_name: inp})
            out_tile = _postprocess_tile(out_raw[0])  # HWC RGB

            # Paste (scaled) valid region back, trimming padding
            ox1, oy1 = x1 * _SCALE, y1 * _SCALE
            ox2, oy2 = x2 * _SCALE, y2 * _SCALE
            valid_w = (x2 - x1) * _SCALE
            valid_h = (y2 - y1) * _SCALE

            # out_tile is in RGB; convert to BGR for out_img
            out_tile_bgr = out_tile[:valid_h, :valid_w, ::-1]
            out_img[oy1:oy2, ox1:ox2] = out_tile_bgr

    out_rgb: np.ndarray[Any, Any] = cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(out_rgb)


class ImageUpscaler:
    """4x AI image upscaler using Real-ESRGAN ONNX (falls back to Lanczos)."""

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Upscale image 4x. Returns dict with base64-encoded result."""
        pil_in = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = pil_in.size

        model_path = _find_model()
        method: str

        if model_path is not None:
            try:
                pil_out = _upscale_onnx(pil_in, model_path)
                method = "realesrgan_onnx"
            except Exception:
                pil_out = _upscale_lanczos(pil_in)
                method = "lanczos_fallback"
        else:
            pil_out = _upscale_lanczos(pil_in)
            method = "lanczos_fallback"

        out_w, out_h = pil_out.size

        # Encode result
        buf = io.BytesIO()
        pil_out.save(buf, format="JPEG", quality=95, optimize=True)
        result_b64 = base64.b64encode(buf.getvalue()).decode()

        # Encode side-by-side comparison (scaled down to same display size as input)
        pil_in_disp = pil_in.copy()
        pil_out_disp = pil_out.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        comparison = Image.new("RGB", (orig_w * 2, orig_h))
        comparison.paste(pil_in_disp, (0, 0))
        comparison.paste(pil_out_disp, (orig_w, 0))
        cmp_buf = io.BytesIO()
        comparison.save(cmp_buf, format="JPEG", quality=90)
        comparison_b64 = base64.b64encode(cmp_buf.getvalue()).decode()

        return {
            "result_image_b64": result_b64,
            "comparison_b64": comparison_b64,
            "format": "jpeg",
            "method": method,
            "original_width": orig_w,
            "original_height": orig_h,
            "upscaled_width": out_w,
            "upscaled_height": out_h,
            "scale_factor": _SCALE,
        }
