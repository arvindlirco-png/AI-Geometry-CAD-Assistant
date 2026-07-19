from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Geometry CAD Assistant"
    database_url: str = "sqlite:///./cad_drawings.db"
    ollama_url: str = "http://127.0.0.1:11434"
    preferred_model: str = "qwen2.5-coder:7b"
    fallback_model: str = "llama3.1:8b"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    cors_origins: list[str] = [
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]


settings = Settings()
