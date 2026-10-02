"""Server-side verification of the signed browser session cookie set by the
Next.js frontend (see client/src/lib/session.ts, client/src/app/api/init-browser-session).

The Next.js web proxy already forwards a derived session id via the X-Session-Id
header for fetch()-based API calls (see internal_auth_guard in LDlink.py). But plain
browser navigation (e.g. an <a href> download link) cannot carry custom headers --
only the same-origin cookie is sent automatically. This module lets Flask
independently verify that cookie and derive the *same* session id, so download links
can still be authorized without relying on the internal-auth-gated JSON API path.
"""
import base64
import hashlib
import hmac
import os
import time

COOKIE_NAME = "ldlink_browser_session"
COOKIE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _sign_payload(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _is_signed_session_value_valid(value: str, secret: str) -> bool:
    parts = value.split(".")
    if len(parts) != 3:
        return False
    issued_at_raw, nonce, signature = parts
    try:
        issued_at = int(issued_at_raw)
    except ValueError:
        return False
    if issued_at <= 0 or not nonce or not signature:
        return False

    now_ms = int(time.time() * 1000)
    if issued_at > now_ms + 5 * 60 * 1000:
        return False
    if now_ms - issued_at > COOKIE_MAX_AGE_SECONDS * 1000:
        return False

    expected_signature = _sign_payload(f"{issued_at_raw}.{nonce}", secret)
    return hmac.compare_digest(expected_signature, signature)


def derive_session_id_from_cookie(cookie_value):
    """Verifies a signed browser session cookie value and returns the same
    sha256-hex session id the Next.js proxy derives, or None if missing/invalid."""
    secret = os.environ.get("LDLINK_INTERNAL_AUTH_TOKEN", "").strip()
    cookie_value = (cookie_value or "").strip()
    if not secret or not cookie_value:
        return None
    if not _is_signed_session_value_valid(cookie_value, secret):
        return None
    return hashlib.sha256(cookie_value.encode("utf-8")).hexdigest()
