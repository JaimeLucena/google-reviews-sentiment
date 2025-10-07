from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# -------------------------------------------------------
# SENTIMENT ANALYSIS MODELS
# -------------------------------------------------------

class SentimentLabel(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class AspectSentiment(BaseModel):
    aspect: str = Field(..., description="The aspect/topic mentioned, such as 'service', 'price', 'food'.")
    label: SentimentLabel
    score: float = Field(..., ge=-1.0, le=1.0, description="Signed intensity for the aspect (-1..1).")


class ReviewSentiment(BaseModel):
    text: str
    language: Optional[str] = Field(None, description="Detected or declared language of the text.")
    label: SentimentLabel
    score: float = Field(..., ge=-1.0, le=1.0)
    rationale: str = Field(..., description="Short explanation for the label.")
    aspects: List[AspectSentiment] = Field(default_factory=list)


class AnalyzeTextRequest(BaseModel):
    texts: List[str]
    language_hint: Optional[str] = Field(
        None, description="Optional language hint like 'en', 'es'."
    )
    model_name: Optional[str] = None


class AnalyzeTextResponse(BaseModel):
    results: List[ReviewSentiment]


# -------------------------------------------------------
# GOOGLE PLACES / REVIEWS MODELS
# -------------------------------------------------------

class GoogleBusinessLookup(BaseModel):
    query: str = Field(..., description="Free text query like 'Bar Central Madrid'.")


class GoogleBusinessReviewsRequest(BaseModel):
    place_id: str = Field(..., description="Google Place ID.")
    limit: int = Field(10, ge=1, le=50)
    language: Optional[str] = None
    model_name: Optional[str] = None


class BusinessReview(BaseModel):
    author: Optional[str] = None
    rating: Optional[float] = None
    time: Optional[str] = None
    text: str


class AnalyzeBusinessReviewsResponse(BaseModel):
    place_id: str
    review_count: int
    results: List[ReviewSentiment]


# -------------------------------------------------------
# COMBINED ENDPOINT: FIND + ANALYZE BY QUERY
# -------------------------------------------------------

class AnalyzeByQueryRequest(BaseModel):
    query: str = Field(..., description="Free text query such as 'El Tigre Madrid'.")
    limit: int = Field(5, ge=1, le=50)
    language: Optional[str] = Field("es", description="Language for Google reviews retrieval.")
    model_name: Optional[str] = Field(None, description="Override default LLM model if desired.")


class AnalyzeByQueryResponse(BaseModel):
    query: str
    place_id: str
    review_count: int
    results: List[ReviewSentiment]