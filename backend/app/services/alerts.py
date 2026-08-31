from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Asset, PriceAlert
from app.models.enums import AlertKind


class AlertError(ValueError):
    pass


def alert_triggered(
    kind: AlertKind | str,
    threshold: float,
    *,
    price: float | None,
    change_pct: float | None,
) -> bool:
    raw = kind.value if isinstance(kind, AlertKind) else str(kind)
    if raw == AlertKind.BELOW.value:
        return price is not None and price <= threshold
    if raw == AlertKind.ABOVE.value:
        return price is not None and price >= threshold
    if raw == AlertKind.PCT_TODAY.value:
        return change_pct is not None and abs(change_pct) >= threshold
    return False


def _payload(alert: PriceAlert, price: float | None, change_pct: float | None) -> dict:
    symbol = alert.asset.symbol if alert.asset else "?"
    if alert.kind == AlertKind.BELOW:
        title = f"Alarm: {symbol} unter {alert.threshold}"
        body = f"Kurs {price} — unter der Schwelle {alert.threshold}."
    elif alert.kind == AlertKind.ABOVE:
        title = f"Alarm: {symbol} über {alert.threshold}"
        body = f"Kurs {price} — über der Schwelle {alert.threshold}."
    else:
        title = f"Alarm: {symbol} ±{alert.threshold} % heute"
        body = f"Tagesänderung {change_pct:.2f} %." if change_pct is not None else "Tagesänderung erreicht."
    return {
        "title": title,
        "body": body,
        "url": f"/watchlist/{symbol}",
        "tag": f"alert-{alert.id}",
    }


async def list_alerts(session: AsyncSession, symbol: str | None = None) -> list[PriceAlert]:
    stmt = select(PriceAlert).options(selectinload(PriceAlert.asset)).order_by(PriceAlert.created_at.desc())
    if symbol:
        stmt = stmt.join(Asset).where(Asset.symbol == symbol.upper())
    return list((await session.execute(stmt)).scalars().all())


async def create_alert(
    session: AsyncSession,
    *,
    symbol: str,
    kind: AlertKind,
    threshold: Decimal,
) -> PriceAlert:
    asset = (
        await session.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if asset is None:
        raise AlertError(f"Titel {symbol} unbekannt.")
    if threshold <= 0:
        raise AlertError("Schwelle muss grösser als 0 sein.")
    row = PriceAlert(asset_id=asset.id, kind=kind, threshold=threshold, enabled=True)
    session.add(row)
    await session.flush()
    await session.refresh(row, attribute_names=["asset"])
    return row


async def delete_alert(session: AsyncSession, alert_id: UUID) -> bool:
    row = await session.get(PriceAlert, alert_id)
    if row is None:
        return False
    await session.delete(row)
    await session.flush()
    return True


async def check_alerts(
    session: AsyncSession,
    *,
    symbol: str | None = None,
    price: float | None = None,
    change_pct: float | None = None,
) -> list[PriceAlert]:
    from app.services.market import get_quote
    from app.services.push import broadcast

    stmt = (
        select(PriceAlert)
        .options(selectinload(PriceAlert.asset))
        .where(PriceAlert.enabled.is_(True), PriceAlert.fired_at.is_(None))
    )
    if symbol:
        stmt = stmt.join(Asset).where(Asset.symbol == symbol.upper())
    rows = list((await session.execute(stmt)).scalars().all())
    fired: list[PriceAlert] = []
    quotes: dict[str, tuple[float | None, float | None]] = {}
    if price is not None and symbol:
        quotes[symbol.upper()] = (price, change_pct)

    for alert in rows:
        if not alert.asset:
            continue
        sym = alert.asset.symbol
        if sym not in quotes:
            try:
                quote = await get_quote(sym, session)
            except Exception:
                quote = None
            if quote is None:
                last = float(alert.asset.last_price) if alert.asset.last_price is not None else None
                quotes[sym] = (last, None)
            else:
                quotes[sym] = (float(quote.price), quote.change_pct)
        px, chg = quotes[sym]
        if not alert_triggered(alert.kind, float(alert.threshold), price=px, change_pct=chg):
            continue
        alert.fired_at = datetime.now(UTC)
        alert.enabled = False
        fired.append(alert)
        try:
            await broadcast(session, _payload(alert, px, chg))
        except Exception:
            pass
    if fired:
        await session.flush()
    return fired
