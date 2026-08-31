from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import AlertKind
from app.schemas.common import AssetOut, ORMModel
from app.services.alerts import AlertError, create_alert, delete_alert, list_alerts

router = APIRouter()


class AlertIn(BaseModel):
    symbol: str
    kind: AlertKind
    threshold: float = Field(gt=0)


class AlertOut(ORMModel):
    id: UUID
    kind: AlertKind
    threshold: float
    enabled: bool
    fired_at: str | None = None
    created_at: str
    asset: AssetOut


def _out(row) -> dict:
    return {
        "id": row.id,
        "kind": row.kind,
        "threshold": float(row.threshold),
        "enabled": row.enabled,
        "fired_at": row.fired_at.isoformat() if row.fired_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else "",
        "asset": AssetOut.model_validate(row.asset),
    }


@router.get("")
async def get_alerts(symbol: str | None = None, db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = await list_alerts(db, symbol)
    return [_out(r) for r in rows]


@router.post("")
async def post_alert(payload: AlertIn, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        row = await create_alert(
            db,
            symbol=payload.symbol,
            kind=payload.kind,
            threshold=Decimal(str(payload.threshold)),
        )
    except AlertError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    await db.refresh(row, attribute_names=["asset"])
    return _out(row)


@router.delete("/{alert_id}")
async def remove_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await delete_alert(db, alert_id)
    if not ok:
        raise HTTPException(404, "Alarm nicht gefunden")
    await db.commit()
    return {"ok": True}
