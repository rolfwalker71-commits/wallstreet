from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recommendation
from app.models.enums import RecommendationAction
from app.models.settings import PushSubscription
from app.services.vapid import ensure_vapid

logger = logging.getLogger(__name__)


class PushError(ValueError):
    pass


async def list_subscriptions(session: AsyncSession) -> list[PushSubscription]:
    return list((await session.execute(select(PushSubscription))).scalars().all())


async def subscription_count(session: AsyncSession) -> int:
    return int(
        (await session.execute(select(func.count()).select_from(PushSubscription))).scalar_one()
    )


async def upsert_subscription(
    session: AsyncSession,
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None = None,
) -> PushSubscription:
    if not endpoint or not p256dh or not auth:
        raise PushError("Unvollständiges Push-Abo.")
    row = (
        await session.execute(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    ).scalar_one_or_none()
    if row:
        row.p256dh = p256dh
        row.auth = auth
        if user_agent:
            row.user_agent = user_agent
    else:
        row = PushSubscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
        )
        session.add(row)
    await session.flush()
    return row


async def delete_subscription(session: AsyncSession, endpoint: str) -> bool:
    row = (
        await session.execute(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    ).scalar_one_or_none()
    if not row:
        return False
    await session.delete(row)
    await session.flush()
    return True


def should_notify(rec: Recommendation, previous: Recommendation | None) -> bool:
    if rec.action not in {RecommendationAction.BUY, RecommendationAction.SELL}:
        return False
    if previous is None:
        return True
    return previous.action != rec.action


async def previous_recommendation(
    session: AsyncSession,
    asset_id: UUID,
    current_id: UUID,
) -> Recommendation | None:
    return (
        await session.execute(
            select(Recommendation)
            .where(Recommendation.asset_id == asset_id, Recommendation.id != current_id)
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


def _payload(rec: Recommendation) -> dict:
    action = "Kauf" if rec.action.value == "buy" else "Verkauf"
    kind = "Idee" if not rec.asset.watched else "Signal"
    body = (rec.rationale or rec.news_summary or "").replace("\n", " ").strip()
    if len(body) > 180:
        body = body[:177] + "…"
    return {
        "title": f"{kind}: {action} {rec.asset.symbol}",
        "body": body or f"{action} empfohlen.",
        "url": f"/signals/{rec.id}",
        "tag": f"rec-{rec.asset.symbol}",
    }


def _send_one(sub: PushSubscription, keys: dict[str, str], payload: dict) -> bool:
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=keys["private_key"],
            vapid_claims={"sub": keys["subject"]},
        )
        return True
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            return False
        logger.warning("Push fehlgeschlagen: %s", exc)
        return True
    except Exception:
        logger.exception("Push unerwartet fehlgeschlagen")
        return True


async def broadcast(session: AsyncSession, payload: dict) -> int:
    import asyncio

    keys = await ensure_vapid(session)
    subs = await list_subscriptions(session)
    sent = 0
    stale: list[PushSubscription] = []
    for sub in subs:
        ok = await asyncio.to_thread(_send_one, sub, keys, payload)
        if ok:
            sent += 1
        else:
            stale.append(sub)
    for sub in stale:
        await session.delete(sub)
    if stale:
        await session.flush()
    return sent


async def notify_new_signals(session: AsyncSession, recs: list[Recommendation]) -> int:
    if not recs:
        return 0
    if await subscription_count(session) == 0:
        return 0
    sent = 0
    for rec in recs:
        prev = await previous_recommendation(session, rec.asset_id, rec.id)
        if not should_notify(rec, prev):
            continue
        sent += await broadcast(session, _payload(rec))
    return sent
