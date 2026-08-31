import pytest
from py_vapid import Vapid

from app.models.enums import RecommendationAction
from app.services.push import should_notify
from app.services.vapid import generate_vapid_keys, load_vapid_private


class _Rec:
    def __init__(self, action: RecommendationAction):
        self.action = action


def test_vapid_keys_are_webpush_shaped() -> None:
    private_pem, public_b64 = generate_vapid_keys()
    assert "BEGIN PRIVATE KEY" in private_pem
    assert public_b64.startswith("B")
    assert "=" not in public_b64


def test_pem_private_key_loads_for_webpush() -> None:
    private_pem, _public = generate_vapid_keys()
    with pytest.raises(Exception):
        Vapid.from_string(private_pem)
    vapid = load_vapid_private(private_pem)
    headers = vapid.sign({"sub": "mailto:wallstreet@localhost", "aud": "https://fcm.googleapis.com"})
    assert "Authorization" in headers


def test_notify_only_new_buy_sell() -> None:
    buy = _Rec(RecommendationAction.BUY)
    sell = _Rec(RecommendationAction.SELL)
    hold = _Rec(RecommendationAction.HOLD)
    assert should_notify(buy, None) is True
    assert should_notify(hold, None) is False
    assert should_notify(buy, buy) is False
    assert should_notify(sell, buy) is True
