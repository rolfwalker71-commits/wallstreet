from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset
from app.models.settings import AppSetting
from app.services.prefs import get_prefs, set_pref


KIND_LABEL = {
    "earnings": "Ergebnisse",
    "ex_dividend": "Ex-Dividende",
}


def parse_event_date(raw: Any) -> date | None:
    if raw is None or raw == "":
        return None
    text = str(raw)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def event_in_window(event: date, *, today: date, days: int = 14) -> bool:
    return today <= event <= today + timedelta(days=days)


def should_calendar_push(event: date, *, today: date) -> bool:
    return event in {today, today + timedelta(days=1)}


def events_from_extra(symbol: str, name: str, extra: dict | None) -> list[dict[str, Any]]:
    extra = extra if isinstance(extra, dict) else {}
    out: list[dict[str, Any]] = []
    for kind in ("earnings", "ex_dividend"):
        key = "earnings_date" if kind == "earnings" else "ex_dividend_date"
        parsed = parse_event_date(extra.get(key))
        if parsed is None:
            continue
        out.append(
            {
                "symbol": symbol,
                "name": name,
                "kind": kind,
                "label": KIND_LABEL[kind],
                "date": parsed.isoformat(),
                "source": "gespeichert",
            }
        )
    return out


async def upcoming_events(session: AsyncSession, *, days: int = 14) -> list[dict[str, Any]]:
    assets = (
        await session.execute(select(Asset).where(Asset.watched.is_(True)).order_by(Asset.symbol))
    ).scalars().all()
    today = datetime.now(UTC).date()
    events: list[dict[str, Any]] = []
    for asset in assets:
        for ev in events_from_extra(asset.symbol, asset.name, asset.extra):
            parsed = parse_event_date(ev["date"])
            if parsed and event_in_window(parsed, today=today, days=days):
                events.append(ev)
    events.sort(key=lambda e: (e["date"], e["symbol"], e["kind"]))
    return events


async def notify_calendar(session: AsyncSession) -> int:
    from app.services.push import broadcast

    prefs = await get_prefs(session)
    if not prefs.calendar_push:
        return 0
    today = datetime.now(UTC).date()
    sent_key = "calendar_pushed_dates"
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == sent_key))
    ).scalar_one_or_none()
    already = set((row.value if row else "").split(",")) - {""}
    events = await upcoming_events(session, days=1)
    sent = 0
    for ev in events:
        parsed = parse_event_date(ev["date"])
        if parsed is None or not should_calendar_push(parsed, today=today):
            continue
        stamp = f"{ev['symbol']}:{ev['kind']}:{ev['date']}"
        if stamp in already:
            continue
        when = "heute" if parsed == today else "morgen"
        try:
            await broadcast(
                session,
                {
                    "title": f"{ev['label']} {when}: {ev['symbol']}",
                    "body": f"{ev['name']} — {ev['label']} am {ev['date']}.",
                    "url": f"/watchlist/{ev['symbol']}",
                    "tag": f"cal-{stamp}",
                },
            )
        except Exception:
            continue
        already.add(stamp)
        sent += 1
    if sent:
        await set_pref(session, sent_key, ",".join(sorted(already)[-80:]))
    return sent
