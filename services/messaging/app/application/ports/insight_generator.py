from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.application.dtos.insight_dto import GenerateInsightRequest, GenerateInsightResponse


class IInsightGenerator(Protocol):
    """Decouples ReceiveMessageUseCase from the concrete GenerateInsightUseCase."""

    async def execute(
        self, request: "GenerateInsightRequest"
    ) -> "GenerateInsightResponse": ...
