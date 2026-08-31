from app.services.picks import AssetSnapshot, buy_score, fact_rationale, rank_candidates


def _snap(**kwargs) -> AssetSnapshot:
    base = dict(
        symbol="NESN.SW",
        name="Nestlé N",
        asset_class="stock",
        exchange="SIX",
        watched=True,
        notes=None,
        last_price=78.6,
        currency="CHF",
        last_action="hold",
        last_confidence=0.65,
        headlines=(),
        technicals={"rsi_14": 38, "sma_20": 80, "sma_50": 79, "macd": 0.2, "macd_signal": 0.1, "last_close": 78.6},
    )
    base.update(kwargs)
    return AssetSnapshot(**base)


def test_swiss_blocked_assets_score_last() -> None:
    voo = _snap(symbol="VOO", asset_class="etf", exchange="NYQ")
    fx = _snap(symbol="EURUSD=X", asset_class="forex", exchange=None)
    assert buy_score(voo) == -100
    assert buy_score(fx) == -100


def test_oversold_buy_outranks_overbought_sell() -> None:
    dip = _snap(
        symbol="AAPL",
        last_action="hold",
        technicals={"rsi_14": 28, "sma_20": 210, "sma_50": 220, "macd": -0.1, "macd_signal": -0.2, "last_close": 200},
    )
    hot = _snap(
        symbol="NVDA",
        last_action="sell",
        technicals={"rsi_14": 78, "sma_20": 200, "sma_50": 180, "macd": 1, "macd_signal": 1.2, "last_close": 220},
    )
    assert buy_score(dip) > buy_score(hot)
    ranked = rank_candidates([hot, dip])
    assert ranked[0].symbol == "AAPL"
    assert all(s.last_action != "sell" for s in ranked)


def test_prior_buy_gets_a_boost() -> None:
    fresh = _snap(symbol="MSFT", last_action="buy", last_confidence=0.7)
    hold = _snap(symbol="META", last_action="hold", last_confidence=0.7)
    assert buy_score(fresh) > buy_score(hold)


def test_fact_rationale_lists_numbers_not_a_story() -> None:
    text = fact_rationale(_snap(headlines=("Nestlé raises prices",)))
    assert "NESN.SW" in text
    assert "RSI-14: 38.0" in text
    assert "Nestlé raises prices" in text
    assert "könnte" not in text.lower()
    assert "These" not in text
    assert "klarer Einstieg" not in text
    assert "weil RSI-14=38.0 ≤ 32" not in text
