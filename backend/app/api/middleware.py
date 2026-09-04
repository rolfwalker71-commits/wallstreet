from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.db.session import async_session_factory
from app.services.auth import (
    COOKIE_NAME,
    allow_verify_attempt,
    apply_session_cookie,
    get_auth_state,
    session_valid,
    sign_session,
)

ALWAYS_PUBLIC = {
    "/api/health",
    "/api/auth/status",
    "/api/auth/verify",
}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class TotpGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api"):
            return await call_next(request)
        if path in ALWAYS_PUBLIC:
            if path == "/api/auth/verify" and not allow_verify_attempt(_client_ip(request)):
                return JSONResponse({"detail": "Zu viele Versuche. Kurz warten."}, status_code=429)
            return await call_next(request)

        async with async_session_factory() as session:
            state = await get_auth_state(session)
            await session.commit()

        if not state.confirmed:
            if path.startswith("/api/auth/"):
                return await call_next(request)
            return JSONResponse({"detail": "Authenticator einrichten."}, status_code=401)

        if session_valid(state.cookie_secret, request.cookies.get(COOKIE_NAME)):
            response = await call_next(request)
            apply_session_cookie(response, sign_session(state.cookie_secret))
            return response
        return JSONResponse({"detail": "Bitte mit Authenticator-Code anmelden."}, status_code=401)
