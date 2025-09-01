import os
import httpx
import logging
from typing import Dict, Any, List
from google.oauth2 import service_account
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

GOOGLE_SHEETS_API_URL = "https://sheets.googleapis.com/v4/spreadsheets"

# Resolve service account credentials
DEFAULT_CREDENTIALS_PATH = os.path.join(
    os.path.dirname(__file__), "src", "integrations", "sheets", "google-api-credentials.json"
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "google-api-credentials.json")

class GoogleSheetsClient:
    def __init__(self):
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"Google API credentials file not found at {SERVICE_ACCOUNT_FILE}. "
                "Set GOOGLE_SHEETS_CREDENTIALS env var if it's stored elsewhere."
            )
        self.credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        self.token = self._get_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10)

    def _get_access_token(self) -> str:
        creds = self.credentials
        if creds.expired or not creds.valid:
            creds.refresh(Request())
        return creds.token

    async def get(self, spreadsheet_id: str, range_: str) -> Dict[str, Any]:
        url = f"{GOOGLE_SHEETS_API_URL}/{spreadsheet_id}/values/{range_}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Sheets GET error [{e.response.status_code}] {url} :: {e.response.text}")
            raise

    async def post(self, spreadsheet_id: str, range_: str, values: List[List[Any]]) -> Dict[str, Any]:
        url = f"{GOOGLE_SHEETS_API_URL}/{spreadsheet_id}/values/{range_}?valueInputOption=RAW"
        body = {"values": values}
        try:
            response = await self.client.put(url, json=body)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Sheets POST error [{e.response.status_code}] {url} :: {e.response.text}")
            raise

    async def close(self):
        await self.client.aclose()
