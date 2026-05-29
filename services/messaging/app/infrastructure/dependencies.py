from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.generate_insight import GenerateInsightUseCase
from app.application.use_cases.get_conversation import GetConversationUseCase
from app.application.use_cases.list_contacts import ListContactsUseCase
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.application.use_cases.reply_message import ReplyMessageUseCase
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.services.ollama_client import IOllamaClient
from app.domain.services.whatsapp_client import IWhatsAppClient
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database.engine import get_session_factory
from app.infrastructure.database.factories.insight_repository_factory import (
    SqlaInsightRepositoryFactory,
)
from app.infrastructure.database.repositories.sqla_business_account_repository import SqlaBusinessAccountRepository
from app.infrastructure.database.repositories.sqla_conversation_repository import SqlaConversationRepository
from app.infrastructure.database.repositories.sqla_message_repository import SqlaMessageRepository
from app.infrastructure.http.ollama_client import HttpxOllamaClient
from app.infrastructure.http.whisper_client import HttpxWhisperClient
from app.infrastructure.http.whatsapp_client import HttpxWhatsAppClient
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager, connection_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


def get_ollama_client(settings: Settings = Depends(get_settings)) -> IOllamaClient:
    return HttpxOllamaClient(base_url=settings.OLLAMA_BASE_URL)


def get_transcription_client(settings: Settings = Depends(get_settings)) -> IOllamaClient | None:
    if settings.WHISPER_BASE_URL:
        return HttpxWhisperClient(base_url=settings.WHISPER_BASE_URL, api_key=settings.WHISPER_API_KEY)
    return None


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


def get_connection_manager() -> WebSocketConnectionManager:
    return connection_manager


async def get_business_account_repo(
    session: AsyncSession = Depends(get_db_session),
) -> IBusinessAccountRepository:
    return SqlaBusinessAccountRepository(session)


async def get_receive_message_use_case(
    session: AsyncSession = Depends(get_db_session),
    business_account_repo: IBusinessAccountRepository = Depends(get_business_account_repo),
    insight_generator: GenerateInsightUseCase = Depends(get_generate_insight_use_case),
    publisher: WebSocketConnectionManager = Depends(get_connection_manager),
) -> ReceiveMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReceiveMessageUseCase(
        repository=repo,
        business_account_repo=business_account_repo,
        insight_generator=insight_generator,
        message_publisher=publisher,
    )


async def get_list_contacts_use_case(
    session: AsyncSession = Depends(get_db_session),
    business_account_repo: IBusinessAccountRepository = Depends(get_business_account_repo),
) -> ListContactsUseCase:
    repo = SqlaConversationRepository(session)
    return ListContactsUseCase(repo=repo, business_account_repo=business_account_repo)


async def get_get_conversation_use_case(
    session: AsyncSession = Depends(get_db_session),
    business_account_repo: IBusinessAccountRepository = Depends(get_business_account_repo),
) -> GetConversationUseCase:
    repo = SqlaConversationRepository(session)
    return GetConversationUseCase(repo=repo, business_account_repo=business_account_repo)


async def get_reply_use_case(
    wa_client: IWhatsAppClient = Depends(get_whatsapp_client),
    session: AsyncSession = Depends(get_db_session),
    business_account_repo: IBusinessAccountRepository = Depends(get_business_account_repo),
    insight_generator: GenerateInsightUseCase = Depends(get_generate_insight_use_case),
    publisher: WebSocketConnectionManager = Depends(get_connection_manager),
) -> ReplyMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReplyMessageUseCase(
        whatsapp_client=wa_client,
        repository=repo,
        business_account_repo=business_account_repo,
        insight_generator=insight_generator,
        message_publisher=publisher,
    )
