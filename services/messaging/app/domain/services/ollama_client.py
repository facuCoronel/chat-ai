from __future__ import annotations

from abc import ABC, abstractmethod


class IOllamaClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str) -> str:
        """Call the Ollama API and return the raw model response text."""
        ...

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, model: str) -> str:
        """Transcribe audio bytes using Ollama Whisper-compatible endpoint."""
        ...
