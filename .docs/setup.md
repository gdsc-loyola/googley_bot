# 🚀 Setup & Installation Guide

This guide provides comprehensive instructions for setting up the Googley Bot development and production environments.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **pip**: Latest version
- **Git**: For version control
- **Virtual Environment**: venv or conda
- **Database**: SQLite (development) or PostgreSQL (production)
- **Redis**: For caching and task queues (optional but recommended)

### External Services
- **Discord Application**: Bot token and application ID
- **GitHub**: Personal access token or GitHub App
- **Notion**: Integration token and database IDs
- **Google Calendar**: API credentials (optional)

## 🔧 Development Environment Setup

### 1. Clone the Repository

```bash
git clone # Insert Github Link
cd googley_bot
```

### 2. Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Using conda (alternative)
conda create -n googley-bot python=3.9
conda activate googley-bot
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Alternative: Install with poetry (if using)
poetry install --with dev
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# Use your preferred editor (nano, vim, code, etc.)
nano .env
```

### 5. Database Setup

```bash
# Initialize database (SQLite for development)
python -m alembic upgrade head

# Alternative: Create initial migration
python -m alembic revision --autogenerate -m "Initial migration"
python -m alembic upgrade head
```

### 6. Discord Bot Setup

```bash
# Register slash commands with Discord
python scripts/register_commands.py

# Test bot connection
python scripts/test_connection.py
```

### 7. Run the Bot

```bash
# Development mode with hot reload
python src/main.py

# Alternative: Using uvicorn for webhook server
uvicorn src.webhooks.app:app --reload --host 0.0.0.0 --port 8000
```

## 🔑 Configuration

### Discord Application Setup

1. **Create Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Navigate to "Bot" section and create a bot
   - Copy the bot token

2. **Configure Bot Permissions**:
   ```
   Required Permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Attach Files
   - Read Message History
   - Manage Roles (for auto-role assignment)
   - Manage Channels (for channel management)
   ```

3. **Generate Invite Link**:
   - Navigate to "OAuth2" > "URL Generator"
   - Select "bot" and "applications.commands" scopes
   - Select required permissions
   - Use generated URL to invite bot to your server

### Environment Variables

```env
# Discord Configuration
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
DISCORD_APPLICATION_ID=your_application_id_here

# Database Configuration
DATABASE_URL=sqlite:///./googley_bot.db
# For PostgreSQL: postgresql://user:password@localhost/googley_bot

# GitHub Integration
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
GITHUB_ORG=gdscloyola

# Notion Integration
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_TASKS=your_tasks_database_id
NOTION_DATABASE_TEAM=your_team_database_id

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/googley_bot.log

# Security
SECRET_KEY=your_secret_key_for_session_management
ENCRYPTION_KEY=your_encryption_key_for_sensitive_data

# Webhook Server
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_BASE_URL=https://your-domain.com/webhooks
```

### GitHub Integration Setup

1. **Create Personal Access Token**:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate new token with required scopes:
     ```
     - repo (for repository access)
     - read:org (for organization information)
     - read:user (for user information)
     ```

2. **Alternative: GitHub App** (Recommended for production):
   - Create a GitHub App in your organization settings
   - Configure webhook URL: `https://your-domain.com/webhooks/github`
   - Select required permissions and events
   - Install the app on required repositories

3. **Webhook Configuration**:
   - Set webhook URL in repository settings
   - Use webhook secret from environment variables
   - Select events: pushes, pull requests, issues, releases

### Notion Integration Setup

