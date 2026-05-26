from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.domain.repositories.insight_repository import IInsightRepository


class IInsightRepositoryContextFactory(Protocol):
    """Creates IInsightRepository instances with their own session lifecycle.

    Injecting a factory (not a session) into GenerateInsightUseCase ensures
    the background task owns its own DB session independently of the HTTP request.
    """

    def __call__(self) -> AbstractAsyncContextManager["IInsightRepository"]: ...
