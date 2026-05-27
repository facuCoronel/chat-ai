from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.generate_insight import GenerateInsightUseCase
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.application.use_cases.reply_message import ReplyMessageUseCase
from app.domain.services.ollama_client import IOllamaClient
from app.domain.services.whatsapp_client import IWhatsAppClient
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database.engine import get_session_factory
from app.infrastructure.database.factories.insight_repository_factory import (
    SqlaInsightRepositoryFactory,
)
from app.infrastructure.database.repositories.sqla_message_repository import SqlaMessageRepository
from app.infrastructure.http.ollama_client import HttpxOllamaClient
from app.infrastructure.http.whatsapp_client import HttpxWhatsAppClient
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager, connection_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


def get_ollama_client(settings: Settings = Depends(get_settings)) -> IOllamaClient:
    return HttpxOllamaClient(base_url=settings.OLLAMA_BASE_URL)


def get_insight_repo_factory(
    settings: Settings = Depends(get_settings),
) -> SqlaInsightRepositoryFactory:
    return SqlaInsightRepositoryFactory(get_session_factory())


def get_generate_insight_use_case(
    repo_factory: SqlaInsightRepositoryFactory = Depends(get_insight_repo_factory),
    ollama_client: IOllamaClient = Depends(get_ollama_client),
    settings: Settings = Depends(get_settings),
) -> GenerateInsightUseCase:
    return GenerateInsightUseCase(
        repo_factory=repo_factory,
        ollama_client=ollama_client,
        model=settings.OLLAMA_MODEL,
        prompt_version=settings.OLLAMA_PROMPT_VERSION,
    )


def get_connection_manager() -> WebSocketConnectionManager:
    return connection_manager


async def get_receive_message_use_case(
    session: AsyncSession = Depends(get_db_session),
    insight_generator: GenerateInsightUseCase = Depends(get_generate_insight_use_case),
    publisher: WebSocketConnectionManager = Depends(get_connection_manager),
) -> ReceiveMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReceiveMessageUseCase(repo, insight_generator=insight_generator, message_publisher=publisher)


def get_whatsapp_client(settings: Settings = Depends(get_settings)) -> IWhatsAppClient:
    return HttpxWhatsAppClient(
        phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
        access_token=settings.WHATSAPP_ACCESS_TOKEN,
    )


async def get_reply_use_case(
    wa_client: IWhatsAppClient = Depends(get_whatsapp_client),
    session: AsyncSession = Depends(get_db_session),
    insight_generator: GenerateInsightUseCase = Depends(get_generate_insight_use_case),
    publisher: WebSocketConnectionManager = Depends(get_connection_manager),
    settings: Settings = Depends(get_settings),
) -> ReplyMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReplyMessageUseCase(
        whatsapp_client=wa_client,
        repository=repo,
        phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
        insight_generator=insight_generator,
        message_publisher=publisher,
    )
