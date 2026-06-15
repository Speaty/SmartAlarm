import json
from pathlib import Path
from typing import Any, Tuple

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from .config import GOOGLE_CLIENT_SECRETS, GOOGLE_SCOPES
from .token_store import save_token, get_token
from .calendar_sync import get_weekly_google_events


class GoogleCalendarService:
    def __init__(self):
        self.client_secrets_file = Path(GOOGLE_CLIENT_SECRETS)

    def _load_client_secrets(self) -> Tuple[str, dict[str, Any]]:
        if not self.client_secrets_file.exists():
            raise FileNotFoundError(
                f"Google client secrets not found at {self.client_secrets_file}"
            )
        with self.client_secrets_file.open("r", encoding="utf-8") as handler:
            secret_data = json.load(handler)
        if "installed" in secret_data:
            return "installed", secret_data["installed"]
        if "web" in secret_data:
            return "web", secret_data["web"]
        raise ValueError("Expected 'installed' or 'web' config in Google client secrets")

    def build_flow(self, request_url: str, state: str | None = None) -> Flow:
        root_key, config = self._load_client_secrets()
        flow = Flow.from_client_config(
            {root_key: config},
            scopes=GOOGLE_SCOPES,
            redirect_uri=request_url,
        )
        if state:
            flow.state = state
        return flow

    def build_authorization_url(self, request_url: str):
        flow = self.build_flow(request_url)
        auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
        return auth_url, state

    async def store_credentials(self, credentials: Credentials):
        await save_token(
            provider="google",
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scopes=",".join(GOOGLE_SCOPES),
            expires_at=credentials.expiry,
        )

    async def get_weekly_events(self):
        token = await get_token("google")
        if not token:
            return []
        _, client_config = self._load_client_secrets()
        creds = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_config.get("client_id"),
            client_secret=client_config.get("client_secret"),
            scopes=token.scopes.split(",") if token.scopes else GOOGLE_SCOPES,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            await self.store_credentials(creds)
        events = await get_weekly_google_events(creds)
        return events
