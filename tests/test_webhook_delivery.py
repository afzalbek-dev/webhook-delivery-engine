import pytest
import time
from webhook_delivery.signer import Signer
from webhook_delivery.storage import WebhookQueueStorage
from webhook_delivery.engine import WebhookEngine, DeliveryStatus


def test_hmac_signer_and_verifier():
    signer = Signer("super-secret-key")
    payload = '{"event": "order.paid", "amount": 150000}'
    
    headers = signer.sign(payload)
    assert "X-Webhook-Signature" in headers
    assert "X-Webhook-Timestamp" in headers
    
    sig_header = headers["X-Webhook-Signature"]
    assert signer.verify(payload, sig_header) is True
    
    # Buzilgan payload
    assert signer.verify('{"event": "order.cancelled"}', sig_header) is False
    
    # Boshqa kalit
    fake_signer = Signer("wrong-key")
    assert fake_signer.verify(payload, sig_header) is False


def test_webhook_engine_success(tmp_path):
    db_file = str(tmp_path / "webhooks.db")
    storage = WebhookQueueStorage(db_file)
    
    delivered_calls = []
    def dummy_sender(url, payload, headers):
        delivered_calls.append((url, payload))
        return True, 200, "OK"

    engine = WebhookEngine(storage=storage, sender_func=dummy_sender)
    engine.enqueue("evt_1", "https://api.example.com/hook", '{"status": "ok"}')
    
    processed = engine.process_queue()
    assert processed == 1
    assert len(delivered_calls) == 1
    
    event = storage.get_event("evt_1")
    assert event["status"] == DeliveryStatus.DELIVERED
    assert event["attempts"] == 1
    storage.close()


def test_webhook_engine_retry_and_failure(tmp_path):
    db_file = str(tmp_path / "webhooks_retry.db")
    storage = WebhookQueueStorage(db_file)
    
    def failing_sender(url, payload, headers):
        return False, 500, "Internal Server Error"

    engine = WebhookEngine(storage=storage, sender_func=failing_sender, base_backoff=0.1)
    engine.enqueue("evt_fail", "https://api.example.com/fail", '{"x": 1}', max_retries=2)
    
    # 1-urinish
    engine.process_queue()
    ev = storage.get_event("evt_fail")
    assert ev["status"] == DeliveryStatus.RETRY
    assert ev["attempts"] == 1
    
    # Kutish va 2-urinish
    time.sleep(0.2)
    engine.process_queue()
    ev = storage.get_event("evt_fail")
    assert ev["status"] == DeliveryStatus.FAILED
    assert ev["attempts"] == 2
    storage.close()
