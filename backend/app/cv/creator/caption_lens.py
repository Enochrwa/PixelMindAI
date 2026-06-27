"""Caption Lens CV tool.

Generates descriptive captions for images using BLIP or CLIP-based models.
Falls back to basic color/object analysis if heavy models unavailable.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image


class CaptionLens:
    """Generate captions and descriptive tags for images."""

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Generate a caption for the given image."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        try:
            from transformers import BlipForConditionalGeneration, BlipProcessor  # type: ignore[import]
            import torch  # type: ignore[import]

            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            inputs = processor(pil, return_tensors="pt")
            out = model.generate(**inputs, max_new_tokens=50)
            caption = processor.decode(out[0], skip_special_tokens=True)
            return {
                "caption": caption,
                "method": "blip",
                "tags": [],
                "confidence": 0.85,
            }
        except (ImportError, Exception):
            # Fallback: basic image analysis
            img_array = np.array(pil)
            avg_brightness = float(np.mean(img_array))
            dominant_channel = ["red", "green", "blue"][int(np.argmax(np.mean(img_array, axis=(0, 1))))]
            w, h = pil.size
            aspect = "landscape" if w > h else "portrait" if h > w else "square"
            caption = f"A {aspect} image with {dominant_channel}-dominant tones"
            return {
                "caption": caption,
                "method": "basic_analysis",
                "tags": [aspect, dominant_channel, "image"],
                "confidence": 0.5,
                "image_info": {
                    "width": w,
                    "height": h,
                    "avg_brightness": round(avg_brightness, 2),
                },
            }
