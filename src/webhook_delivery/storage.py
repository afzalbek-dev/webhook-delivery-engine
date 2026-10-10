import sqlite3
import json
import time
from typing import List, Dict, Optional, Any


class WebhookQueueStorage:
    """Webhook yuborish navbatini SQLite ma'lumotlar bazasida saqlash."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id TEXT PRIMARY KEY,
                    target_url TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    next_retry_at REAL DEFAULT 0,
                    last_error TEXT,
                    created_at REAL NOT NULL
                )
                """
            )

    def enqueue(self, event_id: str, url: str, payload: str, max_retries: int = 3):
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO webhook_events (id, target_url, payload, status, attempts, max_retries, next_retry_at, created_at)
                VALUES (?, ?, ?, 'pending', 0, ?, ?, ?)
                """,
                (event_id, url, payload, max_retries, time.time(), time.time()),
            )

    def get_pending(self, limit: int = 10) -> List[Dict[str, Any]]:
        now = time.time()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, target_url, payload, status, attempts, max_retries, next_retry_at
            FROM webhook_events
            WHERE status IN ('pending', 'retry') AND next_retry_at <= ?
            LIMIT ?
            """,
            (now, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "target_url": r[1],
                "payload": r[2],
                "status": r[3],
                "attempts": r[4],
                "max_retries": r[5],
                "next_retry_at": r[6],
            }
            for r in rows
        ]

    def update_status(self, event_id: str, status: str, attempts: int, next_retry_at: float = 0, last_error: str = None):
        with self._conn:
            self._conn.execute(
                """
                UPDATE webhook_events
                SET status = ?, attempts = ?, next_retry_at = ?, last_error = ?
                WHERE id = ?
                """,
                (status, attempts, next_retry_at, last_error, event_id),
            )

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT id, target_url, payload, status, attempts, last_error FROM webhook_events WHERE id = ?", (event_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "target_url": r[1],
            "payload": r[2],
            "status": r[3],
            "attempts": r[4],
            "last_error": r[5],
        }

    def close(self):
        self._conn.close()
