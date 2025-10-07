from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv, find_dotenv

env_path = find_dotenv()
load_dotenv(dotenv_path=env_path, override=False)

@dataclass(frozen=True)
class Settings:
    service_name: str = os.getenv("SERVICE_NAME", "sentiment-service")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    google_maps_api_key: str | None = os.getenv("GOOGLE_MAPS_API_KEY")

    # network
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()