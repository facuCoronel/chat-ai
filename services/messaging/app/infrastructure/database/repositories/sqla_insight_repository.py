from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.insight import (
    CommercialRisk,
    Intent,
    MainEmotion,
    MessageInsight,
    SenderRole,
    Sentiment,
    Urgency,
)
from app.domain.entities.message import Platform
from app.domain.repositories.insight_repository import IInsightRepository
from app.infrastructure.database.models import InsightORM


class SqlaInsightRepository(IInsightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, insight: MessageInsight) -> MessageInsight:
        orm = _to_orm(insight)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_entity(orm)

    async def find_by_message_id(self, message_id: str) -> Optional[MessageInsight]:
        result = await self._session.execute(
            select(InsightORM).where(InsightORM.message_id == message_id)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def find_by_wamid(self, wamid: str) -> Optional[MessageInsight]:
        result = await self._session.execute(
            select(InsightORM).where(InsightORM.wamid == wamid)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def find_recent_by_sender(
        self, sender_id: str, platform: str, limit: int
    ) -> list[MessageInsight]:
        result = await self._session.execute(
            select(InsightORM)
            .where(InsightORM.sender_id == sender_id, InsightORM.platform == platform)
            .order_by(InsightORM.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [_to_entity(r) for r in reversed(rows)]


def _to_orm(entity: MessageInsight) -> InsightORM:
    return InsightORM(
        id=entity.id,
        message_id=entity.message_id,
        wamid=entity.wamid,
        platform=entity.platform.value,
        sender_id=entity.sender_id,
        sender_role=entity.sender_role.value,
        sentiment=entity.sentiment.value,
        main_emotion=entity.main_emotion.value,
        intent=entity.intent.value,
        urgency=entity.urgency.value,
        commercial_risk=entity.commercial_risk.value,
        summary=entity.summary,
        recommended_action=entity.recommended_action,
        insights=entity.insights,
        raw_model_response=entity.raw_model_response,
        model_name=entity.model_name,
        prompt_version=entity.prompt_version,
        created_at=entity.created_at,
    )


def _to_entity(orm: InsightORM) -> MessageInsight:
    return MessageInsight(
        id=orm.id,
        message_id=orm.message_id,
        wamid=orm.wamid,
        platform=Platform(orm.platform),
        sender_id=orm.sender_id,
        sender_role=SenderRole(orm.sender_role),
        sentiment=Sentiment(orm.sentiment),
        main_emotion=MainEmotion(orm.main_emotion),
        intent=Intent(orm.intent),
        urgency=Urgency(orm.urgency),
        commercial_risk=CommercialRisk(orm.commercial_risk),
        summary=orm.summary,
        recommended_action=orm.recommended_action,
        insights=orm.insights,
        raw_model_response=orm.raw_model_response,
        model_name=orm.model_name,
        prompt_version=orm.prompt_version,
        created_at=orm.created_at,
    )
