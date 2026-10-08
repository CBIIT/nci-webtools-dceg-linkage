import os
import sys
import time


SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

os.environ.setdefault("LDLINK_INTERNAL_AUTH_TOKEN", "test-secret")

from session_auth import derive_session_id_from_cookie, _sign_payload  # noqa: E402


SECRET = "test-secret"


def make_cookie(issued_at_ms=None, nonce="nonce-value", secret=SECRET):
    issued_at = str(issued_at_ms if issued_at_ms is not None else int(time.time() * 1000))
    signature = _sign_payload(f"{issued_at}.{nonce}", secret)
    return f"{issued_at}.{nonce}.{signature}"


def test_derive_session_id_from_valid_cookie_is_deterministic():
    cookie = make_cookie()

    first = derive_session_id_from_cookie(cookie)
    second = derive_session_id_from_cookie(cookie)

    assert first is not None
    assert first == second


def test_derive_session_id_rejects_tampered_signature():
    cookie = make_cookie()
    tampered = cookie[:-1] + ("a" if cookie[-1] != "a" else "b")

    assert derive_session_id_from_cookie(tampered) is None


def test_derive_session_id_rejects_expired_cookie():
    eight_days_ago_ms = int(time.time() * 1000) - (8 * 24 * 60 * 60 * 1000)
    cookie = make_cookie(issued_at_ms=eight_days_ago_ms)

    assert derive_session_id_from_cookie(cookie) is None


def test_derive_session_id_rejects_malformed_cookie():
    assert derive_session_id_from_cookie("not-a-valid-cookie") is None
    assert derive_session_id_from_cookie("") is None
    assert derive_session_id_from_cookie(None) is None


def test_derive_session_id_rejects_wrong_secret():
    cookie = make_cookie(secret="a-different-secret")

    assert derive_session_id_from_cookie(cookie) is None
