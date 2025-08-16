"""Pydantic schemas for GitHub integration."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GitHubEventType(str, Enum):
    push = "push"
    pull_request = "pull_request"
    issues = "issues"
    issue_comment = "issue_comment"
    pull_request_review = "pull_request_review"
    pull_request_review_comment = "pull_request_review_comment"
    release = "release"
    create = "create"
    delete = "delete"
    fork = "fork"
    star = "star"
    watch = "watch"


class GitHubRepositorySchema(BaseModel):
    id: int
    name: str
    full_name: str
    owner: str
    description: Optional[str] = None
    is_private: bool
    default_branch: str
    discord_channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_id: Optional[int] = None
    is_active: bool = True
    track_pushes: bool = True
    track_pull_requests: bool = True
    track_issues: bool = True
    track_releases: bool = True
    ignored_branches: Optional[str] = None
    ignored_users: Optional[str] = None
    total_commits: int = 0
    total_pull_requests: int = 0
    total_issues: int = 0
    last_activity: Optional[datetime] = None

    class Config:
        orm_mode = True


class GitHubWebhookEventSchema(BaseModel):
    id: int
    github_event_id: Optional[str] = None
    delivery_id: str
    repository_name: str
    repository_full_name: str
    event_type: GitHubEventType
    action: Optional[str] = None
    sender_login: str
    sender_id: int
    sender_avatar: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pull_request_number: Optional[int] = None
    issue_number: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    raw_payload: Dict[str, Any]
    processed: bool = False
    processed_at: Optional[datetime] = None
    discord_message_id: Optional[str] = None
    discord_channel_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    class Config:
        orm_mode = True
