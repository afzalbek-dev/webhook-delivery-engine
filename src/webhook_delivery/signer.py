import hmac
import hashlib
import time
from typing import Dict


class Signer:
    """Webhook so'rovlariga HMAC-SHA256 imzosi qo'yish va tekshirish."""

    def __init__(self, secret: str):
        if not secret:
            raise ValueError("Secret bo'sh bo'lishi mumkin emas")
        self.secret = secret.encode("utf-8")

    def sign(self, payload: str, timestamp: int = None) -> Dict[str, str]:
        if timestamp is None:
            timestamp = int(time.time())
        to_sign = f"{timestamp}.{payload}".encode("utf-8")
        signature = hmac.new(self.secret, to_sign, hashlib.sha256).hexdigest()
        return {
            "X-Webhook-Timestamp": str(timestamp),
            "X-Webhook-Signature": f"t={timestamp},v1={signature}",
        }

    def verify(self, payload: str, signature_header: str, tolerance_seconds: int = 300) -> bool:
        if not signature_header:
            return False

        parts = dict(part.split("=", 1) for part in signature_header.split(",") if "=" in part)
        if "t" not in parts or "v1" not in parts:
            return False

        try:
            timestamp = int(parts["t"])
        except ValueError:
            return False

        now = int(time.time())
        if abs(now - timestamp) > tolerance_seconds:
            return False

        to_sign = f"{timestamp}.{payload}".encode("utf-8")
        expected_sig = hmac.new(self.secret, to_sign, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, parts["v1"])
