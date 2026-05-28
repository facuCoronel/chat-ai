from __future__ import annotations

from abc import ABC, abstractmethod


class IBusinessAccountRepository(ABC):

    @abstractmethod
    async def get_active_external_ids(self) -> set[str]:
        """Return the set of external_ids for all active business accounts."""
        ...
