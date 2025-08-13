# 🚀 Development Setup Guide

This guide will help you set up the Googley Bot development environment with PostgreSQL.

## 📋 Prerequisites

1. **Python 3.9+**
2. **PostgreSQL 12+** 
3. **Git**
4. **Virtual Environment** (venv recommended)

## 🐘 PostgreSQL Setup

### Windows (using PostgreSQL installer)

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings (remember the postgres password)
3. Open pgAdmin or use psql command line

### macOS (using Homebrew)

```bash
brew install postgresql
brew services start postgresql
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE googley_bot_dev;
CREATE USER googley_bot WITH PASSWORD 'googley_bot_password';
GRANT ALL PRIVILEGES ON DATABASE googley_bot_dev TO googley_bot;

-- For testing (optional)
CREATE DATABASE googley_bot_test;
GRANT ALL PRIVILEGES ON DATABASE googley_bot_test TO googley_bot;

-- Exit psql
\q
```

## 🐍 Python Environment Setup

### 1. Clone Repository

```bash
git clone # Insert Github Link
cd googley_bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing, linting, etc.)
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Use your preferred editor (notepad, nano, vim, code, etc.)
code .env  # or nano .env
```

**Required environment variables:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://googley_bot:googely_bot_password@localhost:5432/googley_bot_dev

# Discord (get from Discord Developer Portal)
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
DISCORD_APPLICATION_ID=your_application_id_here

# GitHub (get from GitHub Settings > Developer settings)
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_ORG=googledevelopersguild

# Notion (get from Notion Developers)
NOTION_TOKEN=secret_your_notion_token_here
```

## 🗄️ Database Setup

### 1. Test Connection

```bash
python scripts/setup_database.py test
```

### 2. Initialize Database

```bash
# Create all tables and default configuration
python scripts/setup_database.py setup
```

### 3. Generate Initial Migration

```bash
# Generate the first migration
python scripts/create_migration.py generate -m "Initial database schema"

# Apply the migration
python scripts/create_migration.py upgrade
```

## 🎮 Discord Bot Setup

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Googley Bot - Dev")
4. Navigate to "Bot" section
5. Click "Add Bot"
6. Copy the bot token
7. Enable necessary intents:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent

### 2. Bot Permissions

Required permissions (permission integer: `8589934592`):
- Send Messages
- Use Slash Commands
- Embed Links
- Attach Files
- Read Message History
- Manage Roles
- Manage Channels
- View Channels

### 3. Invite Bot to Server

1. Go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select permissions listed above
4. Use generated URL to invite bot

## 🔧 Development Tools Setup

### 1. Pre-commit Hooks

```bash
# Install pre-commit hooks for code quality
pre-commit install
```

### 2. IDE Configuration

**VS Code** (recommended extensions):
- Python
- Pylance
- Black Formatter
- Ruff

**PyCharm**:
- Configure Python interpreter to use venv
- Enable Black as code formatter
- Configure Ruff as linter

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_models/test_user.py

# Run integration tests (requires database)
pytest tests/integration/ --integration
```

## 🚀 Running the Bot

### Development Mode

```bash
# Run the main bot
python src/main.py

# Run with debug logging
DEBUG_MODE=true python src/main.py
```

### Webhook Server (for GitHub/external integrations)

```bash
# Run webhook server alongside bot
uvicorn src.webhooks.app:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Database Management

### Migrations

```bash
# Generate new migration after model changes
python scripts/create_migration.py generate -m "Add new feature"

# Apply migrations
python scripts/create_migration.py upgrade

# Rollback migration
python scripts/create_migration.py downgrade -1

# View migration history
python scripts/create_migration.py history
```

### Reset Database

```bash
# ⚠️ This will delete all data!
python scripts/setup_database.py reset
```

## 🔍 Troubleshooting

### Database Connection Issues

```bash
# Test connection
python scripts/setup_database.py test

# Check PostgreSQL service
# Windows
services.msc  # Look for PostgreSQL service

# macOS
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql
```

### Discord Bot Issues

1. **Bot not responding**: Check token and permissions
2. **Slash commands not appearing**: Re-run command registration
3. **Permission errors**: Check bot role hierarchy

### Environment Issues

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Check installed packages
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Next Steps

1. **Read the documentation** in `.docs/` folder
2. **Review the project structure** in `.docs/project_structure.md`
3. **Check development tasks** in `.docs/tasks.md`
4. **Start implementing** Phase 1 features

---

**Happy coding! 🎉** 
