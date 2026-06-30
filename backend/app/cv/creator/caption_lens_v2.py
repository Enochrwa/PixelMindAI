"""Caption Lens — Sprint 5 (S5-03).

Pipeline:
  1. CLIP Interrogator → natural-language description of the image
  2. Groq (LLaMA 3.1 8B) → platform-specific captions + hashtags

Platforms: instagram | twitter | linkedin
"""

from __future__ import annotations

import io
import logging
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates per platform
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a professional social media copywriter for a visual AI platform. "
    "Write punchy, engaging captions. Return ONLY valid JSON — no markdown fences."
)

_INSTAGRAM_PROMPT = """
Write exactly 3 Instagram captions (casual, inspirational, funny) plus 10 relevant hashtags
for each caption, based on this image description:

"{description}"

Return JSON with this exact shape:
{{
  "captions": [
    {{"style": "casual",       "caption": "...", "hashtags": ["...", ...]}},
    {{"style": "inspirational","caption": "...", "hashtags": ["...", ...]}},
    {{"style": "funny",        "caption": "...", "hashtags": ["...", ...]}}
  ]
}}
"""

_TWITTER_PROMPT = """
Write exactly 3 tweets (each under 280 characters) for this image description:

"{description}"

Return JSON:
{{"tweets": ["tweet 1", "tweet 2", "tweet 3"]}}
"""

_LINKEDIN_PROMPT = """
Write a professional LinkedIn caption (2-3 sentences, thought-leadership tone) for:

"{description}"

Return JSON:
{{"caption": "..."}}
"""


class CaptionLens:
    """Generate platform-specific social captions from any image."""

    def process(
        self,
        image_bytes: bytes,
        platforms: list[str] | None = None,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Return captions for the requested *platforms* (default: all three)."""
        if platforms is None:
            platforms = ["instagram", "twitter", "linkedin"]

        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        description = self._describe_image(pil)
        result: dict[str, Any] = {"image_description": description, "platforms": {}}

        for platform in platforms:
            result["platforms"][platform] = self._generate_platform_captions(
                description, platform, user_id
            )

        return result

    # ------------------------------------------------------------------
    # Image description
    # ------------------------------------------------------------------

    def _describe_image(self, pil: Image.Image) -> str:
        """Return a natural-language description via CLIP Interrogator (or fallback)."""
        try:
            from clip_interrogator import Config, Interrogator  # type: ignore[import]

            cfg = Config(
                clip_model_name="ViT-B/32",
                caption_model_name="blip-base",
            )
            cfg.apply_low_vram_defaults()
            interrogator = Interrogator(cfg)
            return str(interrogator.interrogate(pil))
        except Exception as _clip_err:
            logger.debug("clip_interrogator unavailable: %s", _clip_err)

        # Fallback: BLIP only
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
        except Exception as _blip_err:
            logger.debug("blip unavailable: %s", _blip_err)

        # Basic colour/composition fallback
        arr = np.array(pil)
        ch_means = np.mean(arr, axis=(0, 1))
        dominant = ["red", "green", "blue"][int(np.argmax(ch_means))]
        w, h = pil.size
        aspect = "landscape" if w > h else "portrait"
        return f"A {aspect} photo with {dominant}-dominant tones and natural composition"

    # ------------------------------------------------------------------
    # Caption generation per platform
    # ------------------------------------------------------------------

    def _generate_platform_captions(self, description: str, platform: str, user_id: str) -> Any:
        import asyncio
        import json

        from app.cv.ai.language_client import LanguageAIClient

        prompt_map = {
            "instagram": _INSTAGRAM_PROMPT,
            "twitter": _TWITTER_PROMPT,
            "linkedin": _LINKEDIN_PROMPT,
        }
        prompt_template = prompt_map.get(platform, _INSTAGRAM_PROMPT)
        prompt = prompt_template.format(description=description)

        try:
            client = LanguageAIClient()
            loop = asyncio.new_event_loop()
            raw = loop.run_until_complete(
                client.generate(
                    prompt=prompt,
                    system=_SYSTEM_PROMPT,
                    max_tokens=600,
                    user_id=user_id,
                )
            )
            loop.close()

            # Strip possible markdown code fences
            cleaned = raw.strip()
            for fence in ("```json", "```"):
                cleaned = cleaned.removeprefix(fence).removesuffix(fence)
            cleaned = cleaned.strip()
            data: Any = json.loads(cleaned)
            return data
        except Exception as exc:
            logger.warning("caption_lens.generate_failed platform=%s err=%s", platform, exc)
            return self._fallback_captions(platform, description)

    # ------------------------------------------------------------------
    # Fallback captions (no LLM available)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_captions(platform: str, description: str) -> Any:
        short_desc = description[:80] if len(description) > 80 else description
        if platform == "instagram":
            return {
                "captions": [
                    {
                        "style": "casual",
                        "caption": f"Love this shot 📸 {short_desc}",
                        "hashtags": [
                            "#photography",
                            "#photooftheday",
                            "#instagood",
                            "#picoftheday",
                            "#visual",
                            "#art",
                            "#creative",
                            "#explore",
                            "#beautiful",
                            "#life",
                        ],
                    },
                    {
                        "style": "inspirational",
                        "caption": f"Every image tells a story. ✨ {short_desc}",
                        "hashtags": [
                            "#inspiration",
                            "#motivation",
                            "#mindset",
                            "#photography",
                            "#storytelling",
                            "#vision",
                            "#growth",
                            "#perspective",
                            "#dreambig",
                            "#positivity",
                        ],
                    },
                    {
                        "style": "funny",
                        "caption": (
                            f"Me pretending to be a professional photographer 😅 {short_desc}"
                        ),
                        "hashtags": [
                            "#relatable",
                            "#funny",
                            "#moodoftheday",
                            "#photography",
                            "#humor",
                            "#LOL",
                            "#authentic",
                            "#reallife",
                            "#nofilter",
                            "#vibes",
                        ],
                    },
                ]
            }
        if platform == "twitter":
            return {
                "tweets": [
                    f"Captured this today — {short_desc} 📸",
                    f"A picture is worth a thousand words. {short_desc}",
                    f"Sharing a little visual story with you all today. {short_desc} 🌟",
                ]
            }
        # linkedin
        return {
            "caption": (
                f"Sharing a perspective captured today: {short_desc}. "
                "Visual communication continues to be one of the most powerful tools we have. "
                "What does this image say to you?"
            )
        }
