from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.dtos.insight_dto import GenerateInsightRequest
    from app.application.ports.insight_generator import IInsightGenerator

logger = logging.getLogger(__name__)


async def run_insight_safely(
    generator: "IInsightGenerator",
    request: "GenerateInsightRequest",
) -> None:
    """Fire-and-forget wrapper used by use cases that trigger insight generation."""
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
