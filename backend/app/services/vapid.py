from __future__ import annotations

import base64
import logging

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting

logger = logging.getLogger(__name__)

KEY_PUBLIC = "vapid_public"
KEY_PRIVATE = "vapid_private"
KEY_SUBJECT = "vapid_subject"
DEFAULT_SUBJECT = "mailto:wallstreet@localhost"


def generate_vapid_keys() -> tuple[str, str]:
    key = ec.generate_private_key(ec.SECP256R1())
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_raw = key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    public_b64 = base64.urlsafe_b64encode(public_raw).decode().rstrip("=")
    return private_pem, public_b64


async def _get(session: AsyncSession, key: str) -> str | None:
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    return row.value if row else None


async def _put(session: AsyncSession, key: str, value: str) -> None:
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(AppSetting(key=key, value=value))


async def ensure_vapid(session: AsyncSession, subject: str | None = None) -> dict[str, str]:
    public = await _get(session, KEY_PUBLIC)
    private = await _get(session, KEY_PRIVATE)
    sub = await _get(session, KEY_SUBJECT)
    if not public or not private:
        private, public = generate_vapid_keys()
        await _put(session, KEY_PRIVATE, private)
        await _put(session, KEY_PUBLIC, public)
        await _put(session, KEY_SUBJECT, subject or sub or DEFAULT_SUBJECT)
        logger.info("VAPID-Schlüssel erzeugt und in der Datenbank gespeichert.")
    elif subject and sub != subject:
        await _put(session, KEY_SUBJECT, subject)
    await session.commit()
    return {
        "public_key": public,
        "private_key": private,
        "subject": (await _get(session, KEY_SUBJECT)) or DEFAULT_SUBJECT,
    }


async def get_vapid_public(session: AsyncSession) -> str:
    keys = await ensure_vapid(session)
    return keys["public_key"]
