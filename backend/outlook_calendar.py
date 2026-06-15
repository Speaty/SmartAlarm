from azure.identity import DeviceCodeCredential
from .config import OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_SCOPES
from .calendar_sync import get_weekly_outlook_events
from .token_store import save_token, get_token


class OutlookCalendarService:
    def __init__(self):
        self.scopes = OUTLOOK_SCOPES

    def build_device_flow(self):
        credential = DeviceCodeCredential(client_id=OUTLOOK_CLIENT_ID)
        return credential

    async def store_token(self, access_token: str, refresh_token: str, scopes: str, expires_at):
        await save_token(
            provider="outlook",
            access_token=access_token,
            refresh_token=refresh_token,
            scopes=scopes,
            expires_at=expires_at,
        )

    async def get_weekly_events(self):
        token = await get_token("outlook")
        if not token:
            return []
        return await get_weekly_outlook_events(token.access_token)
