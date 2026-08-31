from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recommendation
from app.models.enums import RecommendationAction
from app.models.settings import AppSetting, PushSubscription
from app.services.prefs import get_prefs
from app.services.vapid import ensure_vapid, load_vapid_private

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


def should_notify(
    rec: Recommendation,
    previous: Recommendation | None,
    *,
    min_confidence: float = 0.0,
) -> bool:
    if rec.action not in {RecommendationAction.BUY, RecommendationAction.SELL}:
        return False
    try:
        conf = float(rec.confidence)
    except (TypeError, ValueError):
        conf = 0.0
    if conf < min_confidence:
        return False
    if previous is None:
        return True
    return previous.action != rec.action


DIGEST_KEY = "push_digest_queue"


def _digest_line(rec: Recommendation) -> str:
    action = "Kauf" if rec.action.value == "buy" else "Verkauf"
    return f"{action} {rec.asset.symbol}"


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
            vapid_private_key=load_vapid_private(keys["private_key"]),
            vapid_claims={"sub": keys["subject"]},
            ttl=86_400,
        )
        return True
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            return False
        raise PushError(str(exc)) from exc
    except Exception as exc:
        raise PushError(str(exc)) from exc


async def broadcast(session: AsyncSession, payload: dict) -> int:
    import asyncio

    keys = await ensure_vapid(session)
    try:
        load_vapid_private(keys["private_key"])
    except Exception as exc:
        raise PushError(f"VAPID-Schlüssel ungültig: {exc}") from exc
    subs = await list_subscriptions(session)
    sent = 0
    stale: list[PushSubscription] = []
    errors: list[str] = []
    for sub in subs:
        try:
            ok = await asyncio.to_thread(_send_one, sub, keys, payload)
        except PushError as exc:
            errors.append(str(exc))
            logger.warning("Push fehlgeschlagen: %s", exc)
            continue
        if ok:
            sent += 1
        else:
            stale.append(sub)
    for sub in stale:
        await session.delete(sub)
    if stale:
        await session.flush()
    if sent == 0 and errors:
        raise PushError(errors[0])
    return sent


async def _queue_digest(session: AsyncSession, recs: list[Recommendation]) -> int:
    from sqlalchemy import select

    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == DIGEST_KEY))
    ).scalar_one_or_none()
    existing = []
    if row and row.value:
        try:
            import json

            existing = json.loads(row.value)
        except Exception:
            existing = []
    if not isinstance(existing, list):
        existing = []
    seen = {item.get("id") for item in existing if isinstance(item, dict)}
    for rec in recs:
        rid = str(rec.id)
        if rid in seen:
            continue
        existing.append(
            {
                "id": rid,
                "line": _digest_line(rec),
                "url": f"/signals/{rec.id}",
            }
        )
        seen.add(rid)
    payload = __import__("json").dumps(existing, ensure_ascii=False)
    if row:
        row.value = payload
    else:
        session.add(AppSetting(key=DIGEST_KEY, value=payload))
    await session.flush()
    return len(recs)


async def flush_digest(session: AsyncSession) -> int:
    import json

    from sqlalchemy import select

    if await subscription_count(session) == 0:
        return 0
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == DIGEST_KEY))
    ).scalar_one_or_none()
    items = []
    if row and row.value:
        try:
            items = json.loads(row.value)
        except Exception:
            items = []
    if not items:
        return 0
    lines = [str(i.get("line")) for i in items if isinstance(i, dict) and i.get("line")]
    body = ", ".join(lines[:6])
    if len(lines) > 6:
        body += f" · +{len(lines) - 6} weitere"
    sent = await broadcast(
        session,
        {
            "title": f"Tagesdigest: {len(lines)} Signale",
            "body": body or "Neue Kauf- und Verkaufssignale.",
            "url": "/",
            "tag": "digest",
        },
    )
    if row:
        row.value = "[]"
        await session.flush()
    return sent


async def notify_new_signals(session: AsyncSession, recs: list[Recommendation]) -> int:
    if not recs:
        return 0
    if await subscription_count(session) == 0:
        return 0
    prefs = await get_prefs(session)
    eligible: list[Recommendation] = []
    for rec in recs:
        prev = await previous_recommendation(session, rec.asset_id, rec.id)
        if not should_notify(rec, prev, min_confidence=prefs.push_min_confidence):
            continue
        eligible.append(rec)
    if not eligible:
        return 0
    if prefs.push_digest:
        return await _queue_digest(session, eligible)
    sent = 0
    for rec in eligible:
        sent += await broadcast(session, _payload(rec))
    return sent
