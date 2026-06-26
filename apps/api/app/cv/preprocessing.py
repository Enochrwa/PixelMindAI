"""Reusable OpenCV image preprocessing pipeline used by ALL CV tools (S1-02)."""

from __future__ import annotations

import io
import urllib.request

import cv2
import numpy as np
from PIL import Image


class ImagePreprocessor:
    """Stateless preprocessing utilities for CV pipelines."""

    @staticmethod
    def load_image(source: bytes | str) -> np.ndarray:
        """Load an image from bytes or URL into a BGR numpy array."""
        raw: bytes
        if isinstance(source, str):
            with urllib.request.urlopen(source) as resp:  # noqa: S310
                raw = resp.read()
        else:
            raw = source
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    @staticmethod
    def enhance_contrast(img: np.ndarray) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        return cv2.cvtColor(cv2.merge((l_channel, a, b)), cv2.COLOR_LAB2BGR)

    @staticmethod
    def deskew(img: np.ndarray) -> np.ndarray:
        """Detect and correct text skew using Hough line transform."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) == 0:
            return img
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:
            return img
        h, w = img.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(
            img, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )

    @staticmethod
    def denoise(img: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    @staticmethod
    def binarize(img: np.ndarray) -> np.ndarray:
        """Adaptive Otsu thresholding for document binarization."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    @staticmethod
    def detect_orientation(img: np.ndarray) -> float:
        """Return the estimated rotation angle of text in image."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) < 10:
            return 0.0
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        return float(angle)

    @staticmethod
    def rotate_to_upright(img: np.ndarray) -> np.ndarray:
        """Rotate image to upright orientation."""
        angle = ImagePreprocessor.detect_orientation(img)
        if abs(angle) < 0.5:
            return img
        h, w = img.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(
            img, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )

    @staticmethod
    def to_png_bytes(img: np.ndarray) -> bytes:
        """Encode a BGR numpy array to PNG bytes."""
        success, buffer = cv2.imencode(".png", img)
        if not success:
            raise RuntimeError("Failed to encode image to PNG")
        return buffer.tobytes()
