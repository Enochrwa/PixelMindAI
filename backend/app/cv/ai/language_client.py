"""Central language AI client for PixelMind AI.

Wraps Groq (primary) with rate-limiting, per-user daily cap, and Redis
response caching.  A single ``LANGUAGE_AI_PROVIDER`` env var lets you
switch to Together.ai or Fireworks.ai without touching callers.

Usage::

    from app.cv.ai.language_client import LanguageAIClient

    client = LanguageAIClient()
    text = await client.generate(
        prompt="Describe this image: a golden sunset over Lake Kivu",
        max_tokens=200,
        user_id="user-uuid",
    )
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

_DAILY_GLOBAL_CAP = 14_000  # Groq free tier
_DAILY_USER_CAP_FREE = 3  # calls/day for free-tier users
_CACHE_TTL = 86_400  # 24 h in seconds
_REDIS_KEY_GLOBAL = "groq:calls_today"
_REDIS_KEY_USER_PREFIX = "groq:user_calls:"


class RateLimitError(Exception):
    """Raised when a Groq rate limit (global or per-user) is exceeded."""


class LanguageAIClient:
    """Rate-limited, cached wrapper around a hosted LLM provider.

    All state is stored in Upstash Redis so it survives across Fly.io
    restarts and worker processes.
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis[Any] | None = None
        self._provider: str = getattr(settings, "LANGUAGE_AI_PROVIDER", "groq")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_redis(self) -> aioredis.Redis[Any]:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
        return self._redis

    @staticmethod
    def _cache_key(prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        return f"llm:cache:{digest}"

    async def _check_global_limit(self, redis: aioredis.Redis[Any]) -> None:
        calls = await redis.get(_REDIS_KEY_GLOBAL)
        if calls and int(calls) >= _DAILY_GLOBAL_CAP:
            raise RateLimitError("Global Groq daily limit reached. Try again tomorrow.")

    async def _check_user_limit(self, redis: aioredis.Redis[Any], user_id: str) -> None:
        key = f"{_REDIS_KEY_USER_PREFIX}{user_id}"
        calls = await redis.get(key)
        if calls and int(calls) >= _DAILY_USER_CAP_FREE:
            raise RateLimitError(
                f"Free-tier limit of {_DAILY_USER_CAP_FREE} AI calls/day reached. "
                "Upgrade to Pro for unlimited access."
            )

    async def _increment_counters(self, redis: aioredis.Redis[Any], user_id: str) -> None:
        # Global counter with 24-h TTL
        pipe = redis.pipeline()
        pipe.incr(_REDIS_KEY_GLOBAL)
        pipe.expire(_REDIS_KEY_GLOBAL, _CACHE_TTL)
        # Per-user counter
        user_key = f"{_REDIS_KEY_USER_PREFIX}{user_id}"
        pipe.incr(user_key)
        pipe.expire(user_key, _CACHE_TTL)
        await pipe.execute()

    # ------------------------------------------------------------------
    # Core generation method
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 400,
        temperature: float = 0.7,
        system: str = "You are a helpful AI assistant for a visual intelligence platform.",
        user_id: str = "anonymous",
    ) -> str:
        """Generate text from *prompt* via the configured LLM provider.

        Returns the generated string.  Raises :class:`RateLimitError` when
        per-user or global limits are exhausted, and ``RuntimeError`` when the
        upstream provider returns an error.
        """
        redis = await self._get_redis()
        cache_key = self._cache_key(prompt)

        # 1. Cache hit
        cached = await redis.get(cache_key)
        if cached:
            logger.debug("language_client.cache_hit key=%s", cache_key[:16])
            return str(cached)

        # 2. Rate-limit checks
        await self._check_global_limit(redis)
        if user_id and user_id != "anonymous":
            await self._check_user_limit(redis, user_id)

        # 3. Call provider
        result = await self._call_provider(prompt, max_tokens, temperature, system)

        # 4. Increment counters & cache result
        await self._increment_counters(redis, user_id)
        await redis.set(cache_key, result, ex=_CACHE_TTL)

        return result

    async def _call_provider(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system: str,
    ) -> str:
        if self._provider == "groq":
            return await self._call_groq(prompt, max_tokens, temperature, system)
        if self._provider in {"together", "fireworks"}:
            return await self._call_openai_compatible(prompt, max_tokens, temperature, system)
        # Fallback: naive template (for dev / no API key)
        return await self._fallback_template(prompt)

    async def _call_groq(
        self, prompt: str, max_tokens: int, temperature: float, system: str
    ) -> str:
        try:
            from groq import AsyncGroq  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError("groq package not installed") from exc

        api_key = getattr(settings, "GROQ_API_KEY", None)
        if not api_key:
            logger.warning("GROQ_API_KEY not set — using fallback template")
            return await self._fallback_template(prompt)

        client = AsyncGroq(api_key=api_key)
        model = getattr(settings, "GROQ_MODEL", "llama-3.1-8b-instant")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return str(content) if content is not None else ""

    async def _call_openai_compatible(
        self, prompt: str, max_tokens: int, temperature: float, system: str
    ) -> str:
        """OpenAI-compatible endpoint for Together.ai / Fireworks.ai."""
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx not installed") from exc

        base_urls = {
            "together": "https://api.together.xyz/v1",
            "fireworks": "https://api.fireworks.ai/inference/v1",
        }
        base = base_urls.get(self._provider, "https://api.together.xyz/v1")
        api_key = getattr(settings, "LANGUAGE_AI_API_KEY", "")
        model = getattr(settings, "LANGUAGE_AI_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=30.0) as http:
            r = await http.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            r.raise_for_status()
            data: dict[str, Any] = r.json()
            return str(data["choices"][0]["message"]["content"])

    @staticmethod
    async def _fallback_template(prompt: str) -> str:
        """Return a structured but generic response when no API key is configured."""
        # Detect intent from prompt keywords
        lower = prompt.lower()
        if "instagram" in lower or "caption" in lower or "hashtag" in lower:
            return json.dumps(
                {
                    "instagram": [
                        {
                            "caption": "Capturing life's beautiful moments ✨",
                            "hashtags": ["#photography", "#lifestyle", "#moments"],
                        },
                        {
                            "caption": "Every picture tells a story 📸",
                            "hashtags": ["#photo", "#story", "#art"],
                        },
                    ]
                }
            )
        if "tweet" in lower or "twitter" in lower:
            return json.dumps({"twitter": ["A picture is worth a thousand words. 📸 #photography"]})
        if "linkedin" in lower or "professional" in lower:
            return json.dumps(
                {
                    "linkedin": [
                        "Sharing a perspective from today — every image holds a story"
                        " worth telling."
                    ]
                }
            )
        if "meme" in lower or "caption" in lower:
            return json.dumps(
                {
                    "suggestions": [
                        {"top": "When you finally get it right", "bottom": "First try"},
                        {"top": "POV:", "bottom": "You're living your best life"},
                        {"top": "Nobody:", "bottom": "Absolutely nobody: Me:"},
                        {"top": "That feeling when", "bottom": "Everything goes perfectly"},
                        {"top": "Story of my life", "bottom": "Every single time"},
                    ]
                }
            )
        if "story" in lower or "narrative" in lower or "pixelstory" in lower:
            return json.dumps(
                {
                    "captions": [
                        "A moment captured in time 🌟",
                        "The adventure continues ✨",
                        "Making memories that last forever 📸",
                    ]
                }
            )
        return "An interesting visual moment captured beautifully."
