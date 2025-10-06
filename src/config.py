"""Configuration settings for the Telegram Digest application."""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Telegram API settings
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_NAME: str = "telegram_session"

    # Telegram Bot settings (optional, for sending digest)
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    OUTPUT_TELEGRAM_CHANNEL: Optional[str] = os.getenv("OUTPUT_TELEGRAM_CHANNEL")

    # Cerebras AI settings
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
    CEREBRAS_MODEL: str = os.getenv("CEREBRAS_MODEL", "llama3.1-70b")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))
    MAX_TOKENS_RESPONSE: int = int(os.getenv("MAX_TOKENS_RESPONSE", "4000"))

    # Processing settings
    MAX_TOKENS_PER_CHUNK: int = int(os.getenv("MAX_TOKENS_PER_CHUNK", "50000"))
    CHARS_PER_TOKEN: int = 4  # Estimation: 1 token ≈ 4 characters

    # Default channels (can be overridden via CLI)
    DEFAULT_CHANNELS: List[str] = []

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        errors = []

        if not cls.TELEGRAM_API_ID or cls.TELEGRAM_API_ID == 0:
            errors.append("TELEGRAM_API_ID is not set")

        if not cls.TELEGRAM_API_HASH:
            errors.append("TELEGRAM_API_HASH is not set")

        if not cls.CEREBRAS_API_KEY:
            errors.append("CEREBRAS_API_KEY is not set")

        if errors:
            raise ValueError(
                f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        return max(1, len(text) // cls.CHARS_PER_TOKEN)


# Validate configuration on import
Config.validate()
