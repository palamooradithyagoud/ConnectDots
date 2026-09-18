"""
Phase 4: OpenAI LLM Provider
Implements LLMProvider using the AsyncOpenAI client.
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.services.llm.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger("connectdots_openai")


class OpenAIProvider(LLMProvider):
    """
    OpenAI-backed provider for evidence-grounded crime analysis synthesis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Executes chat completion against the configured OpenAI model.
        """
        if not self.client:
            raise ValueError("OpenAIProvider requires an active LLM_API_KEY.")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise RuntimeError(f"OpenAI generation error: {e}")
