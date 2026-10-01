import sqlite3
import threading
from datetime import datetime, timezone

from models import Job


class JobsDB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                key TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                title TEXT,
                location TEXT,
                url TEXT NOT NULL,
                first_seen TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                name TEXT,
                first_seen TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_chat(self, chat_id: int, name: str = "") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO chats (chat_id, name, first_seen) VALUES (?, ?, ?)",
                (chat_id, name, now),
            )
            self.conn.commit()

    def chat_ids(self) -> list[int]:
        with self._lock:
            rows = self.conn.execute("SELECT chat_id FROM chats").fetchall()
        return [row[0] for row in rows]

    def new_jobs(self, jobs: list[Job]) -> list[Job]:
        with self._lock:
            new = []
            for job in jobs:
                row = self.conn.execute("SELECT 1 FROM seen_jobs WHERE key = ?", (job.key,))
                if row.fetchone() is None:
                    new.append(job)
        return new

    def mark_seen(self, jobs: list[Job]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.conn.executemany(
                """
                INSERT OR IGNORE INTO seen_jobs (key, company, title, location, url, first_seen)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [(j.key, j.company, j.title, j.location, j.url, now) for j in jobs],
            )
            self.conn.commit()

    def count(self) -> int:
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
