from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from ..schemas import BusinessReview


class ReviewsClient(ABC):
    @abstractmethod
    async def find_place_id(self, query: str) -> Optional[str]:
        ...

    @abstractmethod
    async def fetch_reviews(self, place_id: str, *, limit: int = 10, language: str | None = None) -> List[BusinessReview]:
        ...