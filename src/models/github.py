"""GitHub integration models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GitHubEventType(str, Enum):
    """GitHub webhook event types."""
    
    PUSH = "push"
    PULL_REQUEST = "pull_request" 
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    RELEASE = "release"
    CREATE = "create"  # Branch/tag creation
    DELETE = "delete"  # Branch/tag deletion
    FORK = "fork"
    STAR = "star"
    WATCH = "watch"


class GitHubRepository(Base):
    """GitHub repository configuration."""

    __tablename__ = "github_repositories"

    # Repository information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # owner/repo
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Repository details
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    
    # Discord integration
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    notification_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Webhook configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_id: Mapped[Optional[int]] = mapped_column(Integer)  # GitHub webhook ID
    
    # Tracking settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    track_pushes: Mapped[bool] = mapped_column(Boolean, default=True)
    track_pull_requests: Mapped[bool] = mapped_column(Boolean, default=True)
    track_issues: Mapped[bool] = mapped_column(Boolean, default=True)
    track_releases: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Filter settings
    ignored_branches: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of branch names
    ignored_users: Mapped[Optional[str]] = mapped_column(Text)    # JSON array of usernames
    
    # Statistics
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    total_pull_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_issues: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<GitHubRepository(full_name={self.full_name}, channel_id={self.discord_channel_id})>"

    @property
    def github_url(self) -> str:
        """Get GitHub repository URL."""
        return f"https://github.com/{self.full_name}"


class GitHubWebhookEvent(Base):
    """GitHub webhook event log."""

    __tablename__ = "github_webhook_events"

    # Event identification
    github_event_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    delivery_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # Repository information
    repository_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repository_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Event details
    event_type: Mapped[GitHubEventType] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[Optional[str]] = mapped_column(String(50))  # opened, closed, synchronize, etc.
    
    # User information
    sender_login: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sender_avatar: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Content references
    branch: Mapped[Optional[str]] = mapped_column(String(255))
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40))
    pull_request_number: Mapped[Optional[int]] = mapped_column(Integer)
    issue_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Event content
    title: Mapped[Optional[str]] = mapped_column(String(500))
    body: Mapped[Optional[str]] = mapped_column(Text)
    
    # Raw webhook data
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    discord_message_id: Mapped[Optional[str]] = mapped_column(String(20))
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<GitHubWebhookEvent(delivery_id={self.delivery_id}, type={self.event_type}, repo={self.repository_name})>"

    @property
    def github_url(self) -> Optional[str]:
        """Get GitHub URL for this event."""
        base_url = f"https://github.com/{self.repository_full_name}"
        
        if self.pull_request_number:
            return f"{base_url}/pull/{self.pull_request_number}"
        elif self.issue_number:
            return f"{base_url}/issues/{self.issue_number}"
        elif self.commit_sha:
            return f"{base_url}/commit/{self.commit_sha}"
        elif self.branch:
            return f"{base_url}/tree/{self.branch}"
        
        return base_url

    def mark_processed(self, discord_message_id: Optional[str] = None, discord_channel_id: Optional[str] = None) -> None:
        """Mark event as processed."""
        self.processed = True
        self.processed_at = datetime.now()
        if discord_message_id:
            self.discord_message_id = discord_message_id
        if discord_channel_id:
            self.discord_channel_id = discord_channel_id

    def mark_error(self, error_message: str) -> None:
        """Mark event as having an error."""
        self.error_message = error_message
        self.retry_count += 1 