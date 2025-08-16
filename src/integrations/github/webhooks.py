from loguru import logger
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.github import GitHubWebhookEvent, GitHubEventType
from datetime import datetime


async def handle_github_webhook_event(event_type: str, delivery_id: str, payload: Dict[str, Any], db: AsyncSession) -> None:
    """
    Process incoming GitHub webhook events and store them in the database.
    """
    repository = payload.get("repository", {})
    sender = payload.get("sender", {})
    action = payload.get("action")
    
    event = GitHubWebhookEvent(
        github_event_id=str(payload.get("id", "")),
        delivery_id=delivery_id,
        repository_name=repository.get("name", ""),
        repository_full_name=repository.get("full_name", ""),
        event_type=GitHubEventType(event_type),
        action=action,
        sender_login=sender.get("login", ""),
        sender_id=sender.get("id", 0),
        sender_avatar=sender.get("avatar_url"),
        raw_payload=payload,
        title=extract_title(event_type, payload),
        body=extract_body(event_type, payload),
        branch=extract_branch(event_type, payload),
        commit_sha=extract_commit_sha(event_type, payload),
        pull_request_number=extract_pr_number(event_type, payload),
        issue_number=extract_issue_number(event_type, payload),
        processed=False,
        retry_count=0,
        created_at=datetime.now(),
    )

    db.add(event)
    await db.commit()
    logger.info(f"Stored GitHub event {event_type} from repo {event.repository_full_name}")


def extract_title(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type == GitHubEventType.PULL_REQUEST:
        return payload.get("pull_request", {}).get("title", "")
    if event_type == GitHubEventType.ISSUES:
        return payload.get("issue", {}).get("title", "")
    return ""


def extract_body(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type == GitHubEventType.PULL_REQUEST:
        return payload.get("pull_request", {}).get("body", "")
    if event_type == GitHubEventType.ISSUES:
        return payload.get("issue", {}).get("body", "")
    return ""


def extract_branch(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type == GitHubEventType.PUSH:
        return payload.get("ref", "").split("/")[-1]
    if event_type == GitHubEventType.PULL_REQUEST:
        return payload.get("pull_request", {}).get("head", {}).get("ref", "")
    return ""


def extract_commit_sha(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type == GitHubEventType.PUSH:
        return payload.get("after", "")
    if event_type == GitHubEventType.PULL_REQUEST:
        return payload.get("pull_request", {}).get("head", {}).get("sha", "")
    return ""


def extract_pr_number(event_type: str, payload: Dict[str, Any]) -> int:
    return payload.get("pull_request", {}).get("number") if event_type == GitHubEventType.PULL_REQUEST else None


def extract_issue_number(event_type: str, payload: Dict[str, Any]) -> int:
    return payload.get("issue", {}).get("number") if event_type == GitHubEventType.ISSUES else None
