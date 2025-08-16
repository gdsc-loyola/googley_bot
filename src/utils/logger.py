"""Logging configuration using loguru."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from .config import settings


def setup_logging() -> None:
    """Configure loguru logging for the application."""
    # Remove default handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Console handler with colors and formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler for persistent logging
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | "
               "{level: <8} | "
               "{name}:{function}:{line} - "
               "{message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    # Error file handler for errors and above
    error_log_file = log_file_path.parent / "error.log"
    logger.add(
        str(error_log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | "
               "{level: <8} | "
               "{name}:{function}:{line} - "
               "{message}\n{exception}",
        level="ERROR",
        rotation="5 MB",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    if settings.debug_mode:
        logger.info("🐛 Debug mode enabled")
        # Add debug file handler in debug mode
        debug_log_file = log_file_path.parent / "debug.log"
        logger.add(
            str(debug_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} - "
                   "{message}",
            level="DEBUG",
            rotation="50 MB",
            retention="7 days",
            compression="zip",
        )


def get_logger(name: str) -> Any:
    """Get a logger instance for the given name."""
    return logger.bind(name=name)


def log_discord_event(event_name: str, **kwargs: Any) -> None:
    """Log Discord events with structured data."""
    logger.info(f"Discord Event: {event_name}", extra={"discord_event": event_name, **kwargs})


def log_command_usage(command_name: str, user_id: str, guild_id: str, **kwargs: Any) -> None:
    """Log command usage for analytics."""
    logger.info(
        f"Command executed: {command_name}",
        extra={
            "command": command_name,
            "user_id": user_id,
            "guild_id": guild_id,
            "event_type": "command_usage",
            **kwargs,
        }
    )


def log_integration_event(integration: str, action: str, **kwargs: Any) -> None:
    """Log integration events (GitHub, Notion, etc.)."""
    logger.info(
        f"Integration {integration}: {action}",
        extra={
            "integration": integration,
            "action": action,
            "event_type": "integration",
            **kwargs,
        }
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log errors with context information."""
    context = context or {}
    logger.error(
        f"Error occurred: {str(error)}",
        extra={"error_type": type(error).__name__, "context": context}
    )


# Initialize logging when module is imported
setup_logging() 