"""
Phase 4: LLM Provider Factory
Selects and initializes the appropriate LLM provider.
"""
import logging
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.core.config import settings

logger = logging.getLogger("connectdots_llm_factory")


def get_llm_provider() -> LLMProvider:
    """
    Returns an instance of LLMProvider based on application settings.
    Falls back to MockLLMProvider if OpenAI API key is missing or LLM_PROVIDER is 'mock'.
    """
    provider_type = (settings.LLM_PROVIDER or "mock").strip().lower()

    if provider_type == "openai":
        if settings.LLM_API_KEY and len(settings.LLM_API_KEY.strip()) > 10:
            try:
                return OpenAIProvider()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAIProvider ({e}), falling back to MockLLMProvider.")
        else:
            logger.info("LLM_API_KEY not provided. Operating with deterministic MockLLMProvider.")

    return MockLLMProvider()
