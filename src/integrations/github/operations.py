import logging
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.integrations.github.client import GitHubClient
from src.utils.database import get_db_session
from src.models.github import GitHubRepository

logger = logging.getLogger(__name__)
client = GitHubClient()

async def list_pull_requests(repo: str) -> List[Dict]:
    """Fetch open pull requests for a given repo (org/repo)."""
    org, repo_name = repo.split("/")
    response = await client.get(f"/repos/{org}/{repo_name}/pulls")
    data = response.json()
    return [
        {
            "title": pr["title"],
            "number": pr["number"],
            "url": pr["html_url"],
            "user": pr["user"]["login"]
        }
        for pr in data
    ]


async def list_issues(repo: str) -> List[Dict]:
    """Fetch open issues (excluding PRs) for a given repo (org/repo)."""
    org, repo_name = repo.split("/")
    response = await client.get(f"/repos/{org}/{repo_name}/issues")
    data = response.json()
    return [
        {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "user": issue["user"]["login"]
        }
        for issue in data if "pull_request" not in issue
    ]


async def list_tracked_repositories() -> List[str]:
    """List all active GitHub repositories being tracked."""
    async_session = get_db_session()
    async with async_session() as db:
        result = await db.execute(
            select(GitHubRepository.full_name).where(GitHubRepository.is_active == True)
        )
        return [row[0] for row in result.all()]


async def subscribe_channel(repo: str, channel_id: int) -> None:
    """
    Subscribe a channel to GitHub events by assigning its ID
    to the `notification_channel_id` field.
    """
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(GitHubRepository).filter_by(full_name=repo)
            )
            repository = result.scalar_one()
            repository.notification_channel_id = str(channel_id)
            repository.is_active = True
            await db.commit()
            logger.info(f"Channel {channel_id} subscribed to {repo}")
        except NoResultFound:
            logger.warning(f"Tried to subscribe to unknown repo: {repo}")
            raise ValueError(f"Repository `{repo}` is not registered in the database.")


async def unsubscribe_channel(repo: str, channel_id: int) -> None:
    """
    Unsubscribe a channel from GitHub events by clearing the
    `notification_channel_id` field.
    """
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(GitHubRepository).filter_by(full_name=repo)
            )
            repository = result.scalar_one()
            if repository.notification_channel_id == str(channel_id):
                repository.notification_channel_id = None
                await db.commit()
                logger.info(f"Channel {channel_id} unsubscribed from {repo}")
            else:
                logger.warning(f"Channel {channel_id} tried to unsubscribe from repo it isn't linked to.")
        except NoResultFound:
            logger.warning(f"Tried to unsubscribe from unknown repo: {repo}")
            raise ValueError(f"Repository `{repo}` is not registered in the database.")
