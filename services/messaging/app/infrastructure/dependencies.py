from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.generate_insight import GenerateInsightUseCase
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.services.ollama_client import IOllamaClient
from app.domain.services.whatsapp_client import IWhatsAppClient
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database.engine import get_session_factory
from app.infrastructure.database.factories.insight_repository_factory import (
    SqlaInsightRepositoryFactory,
)
from app.infrastructure.database.repositories.sqla_business_account_repository import SqlaBusinessAccountRepository
from app.infrastructure.database.repositories.sqla_message_repository import SqlaMessageRepository
from app.infrastructure.http.ollama_client import HttpxOllamaClient
from app.infrastructure.http.whisper_client import HttpxWhisperClient
from app.infrastructure.http.whatsapp_client import HttpxWhatsAppClient


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


def get_ollama_client(settings: Settings = Depends(get_settings)) -> IOllamaClient:
    return HttpxOllamaClient(base_url=settings.OLLAMA_BASE_URL)


def get_transcription_client(settings: Settings = Depends(get_settings)) -> IOllamaClient:
    return HttpxWhisperClient(base_url=settings.WHISPER_BASE_URL, api_key=settings.WHISPER_API_KEY, language=settings.WHISPER_LANGUAGE)


def get_whatsapp_client(settings: Settings = Depends(get_settings)) -> IWhatsAppClient:
    return HttpxWhatsAppClient(access_token=settings.WHATSAPP_ACCESS_TOKEN)


def get_insight_repo_factory(
    settings: Settings = Depends(get_settings),
) -> SqlaInsightRepositoryFactory:
    return SqlaInsightRepositoryFactory(get_session_factory())


def get_generate_insight_use_case(
    repo_factory: SqlaInsightRepositoryFactory = Depends(get_insight_repo_factory),
    ollama_client: IOllamaClient = Depends(get_ollama_client),
    transcription_client: IOllamaClient | None = Depends(get_transcription_client),
    whatsapp_client: IWhatsAppClient = Depends(get_whatsapp_client),
    settings: Settings = Depends(get_settings),
) -> GenerateInsightUseCase:
    return GenerateInsightUseCase(
        repo_factory=repo_factory,
        ollama_client=ollama_client,
        model=settings.OLLAMA_MODEL,
        prompt_version=settings.OLLAMA_PROMPT_VERSION,
        whatsapp_client=whatsapp_client,
        transcription_client=transcription_client,
    )


async def get_business_account_repo(
    session: AsyncSession = Depends(get_db_session),
) -> IBusinessAccountRepository:
    return SqlaBusinessAccountRepository(session)


async def get_receive_message_use_case(
    session: AsyncSession = Depends(get_db_session),
    business_account_repo: IBusinessAccountRepository = Depends(get_business_account_repo),
    insight_generator: GenerateInsightUseCase = Depends(get_generate_insight_use_case),
) -> ReceiveMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReceiveMessageUseCase(
        repository=repo,
        business_account_repo=business_account_repo,
        insight_generator=insight_generator,
    )
