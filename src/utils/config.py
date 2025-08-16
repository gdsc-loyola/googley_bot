"""Configuration management utilities."""

import os
from typing import Any, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Discord Configuration (REQUIRED)
    discord_token: str = "your_discord_token_here"
    discord_guild_id: str = "your_guild_id_here"
    discord_application_id: str = "your_application_id_here"
    discord_command_prefix: str = "!"
    discord_description: str = "Google Developers Guild on Campus - Loyola Discord Bot"
    discord_activity_name: str = "with productivity tools"
    discord_activity_type: str = "playing"

    # Database Configuration
    database_url: str  # Required from environment variable

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/googley_bot.log"
    debug_mode: bool = False

    # Development Settings
    development_mode: bool = True

    # Optional integrations
    github_token: Optional[str] = None
    notion_token: Optional[str] = None
    notion_database_tasks: Optional[str] = None
    notion_database_teams: Optional[str] = None
    notion_database_projects: Optional[str] = None
    notion_database_resources: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


def get_settings() -> Settings:
    """Get application settings instance."""
    # Explicitly load .env file if it exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    settings = Settings()
    
    # Debug: Print config loading details
    if os.getenv('DEBUG_CONFIG'):
        print(f"🔍 Config Debug:")
        print(f"  .env file exists: {os.path.exists('.env')}")
        print(f"  DATABASE_URL env var: {os.getenv('DATABASE_URL', 'NOT SET')}")
        print(f"  Final database_url: {settings.database_url}")
        print(f"  Discord token loaded: {'Yes' if settings.discord_token != 'your_discord_token_here' else 'No (using default)'}")
        print(f"  Development mode: {settings.development_mode}")
    
    return settings


# Global settings instance
settings = get_settings() 