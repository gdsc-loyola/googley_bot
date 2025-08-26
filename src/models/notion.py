"""Notion integration models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TaskPriority(str, Enum):
    """Task priority levels."""
    
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class TaskStatus(str, Enum):
    """Task status options."""
    
    NOT_STARTED = "Not started"
    ON_HOLD = "On hold"
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class NotionTask(Base):
    """Notion task record for tracking created tasks."""

    __tablename__ = "notion_tasks"

    # Task identification
    notion_page_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    notion_database_id: Mapped[str] = mapped_column(String(255), nullable=False)
    notion_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    
    # Task details
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[TaskPriority] = mapped_column(String(50), default=TaskPriority.MEDIUM)
    status: Mapped[TaskStatus] = mapped_column(String(50), default=TaskStatus.NOT_STARTED)
    
    # Discord integration
    discord_user_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    discord_message_id: Mapped[Optional[str]] = mapped_column(String(20))
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Notion metadata
    notion_url: Mapped[Optional[str]] = mapped_column(String(500))
    notion_properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Sync tracking
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<NotionTask(title={self.title}, discord_user_id={self.discord_user_id}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def to_notion_properties(self) -> Dict[str, Any]:
        """Convert to Notion database properties format."""
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": self.title
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": self.status.value
                }
            },
            "Priority": {
                "select": {
                    "name": self.priority.value
                }
            },
            "Discord ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": self.discord_user_id
                        }
                    }
                ]
            }
        }
        
        if self.description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": self.description
                        }
                    }
                ]
            }
            
        if self.start_date:
            properties["Start Date"] = {
                "date": {
                    "start": self.start_date.isoformat()
                }
            }
            
        return properties


class NotionDatabase(Base):
    """Notion database configuration and metadata."""

    __tablename__ = "notion_databases"

    # Database identification
    notion_database_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    database_type: Mapped[str] = mapped_column(String(50), nullable=False)  # tasks, team, projects, resources
    
    # Database details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    notion_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_sync: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval: Mapped[int] = mapped_column(Integer, default=300)  # seconds
    
    # Properties schema
    properties_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Discord integration
    default_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    notification_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Sync tracking
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    sync_errors: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<NotionDatabase(name={self.name}, type={self.database_type}, active={self.is_active})>"

    @property
    def is_tasks_database(self) -> bool:
        """Check if this is a tasks database."""
        return self.database_type == "tasks"

    def update_sync_status(self, success: bool = True, error: Optional[str] = None, record_count: Optional[int] = None) -> None:
        """Update sync status."""
        self.last_synced = datetime.utcnow()
        
        if not success:
            self.sync_errors += 1
            self.last_error = error
        elif record_count is not None:
            self.total_records = record_count