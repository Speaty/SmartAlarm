from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from .google_calendar import GoogleCalendarService
from .token_store import save_token
from .config import GOOGLE_SCOPES

router = APIRouter()


google_service = GoogleCalendarService()


@router.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = str(request.url_for("auth_google_callback"))
    auth_url, state = google_service.build_authorization_url(redirect_uri)
    request.session["state"] = state
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    state = request.query_params.get("state")
    redirect_uri = str(request.url_for("auth_google_callback"))
    flow = google_service.build_flow(redirect_uri, state)
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    await google_service.store_credentials(credentials)
    return {"status": "ok", "message": "Google Calendar connected."}
