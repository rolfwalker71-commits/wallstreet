from app.services.fx import convert, _parse_ecb
from app.services.prefs import normalize_patch, prefs_from_map


def test_convert_same_currency() -> None:
    assert convert(10, "USD", "USD", {"USD": 1.1, "CHF": 0.94, "EUR": 1}) == 10
    assert convert(10, "CHF", "native", {"USD": 1.1, "CHF": 0.94}) == 10


def test_convert_usd_to_chf() -> None:
    rates = {"EUR": 1.0, "USD": 1.10, "CHF": 0.94}
    chf = convert(110, "USD", "CHF", rates)
    assert chf is not None
    assert abs(chf - 94) < 0.01


def test_parse_ecb_cube() -> None:
    xml = """
    <gesmes:Envelope>
      <Cube>
        <Cube time="2026-08-29">
          <Cube currency="USD" rate="1.1700"/>
          <Cube currency="CHF" rate="0.9400"/>
        </Cube>
      </Cube>
    </gesmes:Envelope>
    """
    rates = _parse_ecb(xml)
    assert rates["EUR"] == 1.0
    assert rates["USD"] == 1.17
    assert rates["CHF"] == 0.94


def test_prefs_defaults_and_patch() -> None:
    prefs = prefs_from_map({})
    assert prefs.display_currency == "CHF"
    assert prefs.push_digest is False
    patch = normalize_patch(
        {
            "display_currency": "chf",
            "push_min_confidence": 0.7,
            "push_digest": True,
            "agent_interval_minutes": 60,
            "agent_watchlist_only": True,
            "agent_mini_only": True,
        }
    )
    assert patch["display_currency"] == "CHF"
    assert patch["push_min_confidence"] == "0.7"
    assert patch["agent_interval_minutes"] == "60"
    assert patch["agent_mini_only"] == "true"


def test_prefs_reject_bad_interval() -> None:
    try:
        normalize_patch({"agent_interval_minutes": 12})
    except ValueError as exc:
        assert "30" in str(exc)
    else:
        raise AssertionError("expected ValueError")
