import json
import pytest
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.application.dtos.insight_dto import GenerateInsightRequest
from app.application.use_cases.generate_insight import GenerateInsightUseCase
from app.domain.entities.insight import (
    CommercialRisk,
    Intent,
    MainEmotion,
    MessageInsight,
    Sentiment,
    Urgency,
)
from app.domain.entities.message import MessageType, Platform, SenderRole


_VALID_OLLAMA_RESPONSE = json.dumps({
    "sender_role": "buyer",
    "sentiment": "neutral",
    "main_emotion": "other",
    "intent": "information",
    "urgency": "low",
    "commercial_risk": "low",
    "summary": "Test summary",
    "recommended_action": "No action needed",
    "insights": ["Test insight"],
})


def _make_request(**overrides) -> GenerateInsightRequest:
    defaults = dict(
        message_id="msg-uuid",
        wamid="wamid.ABC123",
        platform=Platform.WHATSAPP,
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        sender_role="buyer",
        message_type=MessageType.TEXT,
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sender_name="Test User",
        raw_text="Hola mundo",
    )
    return GenerateInsightRequest(**{**defaults, **overrides})


def _make_saved_insight(**overrides) -> MessageInsight:
    defaults = dict(
        id="insight-uuid",
        message_id="msg-uuid",
        wamid="wamid.ABC123",
        platform=Platform.WHATSAPP,
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        sender_role=SenderRole.BUYER,
        sentiment=Sentiment.NEUTRAL,
        main_emotion=MainEmotion.OTHER,
        intent=Intent.INFORMATION,
        urgency=Urgency.LOW,
        commercial_risk=CommercialRisk.LOW,
        summary="Test summary",
        recommended_action="No action needed",
        insights=["Test insight"],
        raw_model_response={"response": _VALID_OLLAMA_RESPONSE},
        model_name="llama3",
        prompt_version="v1",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    return MessageInsight(**{**defaults, **overrides})


def _make_repo_factory(mock_repo):
    @asynccontextmanager
    async def _factory():
        yield mock_repo
    return _factory


def _make_use_case(mock_repo, mock_ollama, mock_wa=None, whisper_model=""):
    return GenerateInsightUseCase(
        repo_factory=_make_repo_factory(mock_repo),
        ollama_client=mock_ollama,
        model="llama3",
        prompt_version="v1",
        whatsapp_client=mock_wa,
        whisper_model=whisper_model,
    )


@pytest.mark.asyncio
async def test_text_message_generates_insight():
    request = _make_request()
    mock_ollama = AsyncMock()
    mock_ollama.generate.return_value = _VALID_OLLAMA_RESPONSE
    mock_repo = AsyncMock()
    mock_repo.find_recent_by_conversation.return_value = []
    mock_repo.save.return_value = _make_saved_insight()

    use_case = _make_use_case(mock_repo, mock_ollama)
    response = await use_case.execute(request)

    assert response.was_skipped is False
    assert response.insight_id == "insight-uuid"
    assert response.sentiment == "neutral"
    assert response.audio_transcription is None
    mock_ollama.generate.assert_called_once()
    mock_ollama.transcribe.assert_not_called()


@pytest.mark.asyncio
async def test_message_without_text_is_skipped():
    request = _make_request(raw_text=None, message_type=MessageType.IMAGE)
    mock_ollama = AsyncMock()
    mock_repo = AsyncMock()

    use_case = _make_use_case(mock_repo, mock_ollama)
    response = await use_case.execute(request)

    assert response.was_skipped is True
    mock_repo.save.assert_not_called()
    mock_ollama.generate.assert_not_called()


@pytest.mark.asyncio
async def test_audio_message_transcribes_and_generates_insight():
    request = _make_request(
        raw_text=None,
        message_type=MessageType.AUDIO,
        media_id="MEDIA_ID_123",
    )
    mock_ollama = AsyncMock()
    mock_ollama.transcribe.return_value = "Hola, quiero cancelar mi pedido"
    mock_ollama.generate.return_value = _VALID_OLLAMA_RESPONSE

    mock_wa = AsyncMock()
    mock_wa.download_media.return_value = b"fake-audio-bytes"

    mock_repo = AsyncMock()
    mock_repo.find_recent_by_conversation.return_value = []
    mock_repo.save.return_value = _make_saved_insight(
        audio_transcription="Hola, quiero cancelar mi pedido"
    )

    use_case = _make_use_case(mock_repo, mock_ollama, mock_wa=mock_wa, whisper_model="whisper")
    response = await use_case.execute(request)

    mock_wa.download_media.assert_called_once_with("MEDIA_ID_123")
    mock_ollama.transcribe.assert_called_once_with(b"fake-audio-bytes", "whisper")
    mock_ollama.generate.assert_called_once()
    assert response.was_skipped is False
    assert response.audio_transcription == "Hola, quiero cancelar mi pedido"


@pytest.mark.asyncio
async def test_audio_without_whatsapp_client_is_skipped():
    request = _make_request(
        raw_text=None,
        message_type=MessageType.AUDIO,
        media_id="MEDIA_ID_123",
    )
    mock_ollama = AsyncMock()
    mock_repo = AsyncMock()

    # No whatsapp_client → audio path disabled, falls through to skip
    use_case = _make_use_case(mock_repo, mock_ollama)
    response = await use_case.execute(request)

    assert response.was_skipped is True
    mock_ollama.transcribe.assert_not_called()
    mock_ollama.generate.assert_not_called()


@pytest.mark.asyncio
async def test_audio_without_whisper_model_is_skipped():
    request = _make_request(
        raw_text=None,
        message_type=MessageType.AUDIO,
        media_id="MEDIA_ID_123",
    )
    mock_ollama = AsyncMock()
    mock_wa = AsyncMock()
    mock_repo = AsyncMock()

    # whisper_model="" → audio path disabled
    use_case = _make_use_case(mock_repo, mock_ollama, mock_wa=mock_wa, whisper_model="")
    response = await use_case.execute(request)

    assert response.was_skipped is True
    mock_wa.download_media.assert_not_called()


@pytest.mark.asyncio
async def test_audio_transcription_is_stored_in_saved_entity():
    request = _make_request(
        raw_text=None,
        message_type=MessageType.AUDIO,
        media_id="MEDIA_ID_123",
    )
    mock_ollama = AsyncMock()
    mock_ollama.transcribe.return_value = "Texto transcripto del audio"
    mock_ollama.generate.return_value = _VALID_OLLAMA_RESPONSE

    mock_wa = AsyncMock()
    mock_wa.download_media.return_value = b"audio"

    mock_repo = AsyncMock()
    mock_repo.find_recent_by_conversation.return_value = []

    saved_insight = None

    async def capture_save(insight: MessageInsight) -> MessageInsight:
        nonlocal saved_insight
        saved_insight = insight
        return insight

    mock_repo.save.side_effect = capture_save

    use_case = _make_use_case(mock_repo, mock_ollama, mock_wa=mock_wa, whisper_model="whisper")
    await use_case.execute(request)

    assert saved_insight is not None
    assert saved_insight.audio_transcription == "Texto transcripto del audio"


@pytest.mark.asyncio
async def test_text_message_has_no_audio_transcription():
    request = _make_request(raw_text="Mensaje de texto normal")
    mock_ollama = AsyncMock()
    mock_ollama.generate.return_value = _VALID_OLLAMA_RESPONSE
    mock_repo = AsyncMock()
    mock_repo.find_recent_by_conversation.return_value = []

    saved_insight = None

    async def capture_save(insight: MessageInsight) -> MessageInsight:
        nonlocal saved_insight
        saved_insight = insight
        return insight

    mock_repo.save.side_effect = capture_save

    use_case = _make_use_case(mock_repo, mock_ollama)
    await use_case.execute(request)

    assert saved_insight is not None
    assert saved_insight.audio_transcription is None
