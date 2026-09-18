"""
Phase 4: Base LLM Provider Interface
Defines the contract for LLM generation abstractions.
"""
from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """
    Abstract interface for LLM synthesis.
    Enables pluggable model providers (OpenAI, Anthropic, local LLMs, mock).
    """

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Generates a natural-language completion grounded in the provided prompt context.
        """
        pass
