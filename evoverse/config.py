# evoverse/config.py
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMConfig(BaseSettings):
    base_url: str = Field(default="http://localhost:11434/v1")
    api_key: str = Field(default="ollama")
    model: str = Field(default="qwen3-vl:32b")
    temperature: float = 0.2
    max_tokens: int = 2048

    model_config = {
        "env_prefix": "LLM_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class DatabaseConfig(BaseSettings):
    url: str = "sqlite:///evoverse.db"
    echo: bool = False

    model_config = {
        "env_prefix": "DB_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class EvoVerseConfig(BaseSettings):
    llm: LLMConfig = LLMConfig()
    db: DatabaseConfig = DatabaseConfig()

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


def get_config() -> EvoVerseConfig:
    return EvoVerseConfig()