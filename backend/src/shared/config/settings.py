from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from src.shared.common.errors import ConfigError


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and (value is None or value.strip() == ""):
        raise ConfigError(f"Thiếu biến bắt buộc: {name}")
    return value if value is not None else ""


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"Biến {name} phải là số nguyên, nhận được: {raw!r}") from exc


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"Biến {name} phải là số, nhận được: {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    qwen_api_key: str
    hf_token: str
    chroma_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    app_port: int = 8000
    refresh_token_ttl_hours: int = 720
    log_level: str = "INFO"
    chunk_size: int = 800
    chunk_overlap: int = 120
    fetch_k: int = 10
    top_k: int = 5
    alpha: float = 0.7
    dedup_threshold: float = 0.92
    embedding_dim: int = 768
    embedding_max_tokens: int = 256
    no_info_threshold: float = 0.15
    request_timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: float = 0.5
    history_max_turns: int = 10
    question_max_length: int = 2000
    chroma_collection: str = "tlu_chunks"
    database_url: str = "sqlite:///data/chatbot_tlu.db"
    embedding_model: str = "bkai-foundation-models/vietnamese-bi-encoder"
    router_model: str = "qwen/qwen3.8-27b"
    answer_model: str = "qwen3-235b-a22b"
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            groq_api_key=_env("GROQ_API_KEY", required=True),
            qwen_api_key=_env("QWEN_API_KEY", required=True),
            qwen_base_url=_env(
                "QWEN_BASE_URL",
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            ).rstrip("/"),
            answer_model=_env("ANSWER_MODEL", "qwen3-235b-a22b"),
            hf_token=_env("HF_TOKEN", required=True),
            chroma_url=_env("CHROMA_URL", required=True).rstrip("/"),
            neo4j_uri=_env("NEO4J_URI", required=True),
            neo4j_user=_env("NEO4J_USER", required=True),
            neo4j_password=_env("NEO4J_PASSWORD", required=True),
            app_port=_env_int("APP_PORT", 8000),
            refresh_token_ttl_hours=_env_int("REFRESH_TOKEN_TTL_HOURS", 720),
            log_level=_env("LOG_LEVEL", "INFO").upper(),
            chunk_size=_env_int("CHUNK_SIZE", 800),
            chunk_overlap=_env_int("CHUNK_OVERLAP", 120),
            fetch_k=_env_int("FETCH_K", 10),
            top_k=_env_int("TOP_K", 5),
            alpha=_env_float("ALPHA", 0.7),
            dedup_threshold=_env_float("DEDUP_THRESHOLD", 0.92),
            embedding_dim=_env_int("EMBEDDING_DIM", 768),
            embedding_max_tokens=_env_int("EMBEDDING_MAX_TOKENS", 256),
            no_info_threshold=_env_float("NO_INFO_THRESHOLD", 0.15),
            request_timeout_seconds=_env_int("REQUEST_TIMEOUT_SECONDS", 30),
            max_retries=_env_int("MAX_RETRIES", 3),
            retry_backoff_seconds=_env_float("RETRY_BACKOFF_SECONDS", 0.5),
            history_max_turns=_env_int("HISTORY_MAX_TURNS", 10),
            question_max_length=_env_int("QUESTION_MAX_LENGTH", 2000),
            database_url=_env("DATABASE_URL", "sqlite:///data/chatbot_tlu.db"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
