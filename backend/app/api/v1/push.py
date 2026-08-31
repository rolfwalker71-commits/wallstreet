from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.push import (
    PushError,
    broadcast,
    delete_subscription,
    subscription_count,
    upsert_subscription,
)
from app.services.vapid import get_vapid_public

router = APIRouter()


class PushKeysIn(BaseModel):
    p256dh: str
    auth: str


class SubscribeIn(BaseModel):
    endpoint: str
    keys: PushKeysIn


class VapidOut(BaseModel):
    public_key: str
    ready: bool = True


class PushStatusOut(BaseModel):
    public_key: str
    devices: int
    ready: bool = True


@router.get("/vapid", response_model=VapidOut)
async def vapid_public(db: AsyncSession = Depends(get_db)) -> VapidOut:
    return VapidOut(public_key=await get_vapid_public(db))


@router.get("/status", response_model=PushStatusOut)
async def push_status(db: AsyncSession = Depends(get_db)) -> PushStatusOut:
    return PushStatusOut(
        public_key=await get_vapid_public(db),
        devices=await subscription_count(db),
    )


@router.post("/subscribe")
async def subscribe(
    payload: SubscribeIn,
    db: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
) -> dict:
    try:
        row = await upsert_subscription(
            db,
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            user_agent=user_agent,
        )
    except PushError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    return {"ok": True, "id": str(row.id)}


@router.delete("/subscribe")
async def unsubscribe(payload: SubscribeIn, db: AsyncSession = Depends(get_db)) -> dict:
    removed = await delete_subscription(db, payload.endpoint)
    await db.commit()
    return {"ok": True, "removed": removed}


@router.post("/test")
async def test_push(db: AsyncSession = Depends(get_db)) -> dict:
    sent = await broadcast(
        db,
        {
            "title": "Wallstreet bereit",
            "body": "Benachrichtigungen sind aktiv. Kauf- und Verkaufssignale kommen automatisch.",
            "url": "/",
            "tag": "push-test",
        },
    )
    await db.commit()
    if sent == 0:
        raise HTTPException(400, "Kein Gerät abonniert. Zuerst aktivieren.")
    return {"ok": True, "sent": sent}
