"""
Phase 4: Groq LLM Provider
Implements LLMProvider using Groq's high-speed LPU inference API via httpx.
Supports models like openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.8-27b.
"""
import logging
from typing import Optional
import httpx

from app.services.llm.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger("connectdots_groq")


class GroqProvider(LLMProvider):
    """
    Groq-backed provider for high-speed, evidence-grounded crime analysis synthesis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL or "openai/gpt-oss-120b"
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.base_url = (base_url or settings.LLM_BASE_URL or "https://api.groq.com/openai/v1").rstrip("/")

        if not self.api_key:
            raise ValueError("GroqProvider requires GROQ_API_KEY or LLM_API_KEY.")

    async def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Executes chat completion against Groq's OpenAI-compatible endpoint.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Groq API error HTTP {response.status_code}: {response.text}")
                    raise RuntimeError(f"Groq API error HTTP {response.status_code}: {response.text}")

                data = response.json()
                content = data["choices"][0]["message"].get("content", "")
                return content or ""
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise RuntimeError(f"Groq generation error: {e}")
