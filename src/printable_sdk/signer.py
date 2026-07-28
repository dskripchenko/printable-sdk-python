"""Request/webhook signing, byte-compatible with the Printable server."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from .canonical import canonicalize


class Signer:
    """simple: sha256(token+timestamp+salt+secret);
    strict: HMAC-SHA256(canonical(payload), secret+salt);
    webhook: HMAC-SHA256("{timestamp}.{raw_body}", secret)."""

    def __init__(self, salt: str) -> None:
        if not salt:
            raise ValueError("Printable salt must not be empty.")
        self._salt = salt

    def sign_token(self, token: str, timestamp: int, secret_key: str) -> str:
        data = f"{token}{timestamp}{self._salt}{secret_key}".encode()
        return hashlib.sha256(data).hexdigest()

    def sign_payload(self, payload: dict[str, Any], secret_key: str) -> str:
        key = (secret_key + self._salt).encode()
        return hmac.new(key, canonicalize(payload).encode(), hashlib.sha256).hexdigest()

    def verify_webhook(self, signature: str, timestamp: int, raw_body: str, secret_key: str) -> bool:
        expected = hmac.new(
            secret_key.encode(), f"{timestamp}.{raw_body}".encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
