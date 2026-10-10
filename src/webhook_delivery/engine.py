import time
import math
from typing import Callable, Optional, Tuple
from .signer import Signer
from .storage import WebhookQueueStorage


class DeliveryStatus:
    PENDING = "pending"
    RETRY = "retry"
    DELIVERED = "delivered"
    FAILED = "failed"


class WebhookEngine:
    """Webhook jo'natish, eksponensial kechikish va xatolarni qayta ishlash dvigateli."""

    def __init__(
        self,
        storage: WebhookQueueStorage,
        signer: Optional[Signer] = None,
        base_backoff: float = 2.0,
        sender_func: Optional[Callable[[str, str, dict], Tuple[bool, int, str]]] = None,
    ):
        self.storage = storage
        self.signer = signer
        self.base_backoff = base_backoff
        self.sender_func = sender_func or self._default_mock_sender

    @staticmethod
    def _default_mock_sender(url: str, payload: str, headers: dict) -> Tuple[bool, int, str]:
        # Test va standart holat uchun mock / simulyator
        return True, 200, "OK"

    def calculate_backoff(self, attempt: int) -> float:
        """Eksponensial kechikishni hisoblash: base_backoff ^ attempt."""
        return self.base_backoff ** attempt

    def enqueue(self, event_id: str, target_url: str, payload: str, max_retries: int = 3):
        self.storage.enqueue(event_id, target_url, payload, max_retries)

    def process_queue(self, limit: int = 10) -> int:
        events = self.storage.get_pending(limit=limit)
        processed = 0

        for event in events:
            processed += 1
            headers = {"Content-Type": "application/json"}
            if self.signer:
                headers.update(self.signer.sign(event["payload"]))

            success, status_code, err_msg = self.sender_func(event["target_url"], event["payload"], headers)
            attempts = event["attempts"] + 1

            if success:
                self.storage.update_status(event["id"], DeliveryStatus.DELIVERED, attempts)
            else:
                if attempts >= event["max_retries"]:
                    self.storage.update_status(event["id"], DeliveryStatus.FAILED, attempts, last_error=err_msg)
                else:
                    delay = self.calculate_backoff(attempts)
                    next_retry = time.time() + delay
                    self.storage.update_status(
                        event["id"],
                        DeliveryStatus.RETRY,
                        attempts,
                        next_retry_at=next_retry,
                        last_error=err_msg,
                    )

        return processed
