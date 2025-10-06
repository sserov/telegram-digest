"""Configuration settings for the Telegram Digest application."""

import os
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
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

    @classmethod
    def load_channels_config(cls, config_path: str = "channels.yaml") -> Dict[str, Any]:
        """
        Load channels configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary with configuration: channels, groups, defaults
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ValueError(f"Empty configuration file: {config_path}")
        
        # Validate structure
        if 'channels' not in config and 'groups' not in config:
            raise ValueError("Configuration must contain 'channels' or 'groups' section")
        
        return config

    @classmethod
    def get_channels_from_config(
        cls, 
        config_path: str = "channels.yaml",
        group: Optional[str] = None
    ) -> List[str]:
        """
        Get list of channels from YAML configuration.
        
        Args:
            config_path: Path to YAML configuration file
            group: Optional group name to load specific channel group
            
        Returns:
            List of channel names
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If group not found or invalid config
        """
        config = cls.load_channels_config(config_path)
        
        # If group specified, load channels from that group
        if group:
            if 'groups' not in config:
                raise ValueError(f"No groups defined in {config_path}")
            
            if group not in config['groups']:
                available_groups = ', '.join(config['groups'].keys())
                raise ValueError(
                    f"Group '{group}' not found. Available groups: {available_groups}"
                )
            
            channels = config['groups'][group]
        else:
            # Load default channels list
            if 'channels' not in config:
                raise ValueError(f"No 'channels' section in {config_path}")
            
            channels = config['channels']
        
        if not isinstance(channels, list):
            raise ValueError(f"Channels must be a list, got {type(channels)}")
        
        if not channels:
            raise ValueError("Channels list is empty")
        
        return channels

    @classmethod
    def get_default_settings(cls, config_path: str = "channels.yaml") -> Dict[str, Any]:
        """
        Get default settings from YAML configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary with default settings (empty if no defaults section)
        """
        try:
            config = cls.load_channels_config(config_path)
            return config.get('defaults', {})
        except (FileNotFoundError, ValueError):
            return {}


# Validate configuration on import
Config.validate()
