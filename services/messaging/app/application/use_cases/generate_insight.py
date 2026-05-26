from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from app.application.ports.insight_generator import IInsightGenerator
    from app.application.ports.insight_repository_factory import IInsightRepositoryContextFactory
    from app.domain.services.ollama_client import IOllamaClient

logger = logging.getLogger(__name__)

_REQUIRED_KEYS = {
    "sender_role",
    "sentiment",
    "main_emotion",
    "intent",
    "urgency",
    "commercial_risk",
    "summary",
    "recommended_action",
    "insights",
}


class GenerateInsightUseCase:
    def __init__(
        self,
        repo_factory: "IInsightRepositoryContextFactory",
        ollama_client: "IOllamaClient",
        model: str,
        prompt_version: str,
    ) -> None:
        self._repo_factory = repo_factory
        self._ollama_client = ollama_client
        self._model = model
        self._prompt_version = prompt_version

    async def execute(self, request: GenerateInsightRequest) -> GenerateInsightResponse:
        if not request.raw_text or not request.raw_text.strip():
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
            history = await repo.find_recent_by_sender(
                sender_id=request.sender_id,
                platform=request.platform.value,
                limit=10,
            )

        context_summary = _build_context_summary(history)
        prompt = _build_prompt(
            sender_role=request.sender_role,
            current_text=request.raw_text,
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
            sender_role=SenderRole(parsed["sender_role"]),
            sentiment=Sentiment(parsed["sentiment"]),
            main_emotion=MainEmotion(parsed["main_emotion"]),
            intent=Intent(parsed["intent"]),
            urgency=Urgency(parsed["urgency"]),
            commercial_risk=CommercialRisk(parsed["commercial_risk"]),
            summary=parsed["summary"],
            recommended_action=parsed["recommended_action"],
            insights=parsed["insights"],
            raw_model_response={"response": raw_response},
            model_name=self._model,
            prompt_version=self._prompt_version,
            created_at=datetime.now(tz=timezone.utc),
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
        )


def _build_context_summary(history: list[MessageInsight]) -> str:
    if not history:
        return "No prior context."
    lines = [
        f"[{i.sender_role.value}] {i.intent.value}: \"{i.summary}\" → {i.sentiment.value}"
        for i in history
    ]
    return "\n".join(lines)


def _build_prompt(
    sender_role: str,
    current_text: str,
    context_summary: str,
    prompt_version: str,
) -> str:
    if prompt_version == "v1":
        return _build_prompt_v1(sender_role, current_text, context_summary)
    return _build_prompt_v1(sender_role, current_text, context_summary)


def _build_prompt_v1(sender_role: str, current_text: str, context_summary: str) -> str:
    return f"""You are a conversational intelligence analyst for a commercial messaging platform.
Analyze the following message and respond ONLY with valid JSON matching the required schema.
No markdown, no code fences, no extra text.

CONVERSATION CONTEXT (prior messages, oldest first):
{context_summary}

CURRENT MESSAGE:
- Sender role: {sender_role}
- Message text: "{current_text}"

RULES:
1. Use the context to interpret ambiguous short messages ("ok", "dale", "cancelalo", etc.).
2. commercial_risk=high only for cancellation signals, complaint escalation, or clear sale loss.
3. Do not invent data not present in the message or context. Use neutral values when uncertain.
4. A seller message must never be interpreted as a buyer complaint.
5. Keep sender_role as provided unless the message clearly contradicts it.

REQUIRED JSON SCHEMA:
{{
  "sender_role": "buyer | seller | unknown",
  "sentiment": "positive | neutral | negative | mixed",
  "main_emotion": "anger | frustration | anxiety | confusion | satisfaction | joy | sadness | urgency | other",
  "intent": "complaint | question | purchase_intent | support_request | negotiation | cancellation_risk | follow_up | information | other",
  "urgency": "low | medium | high",
  "commercial_risk": "low | medium | high",
  "summary": "one sentence: what the sender wants or is expressing",
  "insights": ["actionable observation"],
  "recommended_action": "specific next step for the agent"
}}"""


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


async def _run_insight_safely(
    generator: "IInsightGenerator",
    request: GenerateInsightRequest,
) -> None:
    """Fire-and-forget wrapper. Logs errors without propagating them."""
    logger.debug(
        "insight task dispatched wamid=%s sender_role=%s",
        request.wamid,
        request.sender_role,
    )
    try:
        await generator.execute(request)
    except Exception:
        logger.exception(
            "insight generation failed wamid=%s — message is saved, insight skipped",
            request.wamid,
        )
