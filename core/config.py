import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="/app/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    BRAIN_SECRET_KEY: str = "pings-default-secret-change-me"
    NVIDIA_API_KEY: str = ""
    MODEL_VISION: str = "meta/llama-3.2-11b-vision-instruct"
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    DEFAULT_ZEN_MODEL: str = "opencode/mimo-v2.5-free"
    OPENCODE_CONFIG_PATH: str = "/app/opencode.json"
    OPENCODE_SERVER_URL: str = "http://pings-opencode:4096"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ALLOWED_USER_ID: str = ""

    SEARXNG_URL: str = "http://pings-searxng:8080"
    SERPAPI_KEY: str = ""
    NTFY_URL: str = "http://pings-ntfy:80"
    NTFY_TOPIC: str = "pings"

    SSH_HOST: str = ""
    SSH_PORT: int = 22
    SSH_USER: str = ""
    SSH_AUTH_TYPE: str = "key"
    SSH_KEY_PATH: str = "/app/keys/id_rsa"
    SSH_PASSWORD: str = ""

    PROACTIVE_INTERVAL_MINUTES: int = 30
    JOURNAL_PATH: str = "/app/persona/JOURNAL.md"

    TOOL_REGISTRY_ENABLED: bool = True

    DANGER_PATTERNS: List[str] = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=",
        "> /dev/sda",
        ":(){:|:&};:",
        "chmod -R 777 /",
        "chown -R",
        "shutdown",
        "reboot",
        "halt",
        "init 0",
        "init 6",
    ]

    CHROMA_URL: str = "http://pings-chroma:8000"
    SQLITE_DB_PATH: str = "/app/data/pings.db"
    WORKSPACE_PATH: str = "/app/workspace"

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    MIN_SOURCES_PER_SUBTOPIC: int = 15
    MIN_WORDS_PER_SECTION: int = 500
    MIN_WORDS_TOTAL: int = 8000
    MAX_SEARCH_REFORMULATIONS: int = 6
    MAX_SECTION_REWRITE_ATTEMPTS: int = 3
    FETCH_TIMEOUT_SECONDS: int = 15
    FETCH_CONCURRENCY: int = 5


settings = Settings()
