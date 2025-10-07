# app/chains.py
from __future__ import annotations

from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from .config import settings
from .schemas import AnalyzeTextRequest, ReviewSentiment
from .utils.text_clean import normalize_text


def build_llm(model_name: str | None = None) -> ChatOpenAI:
    """
    Build the chat model. Uses request model_name or falls back to env MODEL_NAME.
    """
    name: str = model_name or settings.model_name or "gpt-4o-mini"
    return ChatOpenAI(model=name)


def build_sentiment_chain(model_name: str | None = None):
    """
    LCEL chain: (preprocess) -> prompt -> llm -> Pydantic parser
    """
    parser = PydanticOutputParser(pydantic_object=ReviewSentiment)

    system = (
        "You are a precise sentiment analyst. "
        "Return a single JSON object strictly matching the given schema.\n"
        "{format_instructions}\n"
        "Scoring: negative=-1..-0.05, neutral≈-0.05..0.05, positive=0.05..1.0.\n"
        "Keep rationale concise. Extract aspects if present; otherwise return an empty list."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "user",
                "Analyze the sentiment of the following review.\n"
                "Language hint: {language_hint}\n"
                "Text: ```{text}```",
            ),
        ]
    )

    llm = build_llm(model_name)

    # Preprocess & inject format_instructions so ChatPromptTemplate doesn't
    # try to treat JSON-schema braces as variables.
    pre = RunnableLambda(
        lambda x: {
            "text": normalize_text(x["text"]),
            "language_hint": x.get("language_hint"),
            "format_instructions": parser.get_format_instructions(),
        }
    )

    chain = pre | prompt | llm | parser
    return chain


async def analyze_texts(payload: AnalyzeTextRequest) -> List[ReviewSentiment]:
    chain = build_sentiment_chain(payload.model_name)
    inputs = [{"text": t, "language_hint": payload.language_hint} for t in payload.texts]
    results: List[ReviewSentiment] = await chain.abatch(inputs)
    return results