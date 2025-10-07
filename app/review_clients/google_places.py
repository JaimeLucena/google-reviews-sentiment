from __future__ import annotations

import os
from typing import List, Optional

import httpx

from ..schemas import BusinessReview


class GooglePlacesClient:
    """
    Minimal Google Places client to get a Place ID from a text query and retrieve reviews.
    Requires GOOGLE_MAPS_API_KEY env var.
    """

    def __init__(self, api_key: Optional[str] = None, *, timeout: float = 15.0):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_MAPS_API_KEY is required to use GooglePlacesClient.")
        self.timeout = timeout
        self._base = "https://maps.googleapis.com/maps/api/place"

    async def find_place_id(self, query: str) -> Optional[str]:
        """
        Uses Places 'Find Place' API with text input to resolve a place_id.
        """
        url = f"{self._base}/findplacefromtext/json"
        params = {
            "input": query,
            "inputtype": "textquery",
            "fields": "place_id",
            "key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        candidates = data.get("candidates") or []
        return candidates[0]["place_id"] if candidates else None

    async def fetch_reviews(self, place_id: str, *, limit: int = 10, language: str | None = None) -> List[BusinessReview]:
        """
        Uses Places 'Details' API to pull up to 'limit' reviews (Google typically returns up to 5 per call).
        Note: Google may cap at 5 reviews; pagination of reviews isn't fully supported by the public API.
        """
        url = f"{self._base}/details/json"
        params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": self.api_key,
        }
        if language:
            params["language"] = language

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        results = []
        reviews = (data.get("result") or {}).get("reviews") or []
        for rv in reviews[:limit]:
            results.append(
                BusinessReview(
                    author=rv.get("author_name"),
                    rating=rv.get("rating"),
                    time=str(rv.get("time")),
                    text=rv.get("text") or "",
                )
            )
        return results