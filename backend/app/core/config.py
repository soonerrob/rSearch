from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Reddit API
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str = "GummySearch/0.1.0"

    # OpenAI
    OPENAI_API_KEY: str

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reddit Audience Research Tool"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = Settings() 