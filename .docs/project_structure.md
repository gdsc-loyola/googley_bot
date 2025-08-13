# 📁 Project Structure

This document outlines the recommended project structure for the Googley Bot built with Python and discord.py.

## 🏗️ Directory Layout

```
googley_bot/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── client.py              # Main bot client setup 
│   │   └── events.py              # Event handlers (ready, message, etc.) 
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── github.py              # GitHub integration commands   
│   │   ├── notion.py              # Notion integration commands 
│   │   ├── sheets.py              # Google Sheets integration commands
│   │   └── utils.py               # Utility commands (ping, etc.) 
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── github/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # GitHub API client 
│   │   │   ├── webhooks.py        # Webhook handlers 
│   │   │   └── operations.py      # GitHub operations 
│   │   ├── notion/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Notion API client 
│   │   │   ├── schemas.py         # Pydantic models for Notion data 
│   │   │   ├── parser.py          # Parses models to correct Notion models 
│   │   │   ├── operations.py      # Notion database operations
│   │   ├── telegram/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Telegram API client 
│   │   │   ├── schemas.py         # Pydantic models for Telegram data  
│   │   │   └── operations.py      # Telegram database operations
│   │   └── sheets/ 
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Google Sheets API client 
│   │   │   ├── schemas.py         # Pydantic models for Google Sheets data
│   │   │   └── operations.py      # Google Sheets database operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management 
│   │   ├── database.py            # Database operations (SQLite/PostgreSQL) 
│   │   └── logger.py              # Logging utilities   
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # Base database models 
│   │   ├── config.py              # Configuration management
│   │   ├── github.py              # Github related models
│   │   ├── notion.py              # Notion related models
│   │   ├── user.py                # User-related models 
│   │   ├── tasks.py               # Task management models 
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── github.py              # GitHub webhook schemas 
│   │   ├── notion.py              # Notion API response schemas 
│   │   └── discord.py             # Discord-specific schemas  
│   ├── webhook_server.py          # Handles GITHUB events via FastAPI 
│   └── main.py                    # Application entry point
├── alembic/                       # Database migrations (if using SQLAlchemy)
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── .docs/                         # Documentation
│   ├── project_structure.md
│   ├── tasks.md
│   ├── features.md
│   └── setup.md
├── .env.example                   # Environment variables template
├── .gitignore
├── requirements.txt               # Python dependencies
├── alembic.ini                    # Database migration config (if using)
└── README.md
```

## 🧩 Architecture Overview

### Bot Layer (`src/bot/`)
- **client.py**: Main Discord bot client with setup and configuration
- **events.py**: Event handlers for Discord events (member join, message creation, etc.)

### Commands Layer (`src/commands/`)
Each module contains related slash commands and command groups:
- **admin.py**: Server administration commands
- **checkin.py**: Time tracking and work session commands
- **github.py**: GitHub repository interaction commands
- **intern.py**: Intern-specific productivity tools
- **notion.py**: Notion workspace integration commands
- **standup.py**: Daily standup and progress tracking
- **utils.py**: General utility commands

### Integration Layer (`src/integrations/`)
External API integrations with proper separation of concerns:
- **GitHub**: API client, webhook handlers, and operations
- **Notion**: API client, data schemas, and database operations
- **Google Sheets**: API client, data schemas, and database operations
- **Google Calendar**: API client, data schemas, and database operations
- **Telegram**: API client, data schemas, and database operations

### Data Layer (`src/models/` & `src/schemas/`)
- **models/**: Database models using SQLAlchemy or similar ORM
- **schemas/**: Pydantic models for API validation and serialization

### Utilities (`src/utils/`)
Shared functionality across the application:
- Configuration management
- Database operations
- Logging and monitoring

## 🔧 Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Use FastAPI-style dependency injection where possible
3. **Type Safety**: Full type hints using Python 3.9+ features
4. **Error Handling**: Consistent error handling and logging
5. **Testing**: Comprehensive test coverage with pytest
6. **Configuration**: Environment-based configuration management

## 📦 Key Dependencies

- **discord.py**: Discord API wrapper
- **pydantic**: Data validation and settings management
- **httpx**: Async HTTP client for external APIs
- **sqlalchemy**: Database ORM (optional)
- **alembic**: Database migrations (if using SQLAlchemy)
- **python-dotenv**: Environment variable management
- **loguru**: Advanced logging
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting and code quality 