1. **Create Notion Integration**:
   - Go to [Notion Developers](https://www.notion.so/my-integrations)
   - Create new integration with required capabilities
   - Copy the integration token

2. **Configure Database Access**:
   - Share your Notion databases with the integration
   - Copy database IDs from database URLs
   - Ensure proper permissions are set

3. **Database Schema Requirements**:
   ```
   Tasks Database:
   - Title (Title)
   - Status (Select: Not Started, In Progress, Completed)
   - Assignee (Person)
   - Due Date (Date)
   - Priority (Select: Low, Medium, High)
   - Description (Rich Text)
   
   Team Database:
   - Name (Title)
   - Discord ID (Rich Text)
   - Role (Select)
   - Email (Email)
   - Start Date (Date)
   ```

### Run with Docker

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

## 🧪 Testing Setup

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_commands/test_checkin.py

# Run with verbose output
pytest -v
```

### Integration Tests

```bash
# Run integration tests (requires test database)
pytest tests/integration/ --integration

# Run with test database
TEST_DATABASE_URL=sqlite:///./test.db pytest
```

### Test Configuration

```python
# conftest.py
import pytest
from src.bot.client import create_bot
from src.utils.database import get_database

@pytest.fixture
async def bot():
    """Create test bot instance."""
    return create_bot()

@pytest.fixture
async def db():
    """Create test database connection."""
    return await get_database(test_mode=True)
```

## 🌐 Production Deployment

### Server Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB+ (depending on server size)
- **Storage**: 20GB+ SSD
- **Network**: Stable internet connection
- **OS**: Ubuntu 20.04+ or similar Linux distribution

### Production Setup

```bash
# Create production user
sudo useradd -m -s /bin/bash googley-bot
sudo su - googley-bot

# Clone repository
git clone # Insert Github Link
cd googley_bot

# Set up Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values
```

### Systemd Service

```ini
# /etc/systemd/system/googley-bot.service
[Unit]
Description=Googley Bot - Google Developers Guild Discord Bot
After=network.target

[Service]
Type=simple
User=googley-bot
WorkingDirectory=/home/googley-bot/googley-bot
Environment=PATH=/home/googley-bot/googley-bot/venv/bin
ExecStart=/home/googley-bot/googley-bot/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable googley_bot
sudo systemctl start googley_bot

# Check status
sudo systemctl status googley_bot

# View logs
sudo journalctl -u googley_bot -f
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/googley_bot-webhooks
server {
    listen 80;
    server_name your-domain.com;

    location /webhooks/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Certificate

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## 📊 Monitoring & Logging

### Log Configuration

```python
# logging_config.py
import logging
from loguru import logger
import sys

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/googley_bot.log",
    format="{time} | {level} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="10 MB",
    retention="30 days"
)
```

### Health Checks

```bash
# Health check endpoint
curl http://localhost:8000/health

# Bot status check
python scripts/health_check.py
```

### Monitoring Setup

```python
# Basic monitoring with healthchecks.io
import httpx

async def send_heartbeat():
    """Send heartbeat to monitoring service."""
    async with httpx.AsyncClient() as client:
        await client.get("https://hc-ping.com/your-uuid")
```

## 🔧 Troubleshooting

### Common Issues

1. **Bot Not Responding**:
   ```bash
   # Check bot status
   python scripts/test_connection.py
   
   # Verify token and permissions
   # Check Discord Developer Portal
   ```

2. **Database Connection Issues**:
   ```bash
   # Test database connection
   python scripts/test_database.py
   
   # Check database URL and credentials
   # Verify database server is running
   ```

3. **GitHub Webhook Issues**:
   ```bash
   # Test webhook endpoint
   curl -X POST http://localhost:8000/webhooks/github \
        -H "Content-Type: application/json" \
        -d '{"test": true}'
   
   # Check webhook secret and URL configuration
   ```

4. **Notion API Issues**:
   ```bash
   # Test Notion connection
   python scripts/test_notion.py
   
   # Verify integration token and database permissions
   ```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python src/main.py

# Enable Discord.py debug logging
export PYTHONPATH=src
python -c "
import discord
import asyncio
from src.main import main

discord.utils.setup_logging(level=logging.DEBUG)
asyncio.run(main())
"
```

### Performance Optimization

```bash
# Profile bot performance
python -m cProfile -o profile.stats src/main.py

# Analyze profile
python scripts/analyze_profile.py profile.stats

# Monitor memory usage
python scripts/memory_monitor.py
```

## 📚 Additional Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Notion API Documentation](https://developers.notion.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 🔄 Updates & Maintenance

### Updating the Bot

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Restart bot service
sudo systemctl restart googley_bot
```

### Backup Procedures

```bash
# Database backup
pg_dump googley_bot > backups/googley_bot_$(date +%Y%m%d_%H%M%S).sql

# Configuration backup
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz .env logs/

# Automated backup script
python scripts/backup.py
``` 
