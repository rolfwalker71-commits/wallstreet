from __future__ import annotations

import hashlib
import hmac
import io
import secrets
import time
from dataclasses import dataclass

import pyotp
import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting

TOTP_SECRET_KEY = "totp_secret"
TOTP_CONFIRMED_KEY = "totp_confirmed"
COOKIE_SECRET_KEY = "auth_cookie_secret"
COOKIE_NAME = "wallstreet_session"
# Browser deckeln Cookies (Chrome ~400 Tage). Server-Token läuft nicht ab;
# jedes API-Request erneuert das Cookie, solange das Gerät benutzt wird.
COOKIE_MAX_AGE = 400 * 86400
ISSUER = "Wallstreet"
ACCOUNT = "Familie"

_verify_hits: dict[str, list[float]] = {}


@dataclass
class AuthState:
    secret: str | None
    confirmed: bool
    cookie_secret: str


def new_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=ACCOUNT, issuer_name=ISSUER)


def qr_svg(data: str) -> str:
    img = qrcode.make(data, image_factory=SvgPathImage, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()


def verify_code(secret: str, code: str) -> bool:
    digits = "".join(ch for ch in (code or "") if ch.isdigit())
    if len(digits) != 6:
        return False
    return bool(pyotp.TOTP(secret).verify(digits, valid_window=1))


def sign_session(cookie_secret: str) -> str:
    body = "v1.perm"
    sig = hmac.new(cookie_secret.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def session_valid(cookie_secret: str, token: str | None) -> bool:
    if not token or not cookie_secret:
        return False
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return False
    body = f"{parts[0]}.{parts[1]}"
    expect = hmac.new(cookie_secret.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expect, parts[2]):
        return False
    if parts[1] == "perm":
        return True
    try:
        return int(parts[1]) > int(time.time())
    except ValueError:
        return False


def apply_session_cookie(response, token: str) -> None:
    from app.config import get_settings

    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.app_env != "development",
        path="/",
    )


def allow_verify_attempt(ip: str, *, limit: int = 8, window_s: int = 600) -> bool:
    now = time.time()
    hits = [t for t in _verify_hits.get(ip, []) if now - t < window_s]
    if len(hits) >= limit:
        _verify_hits[ip] = hits
        return False
    hits.append(now)
    _verify_hits[ip] = hits
    return True


async def _get(session: AsyncSession, key: str) -> str | None:
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    return row.value if row else None


async def _set(session: AsyncSession, key: str, value: str) -> None:
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(AppSetting(key=key, value=value))
    await session.flush()


async def get_auth_state(session: AsyncSession) -> AuthState:
    cookie = await _get(session, COOKIE_SECRET_KEY)
    if not cookie:
        cookie = secrets.token_hex(32)
        await _set(session, COOKIE_SECRET_KEY, cookie)
    confirmed = (await _get(session, TOTP_CONFIRMED_KEY) or "").lower() == "true"
    return AuthState(
        secret=await _get(session, TOTP_SECRET_KEY),
        confirmed=confirmed,
        cookie_secret=cookie,
    )


async def ensure_totp_secret(session: AsyncSession) -> AuthState:
    state = await get_auth_state(session)
    if state.secret:
        return state
    secret = new_totp_secret()
    await _set(session, TOTP_SECRET_KEY, secret)
    await _set(session, TOTP_CONFIRMED_KEY, "false")
    return await get_auth_state(session)


async def confirm_totp(session: AsyncSession) -> None:
    await _set(session, TOTP_CONFIRMED_KEY, "true")


def enrollment_payload(secret: str) -> dict:
    uri = provisioning_uri(secret)
    return {
        "otpauth": uri,
        "qr_svg": qr_svg(uri),
        "secret": secret,
        "issuer": ISSUER,
        "account": ACCOUNT,
    }
