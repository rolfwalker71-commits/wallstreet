from app.services.auth import (
    new_totp_secret,
    session_valid,
    sign_session,
    verify_code,
)


def test_totp_roundtrip() -> None:
    import pyotp

    secret = new_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_code(secret, code)
    assert verify_code(secret, f"{code[:3]} {code[3:]}")
    assert not verify_code(secret, "000000")
    assert not verify_code(secret, "12")


def test_session_cookie() -> None:
    secret = "cookie-secret"
    token = sign_session(secret)
    assert token.startswith("v1.perm.")
    assert session_valid(secret, token)
    assert not session_valid("other", token)
    assert not session_valid(secret, "v1.perm.deadbeef")
    assert not session_valid(secret, None)
