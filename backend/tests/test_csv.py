from app.models.enums import TransactionSide
from app.services.csv_trades import parse_trade_rows
from app.services.equity import replay_equity
from app.services.rebalance import propose_rebalance


def test_parse_valid_and_bad_rows() -> None:
    text = """date;isin;symbol;qty;price;side
2024-01-15;IE00BK5BQT80;VWCE.DE;10;100.5;buy
02.03.2024;;AAPL;2;180,25;Kauf
bad-date;;MSFT;1;400;buy
2024-04-01;;NVDA;-1;100;sell
2024-04-02;;;1;10;buy
"""
    rows, errors = parse_trade_rows(text)
    assert len(rows) == 2
    assert rows[0]["symbol"] == "VWCE.DE"
    assert rows[0]["side"] == TransactionSide.BUY
    assert rows[1]["side"] == TransactionSide.BUY
    assert any("Datum" in e["error"] for e in errors)
    assert any("grösser als 0" in e["error"] for e in errors)
    assert any("ISIN oder Symbol fehlt" in e["error"] for e in errors)


def test_parse_missing_headers() -> None:
    rows, errors = parse_trade_rows("foo,bar\n1,2\n")
    assert rows == []
    assert errors[0]["row"] == 0


def test_replay_equity_vs_benchmark() -> None:
    txs = [
        {"date": "2026-01-02", "symbol": "VWCE.DE", "qty": 10, "price": 100, "side": "buy"},
    ]
    points = replay_equity(
        initial_cash=2000,
        transactions=txs,
        price_by_symbol={"VWCE.DE": {"2026-01-02": 100, "2026-01-03": 110}},
        bench_prices={"2026-01-02": 50, "2026-01-03": 55},
    )
    assert points[0]["equity"] == 2000
    assert points[-1]["equity"] == 2100
    assert points[0]["equity_idx"] == 100
    assert points[-1]["benchmark_idx"] == 110


def test_rebalance_takes_first_two_affordable() -> None:
    allocation = {
        "cash": 10_000,
        "equity": 10_000,
        "currency": "CHF",
        "max_single_position_pct": 40,
        "sleeves": [
            {"sleeve": "stock", "label": "Aktien", "gap_pct": 60, "gap_value": 6000, "current_pct": 0, "target_pct": 60},
            {"sleeve": "commodity", "label": "Rohstoffe", "gap_pct": 5, "gap_value": 500, "current_pct": 0, "target_pct": 5},
            {"sleeve": "bond", "label": "Bonds", "gap_pct": 20, "gap_value": 2000, "current_pct": 0, "target_pct": 20},
            {"sleeve": "crypto", "label": "Crypto", "gap_pct": 0, "gap_value": 0, "current_pct": 0, "target_pct": 0},
            {"sleeve": "cash", "label": "Cash", "gap_pct": 15, "gap_value": 1500, "current_pct": 100, "target_pct": 15},
        ],
    }
    quotes = {
        "VWCE.DE": {"price": 120, "currency": "EUR", "name": "World", "swiss_buyable": True},
    }
    items = propose_rebalance(allocation=allocation, held=set(), quotes=quotes, limit=2)
    assert items[0]["symbol"] == "VWCE.DE"
    assert items[0]["qty"] >= 1
    assert items[0]["amount"] > 0
