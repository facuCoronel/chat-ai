from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from app.application.dtos.insight_dto import GenerateInsightRequest, GenerateInsightResponse
from app.domain.entities.insight import (
    CommercialRisk,
    Intent,
    MainEmotion,
    MessageInsight,
    SenderRole,
    Sentiment,
    Urgency,
)
from app.domain.entities.message import MessageType

if TYPE_CHECKING:
    from app.application.ports.insight_generator import IInsightGenerator
    from app.application.ports.insight_repository_factory import IInsightRepositoryContextFactory
    from app.domain.services.ollama_client import IOllamaClient
    from app.domain.services.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

_REQUIRED_KEYS = {
    "sender_role",
    "sentiment",
    "main_emotion",
    "intent",
    "urgency",
    "commercial_risk",
    "summary",
    "insights",
    "keywords",
}


class GenerateInsightUseCase:
    def __init__(
        self,
        repo_factory: "IInsightRepositoryContextFactory",
        ollama_client: "IOllamaClient",
        model: str,
        prompt_version: str,
        whatsapp_client: Optional["IWhatsAppClient"] = None,
        transcription_client: Optional["IOllamaClient"] = None,
    ) -> None:
        self._repo_factory = repo_factory
        self._ollama_client = ollama_client
        self._model = model
        self._prompt_version = prompt_version
        self._whatsapp_client = whatsapp_client
        self._transcription_client = transcription_client

    async def execute(self, request: GenerateInsightRequest) -> GenerateInsightResponse:
        effective_text = request.raw_text

        if request.message_type == MessageType.AUDIO:
            logger.info(
                "audio message received wamid=%s media_id=%s has_whatsapp_client=%s has_transcription_client=%s",
                request.wamid,
                request.media_id,
                bool(self._whatsapp_client),
                bool(self._transcription_client),
            )

        if (
            request.message_type == MessageType.AUDIO
            and request.media_id
            and self._whatsapp_client
            and self._transcription_client
        ):
            logger.info("audio download start media_id=%s wamid=%s", request.media_id, request.wamid)
            audio_bytes = await self._whatsapp_client.download_media(request.media_id)
            logger.info("audio download done media_id=%s bytes=%d wamid=%s", request.media_id, len(audio_bytes), request.wamid)
            effective_text = await self._transcription_client.transcribe(audio_bytes, "")
            logger.info(
                "audio transcribed media_id=%s chars=%d wamid=%s",
                request.media_id,
                len(effective_text),
                request.wamid,
            )
        elif request.message_type == MessageType.AUDIO:
            logger.warning(
                "audio message skipped — transcription not configured wamid=%s media_id=%s",
                request.wamid,
                request.media_id,
            )

        if not effective_text or not effective_text.strip():
            logger.debug(
                "insight skipped — no text content wamid=%s message_type=%s",
                request.wamid,
                request.message_type.value,
            )
            return GenerateInsightResponse(
                message_id=request.message_id,
                wamid=request.wamid,
                was_skipped=True,
            )

        async with self._repo_factory() as repo:
            history = await repo.find_recent_by_conversation(
                sender_id=request.sender_id,
                recipient_id=request.recipient_id,
                platform=request.platform.value,
                limit=10,
            )

        context_summary = _build_context_summary(history)
        prompt = _build_prompt(
            sender_role=request.sender_role,
            current_text=effective_text,
            context_summary=context_summary,
            prompt_version=self._prompt_version,
        )

        logger.info(
            "calling ollama model=%s prompt_version=%s prompt_length=%d wamid=%s",
            self._model,
            self._prompt_version,
            len(prompt),
            request.wamid,
        )
        t0 = time.monotonic()
        raw_response = await self._ollama_client.generate(prompt, self._model)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        parsed = _parse_ollama_response(raw_response, request.wamid)
        logger.info(
            "ollama response received wamid=%s elapsed_ms=%d sentiment=%s intent=%s",
            request.wamid,
            elapsed_ms,
            parsed.get("sentiment"),
            parsed.get("intent"),
        )

        insight = MessageInsight(
            id=str(uuid.uuid4()),
            message_id=request.message_id,
            wamid=request.wamid,
            platform=request.platform,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            sender_name=request.sender_name,
            sender_role=SenderRole(parsed["sender_role"]),
            sentiment=Sentiment(parsed["sentiment"]),
            main_emotion=MainEmotion(parsed["main_emotion"]),
            intent=Intent(parsed["intent"]),
            urgency=Urgency(parsed["urgency"]),
            commercial_risk=CommercialRisk(parsed["commercial_risk"]),
            summary=parsed["summary"],
            insights=parsed["insights"],
            keywords=parsed["keywords"],
            raw_model_response={"response": raw_response},
            model_name=self._model,
            prompt_version=self._prompt_version,
            created_at=datetime.now(tz=timezone.utc),
            audio_transcription=effective_text if request.message_type == MessageType.AUDIO else None,
        )

        async with self._repo_factory() as repo:
            saved = await repo.save(insight)

        logger.info(
            "insight saved insight_id=%s wamid=%s commercial_risk=%s",
            saved.id,
            saved.wamid,
            saved.commercial_risk.value,
        )

        return GenerateInsightResponse(
            insight_id=saved.id,
            message_id=saved.message_id,
            wamid=saved.wamid,
            was_skipped=False,
            sentiment=saved.sentiment.value,
            intent=saved.intent.value,
            urgency=saved.urgency.value,
            commercial_risk=saved.commercial_risk.value,
            audio_transcription=saved.audio_transcription,
        )


_prompt_cache: dict[str, str] = {}


def _load_prompt_template(version: str) -> str:
    if version in _prompt_cache:
        return _prompt_cache[version]
    path = _PROMPTS_DIR / f"insight_{version}.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    template: str = data["template"]
    _prompt_cache[version] = template
    return template


def _build_context_summary(history: list[MessageInsight]) -> str:
    if not history:
        return "No prior context."
    lines = [
        f"[{i.sender_role.value} - {i.sender_name or i.sender_id}] {i.intent.value}: \"{i.summary}\" → {i.sentiment.value}"
        for i in history
    ]
    return "\n".join(lines)


def _build_prompt(
    sender_role: str,
    current_text: str,
    context_summary: str,
    prompt_version: str,
) -> str:
    template = _load_prompt_template(prompt_version)
    return template.format(
        sender_role=sender_role,
        current_text=current_text,
        context_summary=context_summary,
    )


def _parse_ollama_response(raw: str, wamid: str = "") -> dict:
    text = raw.strip()

    # Strip markdown code fences if the model wrapped the JSON
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1 if lines[0].startswith("```") else 0
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(
            "ollama parse error wamid=%s raw_excerpt=%.200s error=%s",
            wamid,
            raw,
            exc,
        )
        raise ValueError(f"Ollama response is not valid JSON: {exc}") from exc

    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        logger.error(
            "ollama response missing keys wamid=%s missing=%s raw_keys=%s raw_excerpt=%.300s",
            wamid,
            missing,
            list(data.keys()),
            raw,
        )
        raise ValueError(f"Ollama response missing required keys: {missing}")

    return data


