import os
import httpx
import logging
from typing import Optional, Dict, Any, Union, List

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token must be provided via argument or environment variable.")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DiscordBot-GitHubIntegration"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10)


    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        url = f"{GITHUB_API_URL}{endpoint}"
        try:
            response = await self.client.get(url, params=params)  # ✅ FIXED
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub GET error [{e.response.status_code}] on {url}: {e.response.text}")
            raise


    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{GITHUB_API_URL}{endpoint}"
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()  # ✅ FIXED
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub POST error [{e.response.status_code}] on {url}: {e.response.text}")
            raise


    async def close(self):
        await self.client.aclose()
