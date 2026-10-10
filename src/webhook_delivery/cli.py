import argparse
import sys
import json
from .storage import WebhookQueueStorage
from .signer import Signer
from .engine import WebhookEngine


def main():
    parser = argparse.ArgumentParser(description="Webhook Delivery Engine CLI")
    parser.add_argument("--db", default="/tmp/webhook_delivery.db", help="SQLite ma'lumotlar bazasi")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enqueue_p = subparsers.add_parser("enqueue", help="Yangi webhook hodisasini navbatga qo'shish")
    enqueue_p.add_argument("id", help="Hodisa identifikatori")
    enqueue_p.add_argument("url", help="Qabul qiluvchi endpoint URL")
    enqueue_p.add_argument("payload", help="JSON formatidagi ma'lumot")
    enqueue_p.add_argument("--retries", type=int, default=3, help="Maksimal qayta urinishlar soni")

    process_p = subparsers.add_parser("process", help="Navbatdagi webhooklarni qayta ishlash")
    process_p.add_argument("--secret", default="test_secret", help="HMAC imzolash siri")

    status_p = subparsers.add_parser("status", help="Hodisa holatini ko'rish")
    status_p.add_argument("id", help="Hodisa identifikatori")

    args = parser.parse_args()
    storage = WebhookQueueStorage(args.db)

    if args.command == "enqueue":
        storage.enqueue(args.id, args.url, args.payload, max_retries=args.retries)
        print(f"NAVBATGA QO'SHILDI: {args.id} -> {args.url}")
    elif args.command == "process":
        signer = Signer(args.secret)
        engine = WebhookEngine(storage=storage, signer=signer)
        count = engine.process_queue()
        print(f"ISHLANDI: {count} ta webhook yuborildi.")
    elif args.command == "status":
        item = storage.get_event(args.id)
        if item:
            print(json.dumps(item, indent=2))
        else:
            print(f"Topilmadi: {args.id}")
            sys.exit(1)


if __name__ == "__main__":
    main()
