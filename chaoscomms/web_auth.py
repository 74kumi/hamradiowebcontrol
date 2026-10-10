"""Web login and password verification helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

PASSWORD_SCHEME = "pbkdf2_sha256"


def make_password_hash(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int = 310_000,
) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "$".join(
        (
            PASSWORD_SCHEME,
            str(iterations),
            base64.urlsafe_b64encode(salt).decode().rstrip("="),
            base64.urlsafe_b64encode(digest).decode().rstrip("="),
        )
    )


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        scheme, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text + "===")
        expected = base64.urlsafe_b64decode(digest_text + "===")
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(actual, expected)


def web_username() -> str:
    return os.environ.get("CHAOSCOMMS_WEB_USERNAME", "admin")


def web_password_configured() -> bool:
    return bool(os.environ.get("CHAOSCOMMS_WEB_PASSWORD_HASH"))
