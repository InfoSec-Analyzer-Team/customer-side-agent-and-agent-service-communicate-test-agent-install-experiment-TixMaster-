from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    data        TEXT    NOT NULL,
    inserted_at REAL    NOT NULL
);
"""


class LocalBuffer:
    """SQLite WAL-backed event queue.

    Thread-safe: multiple collector threads can push(); one sender thread
    calls peek() + delete(). All DB access serializes through self._lock.
    """

    def __init__(self, path: str, max_size_mb: int = 200) -> None:
        self.path = path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = threading.Lock()

        db_dir = os.path.dirname(path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._conn = sqlite3.connect(path, check_same_thread=False)

        # WAL mode: writer does not block readers, so sender can peek()
        # while a collector thread is mid-push(). Default journal mode
        # (DELETE) would lock the whole file on every write.
        self._conn.execute("PRAGMA journal_mode=WAL")

        # NORMAL: sync WAL header on commit but skip full fsync.
        # Gives ~10x write throughput vs FULL. On power loss we lose at most
        # the last in-flight transaction — acceptable for a local event queue.
        self._conn.execute("PRAGMA synchronous=NORMAL")

        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        logger.info("buffer opened: %s (max=%dMB)", path, max_size_mb)

    # ── write ────────────────────────────────────────────────────────────────

    #把 events 序列化成 JSON 後批次寫入 DB
    #寫完後呼叫 _evict_if_needed() 確保不超過大小限制
    def push(self, events: List[Dict[str, Any]]) -> None:
        """Insert events; evict oldest rows if DB exceeds size limit."""
        now = time.time()
        rows = [(json.dumps(e, ensure_ascii=False), now) for e in events]
        with self._lock:
            self._conn.executemany(
                "INSERT INTO events (data, inserted_at) VALUES (?, ?)", rows
            )
            self._conn.commit()
            self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        """Drop oldest rows until DB file is within max_size_bytes.

        We estimate how many rows to drop from (file_size / row_count) rather
        than scanning every row — O(1) regardless of table size.
        After deletion we checkpoint WAL so the main file actually shrinks on
        disk; without checkpoint the WAL grows and the main file stays large.
        """
        try:
            size = os.path.getsize(self.path)
            # In WAL mode writes accumulate in the -wal sidecar file first;
            # the main file only grows after checkpoint. Sum both so eviction
            # triggers even before a checkpoint has run.
            try:
                size += os.path.getsize(self.path + "-wal")
            except OSError:
                pass
        except OSError:
            return
        if size <= self.max_size_bytes:
            return

        count = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        if count == 0:
            return

        avg_bytes = size / count
        excess = size - self.max_size_bytes
        # +1 so we always drop at least one row even with integer rounding
        drop_n = max(1, int(excess / avg_bytes) + 1)

        self._conn.execute(
            "DELETE FROM events WHERE id IN "
            "(SELECT id FROM events ORDER BY id ASC LIMIT ?)",
            (drop_n,),
        )
        # Commit the delete first; checkpoint requires no active write transaction.
        self._conn.commit()
        # PASSIVE checkpoint: copy WAL → main file so disk space is reclaimed.
        # Best-effort — skip if another reader holds a lock; SQLite will
        # auto-checkpoint when WAL reaches 1000 pages anyway.
        try:
            self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except Exception:
            pass
        logger.warning("buffer overflow: evicted %d oldest events", drop_n)

    # ── read / delete ─────────────────────────────────────────────────────────

    def peek(self, limit: int) -> List[Tuple[int, Dict[str, Any]]]:
        """Return up to `limit` oldest events as (id, event_dict) pairs.

        Does NOT remove rows — caller must call delete(ids) after a confirmed
        successful send so events survive crashes between peek and delete.
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, data FROM events ORDER BY id ASC LIMIT ?", (limit,)
            ).fetchall()
        return [(row_id, json.loads(data)) for row_id, data in rows]

    def delete(self, ids: List[int]) -> None:
        """Remove events by id.

        Called after a successful send (200) or a permanent discard (400/413).
        Safe to call with an empty list.
        """
        if not ids:
            return
        # Build placeholders dynamically; SQLite has no array bind type
        placeholders = ",".join("?" * len(ids))
        with self._lock:
            self._conn.execute(
                f"DELETE FROM events WHERE id IN ({placeholders})", ids
            )
            self._conn.commit()

    # ── stats ────────────────────────────────────────────────────────────────

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()
