from __future__ import annotations

from abc import ABC, abstractmethod


class IOllamaClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str) -> str:
        """Call the Ollama API and return the raw model response text."""
        ...
