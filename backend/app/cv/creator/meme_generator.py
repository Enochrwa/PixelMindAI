"""Meme Generator Pro — Sprint 5 (S5-04).

Pipeline:
  1. MediaPipe FaceDetection + DeepFace emotion on detected faces
  2. CLIP Interrogator → scene description
  3. Groq → 5 meme caption suggestions (top + bottom text)
  4. Pillow compose — Impact-style font, white text, black outline

Two-phase API:
  • process(image_bytes) → {job_id context, suggestions, emotions}
  • compose(image_bytes, top_text, bottom_text) → composed image bytes (b64)
"""

from __future__ import annotations

import base64
import io
import json
import logging
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a professional meme writer. "
    "Return ONLY valid JSON — no markdown fences, no extra text."
)

_MEME_PROMPT = """
Create 5 funny meme caption ideas (top text + bottom text) for an image where:
- Scene: {scene}
- Detected emotion(s): {emotions}

Return JSON:
{{
  "suggestions": [
    {{"top": "...", "bottom": "..."}},
    {{"top": "...", "bottom": "..."}},
    {{"top": "...", "bottom": "..."}},
    {{"top": "...", "bottom": "..."}},
    {{"top": "...", "bottom": "..."}}
  ]
}}
"""


class MemeGenerator:
    """Detect faces/emotion, generate meme suggestions, compose final image."""

    # ------------------------------------------------------------------
    # Phase 1: analyse image → suggestions
    # ------------------------------------------------------------------

    def process(
        self,
        image_bytes: bytes,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Analyse image; return emotion data + Groq caption suggestions."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(pil)

        emotions = self._detect_emotions(arr)
        scene = self._describe_scene(pil)
        suggestions = self._generate_suggestions(scene, emotions, user_id)

        return {
            "scene_description": scene,
            "emotions_detected": emotions,
            "suggestions": suggestions,
            "image_width": pil.width,
            "image_height": pil.height,
        }

    # ------------------------------------------------------------------
    # Phase 2: compose meme image
    # ------------------------------------------------------------------

    def compose(
        self,
        image_bytes: bytes,
        top_text: str,
        bottom_text: str,
    ) -> dict[str, Any]:
        """Overlay *top_text* / *bottom_text* on image; return b64 PNG."""
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        composed = self._overlay_text(pil, top_text, bottom_text)

        buf = io.BytesIO()
        composed.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return {
            "result_image_b64": b64,
            "format": "png",
            "width": composed.width,
            "height": composed.height,
            "top_text": top_text,
            "bottom_text": bottom_text,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_emotions(self, img_array: np.ndarray) -> list[str]:
        emotions: list[str] = []
        try:
            from deepface import DeepFace  # type: ignore[import]

            result = DeepFace.analyze(
                img_path=img_array,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            faces = result if isinstance(result, list) else [result]
            for face in faces[:3]:  # cap at 3 faces
                em = face.get("dominant_emotion", "neutral")
                emotions.append(str(em))
        except Exception:
            emotions = ["neutral"]
        return emotions if emotions else ["neutral"]

    def _describe_scene(self, pil: Image.Image) -> str:
        try:
            from clip_interrogator import Config, Interrogator  # type: ignore[import]

            cfg = Config(clip_model_name="ViT-B/32", caption_model_name="blip-base")
            cfg.apply_low_vram_defaults()
            return str(Interrogator(cfg).interrogate(pil))
        except Exception as _clip_err:
            logger.debug("clip_interrogator unavailable: %s", _clip_err)
        try:
            from transformers import (  # type: ignore[import]
                BlipForConditionalGeneration,
                BlipProcessor,
            )

            proc = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            mdl = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            inputs = proc(pil, return_tensors="pt")
            out = mdl.generate(**inputs, max_new_tokens=60)
            return str(proc.decode(out[0], skip_special_tokens=True))
        except Exception:
            arr = np.array(pil)
            ch = np.mean(arr, axis=(0, 1))
            dom = ["red", "green", "blue"][int(np.argmax(ch))]
            w, h = pil.size
            return f"a {'landscape' if w > h else 'portrait'} photo with {dom}-dominant tones"

    def _generate_suggestions(
        self, scene: str, emotions: list[str], user_id: str
    ) -> list[dict[str, str]]:
        import asyncio

        from app.cv.ai.language_client import LanguageAIClient

        prompt = _MEME_PROMPT.format(
            scene=scene[:200],
            emotions=", ".join(emotions),
        )
        try:
            client = LanguageAIClient()
            loop = asyncio.new_event_loop()
            raw = loop.run_until_complete(
                client.generate(
                    prompt=prompt,
                    system=_SYSTEM_PROMPT,
                    max_tokens=500,
                    user_id=user_id,
                )
            )
            loop.close()
            cleaned = raw.strip()
            for fence in ("```json", "```"):
                cleaned = cleaned.removeprefix(fence).removesuffix(fence)
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            suggestions: list[dict[str, str]] = data.get("suggestions", [])
            return suggestions[:5]
        except Exception as exc:
            logger.warning("meme_generator.suggestions_failed err=%s", exc)
            return self._fallback_suggestions(emotions)

    @staticmethod
    def _fallback_suggestions(emotions: list[str]) -> list[dict[str, str]]:
        em = emotions[0] if emotions else "neutral"
        templates = {
            "happy": [
                {"top": "When the plan actually works", "bottom": "First time"},
                {"top": "Me looking at my bank account", "bottom": "After payday"},
                {"top": "Nobody:", "bottom": "Me on a Friday afternoon:"},
                {"top": "That smile when", "bottom": "It's finally the weekend"},
                {"top": "POV:", "bottom": "Life is actually good right now"},
            ],
            "surprise": [
                {"top": "My face when", "bottom": "The WiFi actually works"},
                {"top": "When you check your email", "bottom": "And it's not spam"},
                {"top": "Nobody expected this", "bottom": "But here we are"},
                {"top": "Wait, it actually worked?", "bottom": "It actually worked."},
                {"top": "Me realising", "bottom": "It was that simple all along"},
            ],
        }
        return templates.get(
            em,
            [
                {"top": "Story of my life", "bottom": "Every. Single. Time."},
                {"top": "Me:", "bottom": "Also me:"},
                {"top": "POV:", "bottom": "You chose the wrong option"},
                {"top": "When life gives you lemons", "bottom": "Make memes instead"},
                {"top": "Nobody:", "bottom": "The internet:"},
            ],
        )

    # ------------------------------------------------------------------
    # Text overlay (Impact-style)
    # ------------------------------------------------------------------

    def _overlay_text(self, pil: Image.Image, top_text: str, bottom_text: str) -> Image.Image:
        img = pil.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size
        font_size = max(int(h * 0.08), 24)

        font = self._load_impact_font(font_size)

        def draw_outlined_text(text: str, y: int, anchor: str = "ma") -> None:
            x = w // 2
            # Black outline
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0), anchor=anchor)
            # White fill
            draw.text((x, y), text, font=font, fill=(255, 255, 255), anchor=anchor)

        if top_text:
            draw_outlined_text(top_text.upper(), int(h * 0.06))
        if bottom_text:
            draw_outlined_text(bottom_text.upper(), int(h * 0.94))

        return img

    @staticmethod
    def _load_impact_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        font_paths = [
            "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
            "/usr/share/fonts/truetype/impact.ttf",
            "/System/Library/Fonts/Supplemental/Impact.ttf",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()
