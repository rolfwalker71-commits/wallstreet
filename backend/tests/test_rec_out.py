from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import RecommendationAction, RecommendationStatus
from app.services.rec_out import recommendation_out


def test_recommendation_out_without_outcome_relationship() -> None:
    asset = SimpleNamespace(
        id=uuid4(),
        symbol="VWCE.DE",
        name="Vanguard FTSE All-World",
        asset_class="etf",
        exchange="XETRA",
        currency="EUR",
        last_price=Decimal("140"),
        last_price_at=None,
        sector=None,
        isin="IE00BK5BQT80",
        watched=True,
        notes=None,
        user_note=None,
    )
    rec = SimpleNamespace(
        id=uuid4(),
        run_id=uuid4(),
        action=RecommendationAction.BUY,
        confidence=Decimal("0.70"),
        risk_reward_ratio=None,
        rationale="Startkauf VWCE.DE.",
        news_summary=None,
        news_sources=None,
        technicals=None,
        proposed_qty=Decimal("10"),
        proposed_price=Decimal("140"),
        status=RecommendationStatus.OPEN,
        glossary_terms=["TER"],
        suggested_symbols=["CSSMI.SW"],
        created_at=datetime.now(UTC),
        asset=asset,
        agent_logs=[],
        outcome=None,
    )
    out = recommendation_out(rec)
    assert out.asset.symbol == "VWCE.DE"
    assert out.outcome is None
    assert out.proposed_qty == Decimal("10")
