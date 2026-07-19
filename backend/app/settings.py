from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Geometry CAD Assistant"
    database_url: str = "sqlite:///./cad_drawings.db"
    ollama_url: str = "http://127.0.0.1:11434"
    preferred_model: str = "qwen2.5-coder:7b"
    fallback_model: str = "llama3.1:8b"
    cors_origins: list[str] = [
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]


settings = Settings()

