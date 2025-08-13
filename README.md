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
