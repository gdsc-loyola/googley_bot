#!/usr/bin/env python3
"""
GitHub Webhook Server

Standalone FastAPI server for handling GitHub webhooks.
This runs separately from the Discord bot to ensure webhook reliability.

Usage:
    python -m src.webhook_server
    
Environment Variables:
    - GITHUB_WEBHOOK_SECRET: Secret for validating webhook signatures
    - DISCORD_WEBHOOK_URL: Discord webhook URL for notifications
    - GITHUB_ALLOWED_REPOS: Comma-separated list of allowed repositories (optional)
    - WEBHOOK_HOST: Host to bind to (default: 0.0.0.0)
    - WEBHOOK_PORT: Port to bind to (default: 8080)
    - ENVIRONMENT: Environment (development/production)
"""

import os
import signal
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from loguru import logger

from dotenv import load_dotenv
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.webhook.app import webhook_app
from src.utils.logger import logger
from src.utils.logger import setup_logging


# Global handler instance for cleanup
webhook_handler = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down webhook server...")
    
    # Cleanup webhook handler
    if webhook_handler:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(webhook_handler.shutdown())
            else:
                loop.run_until_complete(webhook_handler.shutdown())
        except Exception as e:
            logger.error(f"Error during webhook handler shutdown: {e}")
    
    sys.exit(0)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    global webhook_handler
    
    # Startup
    logger.info("Starting GitHub webhook server...")
    
    # Initialize webhook handler
    from src.webhook.handlers import WebhookHandler
    webhook_handler = WebhookHandler()
    await webhook_handler.startup()
    
    logger.info("GitHub webhook server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GitHub webhook server...")
    
    if webhook_handler:
        await webhook_handler.shutdown()
    
    logger.info("GitHub webhook server shutdown complete")


def main():
    """Main entry point for the webhook server."""
    # Setup logging
    setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuration
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    environment = os.getenv("ENVIRONMENT", "production")
    
    # Validate required environment variables
    required_vars = ["GITHUB_WEBHOOK_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Log configuration
    logger.info(f"Starting webhook server on {host}:{port}")
    logger.info(f"Environment: {environment}")
    logger.info(f"Discord notifications: {'enabled' if os.getenv('DISCORD_WEBHOOK_URL') else 'disabled'}")
    
    allowed_repos = os.getenv("GITHUB_ALLOWED_REPOS", "").split(",")
    allowed_repos = [repo.strip() for repo in allowed_repos if repo.strip()]
    if allowed_repos:
        logger.info(f"Allowed repositories: {allowed_repos}")
    else:
        logger.info("Allowed repositories: all (no restrictions)")
    
    # Add lifespan to the app
    webhook_app.router.lifespan_context = lifespan
    
    # Configure uvicorn
    config = uvicorn.Config(
        webhook_app,
        host=host,
        port=port,
        log_level="info" if environment == "development" else "warning",
        access_log=environment == "development",
        reload=environment == "development",
        workers=1,  # Single worker to avoid issues with async tasks
    )
    
    # Run the server
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
