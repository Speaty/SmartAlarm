from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from .config import GOOGLE_CLIENT_SECRETS, GOOGLE_SCOPES
from .database import async_session
from .models import OAuthToken

router = APIRouter()


@router.get("/auth/google")
async def google_auth(request: Request):
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRETS),
        scopes=GOOGLE_SCOPES,
        redirect_uri=str(request.url_for("google_auth_callback")),
    )
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
async def google_auth_callback(request: Request):
    state = request.query_params.get("state")
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRETS),
        scopes=GOOGLE_SCOPES,
        state=state,
        redirect_uri=str(request.url_for("google_auth_callback")),
    )
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    async with async_session() as session:
        token = OAuthToken(
            provider="google",
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scopes=",".join(GOOGLE_SCOPES),
        )
        session.add(token)
        await session.commit()

    return {"status": "ok", "message": "Google Calendar connected."}
