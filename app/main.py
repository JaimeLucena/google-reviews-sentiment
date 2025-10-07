from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import (
    AnalyzeTextRequest,
    AnalyzeTextResponse,
    GoogleBusinessLookup,
    GoogleBusinessReviewsRequest,
    AnalyzeBusinessReviewsResponse,
    AnalyzeByQueryRequest,             # <-- nuevo
    AnalyzeByQueryResponse,            # <-- nuevo
)
from .chains import analyze_texts
from .review_clients import GooglePlacesClient

app = FastAPI(title=settings.service_name)

# CORS para Streamlit (localhost:8501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": settings.service_name}


@app.post("/analyze/text", response_model=AnalyzeTextResponse)
async def analyze_text(payload: AnalyzeTextRequest):
    if not payload.texts:
        raise HTTPException(status_code=400, detail="texts cannot be empty")
    results = await analyze_texts(payload)
    return AnalyzeTextResponse(results=results)


@app.post("/google/find-place")
async def google_find_place(body: GoogleBusinessLookup):
    try:
        client = GooglePlacesClient(settings.google_maps_api_key)
        place_id = await client.find_place_id(body.query)
        return {"query": body.query, "place_id": place_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/google/analyze-reviews", response_model=AnalyzeBusinessReviewsResponse)
async def google_analyze_reviews(body: GoogleBusinessReviewsRequest):
    try:
        client = GooglePlacesClient(settings.google_maps_api_key)
        reviews = await client.fetch_reviews(
            body.place_id, limit=body.limit, language=body.language or "es"
        )
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews returned by Google for this place_id.")

        texts = [r.text for r in reviews if r.text and r.text.strip()]
        if not texts:
            raise HTTPException(status_code=404, detail="No textual reviews available to analyze.")

        analysis = await analyze_texts(
            payload=AnalyzeTextRequest(
                texts=texts, language_hint=body.language, model_name=body.model_name
            )
        )
        return AnalyzeBusinessReviewsResponse(
            place_id=body.place_id, review_count=len(texts), results=analysis
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NUEVO: endpoint "todo en uno" para frontend (buscar + analizar)
@app.post("/google/analyze-by-query", response_model=AnalyzeByQueryResponse)
async def google_analyze_by_query(body: AnalyzeByQueryRequest):
    try:
        client = GooglePlacesClient(settings.google_maps_api_key)
        place_id = await client.find_place_id(body.query)
        if not place_id:
            raise HTTPException(status_code=404, detail="No place_id found for that query.")

        reviews = await client.fetch_reviews(
            place_id, limit=body.limit, language=body.language or "es"
        )
        texts = [r.text for r in reviews if r.text and r.text.strip()]
        if not texts:
            raise HTTPException(status_code=404, detail="No textual reviews available to analyze.")

        analysis = await analyze_texts(
            AnalyzeTextRequest(
                texts=texts, language_hint=body.language, model_name=body.model_name
            )
        )
        return AnalyzeByQueryResponse(
            query=body.query,
            place_id=place_id,
            review_count=len(texts),
            results=analysis,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))