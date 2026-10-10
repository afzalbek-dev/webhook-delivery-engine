# Webhook Delivery Engine

HMAC-SHA256 xavfsizlik imzosi, eksponensial qayta urinish (exponential backoff) va SQLite navbatiga ega ishonchli Webhook jo'natish tizimi.

## Xususiyatlari
- **HMAC Imzolash & Tekshirish**: Har bir jo'natilgan webhook so'roviga xavfsiz vaqt tamg'asi (timestamp) va SHA-256 imzosi biriktiriladi.
- **Eksponensial Backoff**: Tarmoq xatolari yoki 5xx javoblarida urinishlar oralig'i avtomatik oshirib boriladi.
- **Navbat boshqaruvi**: Webhooklar holati (pending, retry, delivered, failed) SQLite bazasida xavfsiz saqlanadi.
- **CLI Utility**: Terminal orqali webhook qo'shish va navbatni yuborish.

## Ishlatish
```python
from webhook_delivery import WebhookEngine, Signer, WebhookQueueStorage

storage = WebhookQueueStorage("webhooks.db")
signer = Signer("my-webhook-secret")
engine = WebhookEngine(storage=storage, signer=signer)

# Navbatga qo'shish
engine.enqueue("event_001", "https://api.partner.uz/webhook", '{"order_id": 99}')

# Navbatdagi xabarlarni jo'natish
engine.process_queue()
```

## CLI Buyruqlari
```bash
python3 -m webhook_delivery.cli enqueue evt_101 https://webhook.site/test '{"ping": "pong"}'
python3 -m webhook_delivery.cli process --secret my-secret
python3 -m webhook_delivery.cli status evt_101
```

## Testlar
```bash
pytest tests/ -v
```

## Litsenziya
MIT
