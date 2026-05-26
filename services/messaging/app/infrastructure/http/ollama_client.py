from __future__ import annotations

import logging

import httpx

from app.domain.services.ollama_client import IOllamaClient

logger = logging.getLogger(__name__)


class HttpxOllamaClient(IOllamaClient):
    """Concrete adapter for the Ollama /api/generate endpoint using httpx."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def generate(self, prompt: str, model: str) -> str:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False,
        }
        logger.debug("ollama request url=%s model=%s", url, model)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "ollama HTTP error url=%s status=%d body=%.200s",
                    url,
                    exc.response.status_code,
                    exc.response.text,
                )
                raise
            except httpx.RequestError as exc:
                logger.error("ollama request error url=%s error=%s", url, exc)
                raise

        return response.json()["response"]
