from datetime import datetime
from typing import Optional

from sqlalchemy import select
from .database import async_session
from .models import OAuthToken


async def get_token(provider: str) -> Optional[OAuthToken]:
    async with async_session() as session:
        result = await session.execute(select(OAuthToken).where(OAuthToken.provider == provider))
        return result.scalars().first()


async def save_token(provider: str, access_token: str, refresh_token: str, scopes: str, expires_at: Optional[datetime] = None):
    async with async_session() as session:
        result = await session.execute(select(OAuthToken).where(OAuthToken.provider == provider))
        record = result.scalars().first()
        if record:
            record.access_token = access_token
            record.refresh_token = refresh_token
            record.scopes = scopes
            record.expires_at = expires_at
            await session.commit()
            return record

        token = OAuthToken(
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            scopes=scopes,
            expires_at=expires_at,
        )
        session.add(token)
        await session.commit()
        return token
