from __future__ import annotations

import logging

import httpx

from app.domain.services.ollama_client import IOllamaClient

logger = logging.getLogger(__name__)


class HttpxWhisperClient(IOllamaClient):
    """Adapter for the hwdsl2/whisper-server transcription API."""

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 60.0, language: str = "es") -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._language = language

    async def generate(self, prompt: str, model: str) -> str:
        raise NotImplementedError("WhisperClient only supports transcription")

    async def transcribe(self, audio_bytes: bytes, model: str) -> str:
        url = f"{self._base_url}/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        logger.info("whisper transcribe start url=%s bytes=%d", url, len(audio_bytes))
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
                    data={"model": "whisper-1", "language": self._language},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "whisper transcribe HTTP error url=%s status=%d body=%.200s",
                    url,
                    exc.response.status_code,
                    exc.response.text,
                )
                raise
            except httpx.RequestError as exc:
                logger.error("whisper transcribe request error url=%s error=%s", url, exc)
                raise

        data = response.json()
        text = data.get("text", "")
        logger.info("whisper transcribe done url=%s result_chars=%d text_preview=%.80s", url, len(text), text)
        return text
