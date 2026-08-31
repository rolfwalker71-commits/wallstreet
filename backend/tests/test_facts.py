from app.services.facts import (
    action_from_technicals,
    build_fact_rationale,
    headlines_from_sources,
)


def test_action_follows_rsi_thresholds_only() -> None:
    assert action_from_technicals({"rsi_14": 28})[0] == "buy"
    assert action_from_technicals({"rsi_14": 50})[0] == "hold"
    assert action_from_technicals({"rsi_14": 80})[0] == "sell"
    assert action_from_technicals({})[0] == "hold"


def test_rationale_does_not_invent_news() -> None:
    text = build_fact_rationale(
        symbol="META",
        name="Meta Platforms, Inc.",
        currency="USD",
        price=578.02,
        technicals={"rsi_14": 44, "sma_20": 560, "sma_50": 550, "last_close": 578.02},
        headlines=[],
        action="hold",
    )
    assert "keine Meldung, die den Titel namentlich nennt" in text
    assert "Akquisition" not in text
    assert "könnte" not in text


def test_headlines_from_sources_keep_titles_only() -> None:
    rows = headlines_from_sources(
        [{"title": "Pinterest CFO Exit", "source": "Yahoo Finance", "summary": "ignored"}]
    )
    assert rows == ["Pinterest CFO Exit (Yahoo Finance)"]
