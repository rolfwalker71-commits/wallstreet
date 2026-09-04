from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth import (
    COOKIE_NAME,
    apply_session_cookie,
    confirm_totp,
    enrollment_payload,
    ensure_totp_secret,
    get_auth_state,
    session_valid,
    sign_session,
    verify_code,
)

router = APIRouter()


class VerifyIn(BaseModel):
    code: str


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/status")
async def auth_status(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    state = await get_auth_state(db)
    authed = session_valid(state.cookie_secret, request.cookies.get(COOKIE_NAME))
    if authed:
        apply_session_cookie(response, sign_session(state.cookie_secret))
    return {
        "configured": bool(state.secret and state.confirmed),
        "authenticated": authed,
    }


@router.get("/setup")
async def auth_setup(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    state = await get_auth_state(db)
    authed = session_valid(state.cookie_secret, request.cookies.get(COOKIE_NAME))
    if state.confirmed and not authed:
        raise HTTPException(401, "Bitte zuerst anmelden, dann den QR für die Familie öffnen.")
    state = await ensure_totp_secret(db)
    await db.commit()
    assert state.secret
    return enrollment_payload(state.secret)


@router.post("/verify")
async def auth_verify(
    payload: VerifyIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    state = await get_auth_state(db)
    if not state.secret:
        raise HTTPException(400, "Zuerst den Authenticator einrichten.")
    if not verify_code(state.secret, payload.code):
        raise HTTPException(401, "Code ungültig oder abgelaufen.")
    if not state.confirmed:
        await confirm_totp(db)
        await db.commit()
    apply_session_cookie(response, sign_session(state.cookie_secret))
    return {"ok": True}


@router.post("/logout")
async def auth_logout(response: Response) -> dict:
    _clear_session_cookie(response)
    return {"ok": True}
