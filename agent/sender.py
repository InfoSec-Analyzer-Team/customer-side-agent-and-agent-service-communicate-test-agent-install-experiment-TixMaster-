from __future__ import annotations

import logging
import time
import threading
from typing import List

import requests

from buffer import LocalBuffer
from config import AgentConfig

logger = logging.getLogger(__name__)


class BatchSender:
    """Reads events from LocalBuffer and POSTs them to the Gateway in chunks.

    Runs in its own thread (call run() in a daemon Thread).
    Flush happens every flush_interval_sec, or immediately when stop() is
    called so we drain the buffer on clean shutdown.
    """

    def __init__(self, cfg: AgentConfig, buffer: LocalBuffer) -> None:
        self._url = cfg.gateway_url.rstrip("/") + "/api/v1/ingest/batch"
        self._chunk_size = cfg.batch.chunk_size
        self._flush_interval = cfg.batch.flush_interval_sec
        self._max_attempts = cfg.retry.max_attempts
        self._base_delay = cfg.retry.base_delay_sec
        self._max_delay = cfg.retry.max_delay_sec
        self._buffer = buffer
        # Event used both as a sleep interruptor and a stop signal
        self._stop_event = threading.Event()

    # ── public interface ─────────────────────────────────────────────────────

    def run(self) -> None:
        """Block and flush on interval until stop() is called."""
        logger.info(
            "sender started — url=%s interval=%ds chunk=%d",
            self._url, self._flush_interval, self._chunk_size,
        )
        # wait(timeout) returns False on timeout, True when event is set
        while not self._stop_event.wait(timeout=self._flush_interval):
            self._flush()
        # Final drain before the thread exits
        self._flush()
        logger.info("sender stopped")

    def stop(self) -> None:
        """Signal the sender loop to exit after the current flush finishes."""
        self._stop_event.set()

    # ── flush logic ──────────────────────────────────────────────────────────

    def _flush(self) -> None:
        """Drain the buffer in chunk_size slices until empty or a 503 blocks us."""
        while True:
            rows = self._buffer.peek(self._chunk_size)
            if not rows:
                break  # buffer empty

            ids = [r[0] for r in rows]
            events = [r[1] for r in rows]

            success = self._send_with_retry(events)
            if success:
                # Covers both 200 (sent) and 400/413 (discarded): either way
                # remove from buffer so we don't re-attempt the same batch.
                self._buffer.delete(ids)
            else:
                # 503 survived all retries — leave in buffer, try next cycle
                logger.warning(
                    "flush aborted: %d events kept in buffer for next cycle",
                    len(ids),
                )
                break

            if len(rows) < self._chunk_size:
                break  # last (partial) chunk — buffer is now empty

    # ── HTTP with retry ───────────────────────────────────────────────────────

    def _send_with_retry(self, events: List[dict]) -> bool:
        """POST one chunk to the Gateway.

        Returns True  → caller should delete these events from buffer.
        Returns False → caller should leave events in buffer (retry next cycle).

        Status mapping (from CUSTOMER_AGENT_DESIGN.md §3.4):
          200 → sent OK, delete
          400 → bad payload, discard (return True so caller deletes)
          413 → body too large, discard (same as 400)
          503 → Kafka down, keep buffer, exponential backoff retry
        """
        payload = {"events": events}
        delay = self._base_delay

        for attempt in range(1, self._max_attempts + 1):
            try:
                t0 = time.monotonic()
                resp = requests.post(
                    self._url,
                    json=payload,
                    timeout=30,
                    headers={"Content-Type": "application/json"},
                )
                elapsed = time.monotonic() - t0

                if resp.status_code == 200:
                    body = resp.json()
                    logger.info(
                        "sent %d events — queued=%s failed=%s (%.2fs)",
                        len(events), body.get("queued"), body.get("failed"), elapsed,
                    )
                    return True

                elif resp.status_code == 503:
                    # Gateway/Kafka is down; backoff and retry this chunk
                    logger.warning(
                        "503 Kafka unavailable — attempt %d/%d, retry in %.0fs",
                        attempt, self._max_attempts, delay,
                    )
                    if attempt < self._max_attempts:
                        time.sleep(delay)
                        # Exponential backoff: 1s → 2s → 4s → … → 60s
                        delay = min(delay * 2, self._max_delay)

                elif resp.status_code in (400, 413):
                    # Payload permanently rejected; discard so the queue unblocks
                    logger.error(
                        "HTTP %d — discarding %d events (no retry)",
                        resp.status_code, len(events),
                    )
                    return True  # delete from buffer = discard

                else:
                    logger.warning(
                        "HTTP %d — unexpected, attempt %d/%d, retry in %.0fs",
                        resp.status_code, attempt, self._max_attempts, delay,
                    )
                    if attempt < self._max_attempts:
                        time.sleep(delay)
                        delay = min(delay * 2, self._max_delay)

            except requests.RequestException as exc:
                # Network error (timeout, connection refused, etc.)
                logger.warning(
                    "network error: %s — attempt %d/%d, retry in %.0fs",
                    exc, attempt, self._max_attempts, delay,
                )
                if attempt < self._max_attempts:
                    time.sleep(delay)
                    delay = min(delay * 2, self._max_delay)

        logger.error(
            "all %d retry attempts exhausted for %d events",
            self._max_attempts, len(events),
        )
        return False
