# 🤖 Googley

**Googley** is a multipurpose automation bot built to simplify developer workflows, enhance team collaboration, and bridge communication across platforms. Built with **Discord**, **FastAPI**, **Python**, and **Telegram**, Googley connects your favorite tools like GitHub, Notion, and Google Calendar—so your team stays informed, focused, and in sync.

---

## 🚀 Features

### 🔔 GitHub Activity Alerts
Googley monitors your GitHub repositories and sends real-time alerts to designated Discord or Telegram channels. Never miss a pull request, issue, or commit again.

### 🛠️ Discord Server Management
From role assignments to channel moderation, Googley can help manage your Discord server with custom commands and automation tools tailored for admins.

### ♻️ Automated Repetitive Tasks
Whether it's sending daily stand-up reminders, syncing calendar events, or rotating tasks, Googley handles the boring stuff so your team can focus on what matters.

### 🧠 Notion Integration
Improve team transparency by syncing updates and logs directly to your Notion workspace. Track tasks, updates, and project changes in one central hub.

### 📅 Google Calendar Sync
Integrate and manage team events effortlessly. Googley syncs events to your Discord or Telegram channels and reminds team members about upcoming deadlines and meetings.

### 📊 Google Sheets Integration
Seamlessly read, write, and update data in Google Sheets from Discord or Telegram commands. Perfect for managing spreadsheets, logging data, or collaborating on shared documents.

### 🧩 Streamlined Project Management
Simplify planning and coordination by linking GitHub issues, Notion tasks, and calendar events—right from Discord or Telegram.

---

## 🛠 Tech Stack

- **Python 3.11+**
- **FastAPI** – for webhook handling and API integrations
- **Discord.py / nextcord / py-cord** – for Discord bot features
- **aiogram / python-telegram-bot** – for Telegram integration
- **Notion SDK** – to connect with Notion databases
- **Google Calendar API** – for event synchronization
- **Google Sheets API** – for spreadsheet integration
- **SQLAlchemy / PostgreSQL** – (optional) for storing persistent data

---

## 📦 Installation

> **Requirements:**
> - Python 3.11+
> - GitHub access tokens
> - Discord bot token
> - Telegram bot token
> - Notion integration token
> - Google Calendar credentials

```bash
# Clone the repository
git clone https://github.com/gdsc-loyola/googley_bot.git
cd googley_bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```env
# Discord Configuration
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here

# GitHub Integration
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_ORG=hirayainteractive

# Notion Integration
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_TASKS=your_tasks_database_id

# Database
DATABASE_URL=sqlite:///./googley_bot.db
```

### Run the Bot

```bash
# Initialize database
alembic upgrade head

# Start the bot
python src/main.py
```

---

## 📁 Project Structure

```
googley_bot/
├── src/
│   ├── bot/                    # Core bot setup and event handlers
│   ├── commands/               # Discord slash commands
│   ├── integrations/           # External API integrations (GitHub, Notion, Google Sheets)
│   ├── utils/                  # Shared utilities and helpers
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas for data validation
│   └── main.py                 # Application entry point
├── tests/                      # Comprehensive test suite
├── alembic/                    # Database migrations
├── .docs/                      # Detailed documentation
│   ├── setup.md                # Setup and installation guide
│   ├── features.md             # Comprehensive feature documentation
│   ├── tasks.md                # Development roadmap and tasks
│   └── project_structure.md    # Detailed architecture overview
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
└── README.md                   # This file
```

---

## 🧩 Architecture

IRA Bot follows a modular architecture designed for scalability, maintainability, and extensibility:

### **Layered Design**
- **Bot Layer**: Discord.py client setup and event handling
- **Command Layer**: Slash command implementations with proper error handling
- **Integration Layer**: External API clients and data synchronization
- **Data Layer**: Database models and data access patterns
- **Utility Layer**: Shared functionality and helper modules

### **Key Principles**
- **Type Safety**: Full type hints throughout the codebase
- **Async/Await**: Non-blocking operations for optimal performance
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Dependency Injection**: Clean dependency management using FastAPI patterns
- **Testing**: Extensive test coverage with pytest

---

## 🧪 Development

### Tech Stack
- **[discord.py](https://discordpy.readthedocs.io/)**: Discord API wrapper
- **[FastAPI](https://fastapi.tiangolo.com/)**: Webhook server for external integrations
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: Database ORM
- **[Alembic](https://alembic.sqlalchemy.org/)**: Database migrations
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Data validation and settings
- **[pytest](https://pytest.org/)**: Testing framework
- **[Loguru](https://loguru.readthedocs.io/)**: Advanced logging

---

## 🗺️ Roadmap

### Phase 1: Core Functionality (Weeks 1-6)
- [ ] Discord bot setup and basic commands
- [ ] GitHub integration with webhook support
- [ ] Google Sheets integration with synchronization 

### Phase 2: Productivity Features (Weeks 7-12)
- [ ] Telegram bot setup with basic commands
- [ ] Notion integration and task synchronization
- [ ] Google Calendar integration with synchronization

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Support & Community

### Getting Help
- **Documentation**: Comprehensive guides in the `.docs/` folder
- **Discord**: Join our community server for support and discussions
- **Email**: Contact gdscloyola@gmail.com for enterprise support

### Community Guidelines
- Be respectful and inclusive in all interactions
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- Contribute constructively to discussions and development
- Help others learn and grow within the community

---

## 🙏 Acknowledgments

- **Google Developers Guild on Campus - Loyola**: For vision, feedback, and continuous support
- **Discord.py Community**: For excellent documentation and community support
- **Open Source Contributors**: For the amazing tools and libraries that make this possible
- **Beta Testers**: For early feedback and bug reports
