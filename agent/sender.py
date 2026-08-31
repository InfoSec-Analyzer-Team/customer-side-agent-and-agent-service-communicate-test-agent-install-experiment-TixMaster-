from __future__ import annotations

import datetime
import logging
import time
import threading
from typing import List

import requests

from buffer import LocalBuffer
from config import AgentConfig

logger = logging.getLogger(__name__)


def _auth_headers(api_key) -> dict:
    """Content-Type 一律帶上；有 api_key 時附 Bearer 憑證（見 AGENT_MANAGEMENT §3.2）。"""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    return headers


class HeartbeatSender:
    """Sends a periodic heartbeat event to the Gateway so it can detect dead agents."""

    def __init__(self, cfg: AgentConfig) -> None:
        self._url = cfg.gateway_url.rstrip("/") + "/api/v1/ingest"
        self._tenant_id = cfg.tenant_id
        self._agent_id = cfg.agent_id
        self._headers = _auth_headers(cfg.api_key)
        self._interval = cfg.heartbeat.interval_sec
        self._stop_event = threading.Event()

    def run(self) -> None:
        logger.info("heartbeat started — url=%s interval=%ds", self._url, self._interval)
        while not self._stop_event.wait(timeout=self._interval):
            self._send()
        logger.info("heartbeat stopped")

    def stop(self) -> None:
        self._stop_event.set()

    def _send(self) -> None:
        payload = {
            "tenant_id": self._tenant_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": "heartbeat",
        }
        if self._agent_id:
            payload["agent_id"] = self._agent_id
        try:
            resp = requests.post(self._url, json=payload, timeout=10, headers=self._headers)
            if resp.status_code == 200:
                logger.debug("heartbeat ok")
            else:
                logger.warning("heartbeat failed: HTTP %d", resp.status_code)
        except requests.RequestException as exc:
            logger.warning("heartbeat failed: %s", exc)


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
        self._agent_id = cfg.agent_id
        self._headers = _auth_headers(cfg.api_key)
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

            if not self._send_and_resolve(ids, events):
                # 503 survived all retries somewhere in this chunk — leave the
                # unresolved events in buffer, try next cycle
                logger.warning(
                    "flush aborted: %d events kept in buffer for next cycle",
                    len(ids),
                )
                break

            if len(rows) < self._chunk_size:
                break  # last (partial) chunk — buffer is now empty

    # ── HTTP with retry ───────────────────────────────────────────────────────

    def _send_and_resolve(self, ids: List[int], events: List[dict]) -> bool:
        """Send a chunk, splitting it in half on 413 until it fits or is 1 event.

        Returns True  → this slice is resolved (sent or permanently discarded)
                         and has been removed from buffer.
        Returns False → some part of this slice hit 503-exhausted and was left
                         in buffer for the next flush cycle.
        """
        outcome = self._send_with_retry(events)

        if outcome in ("sent", "discard"):
            self._buffer.delete(ids)
            return True

        if outcome == "exhausted":
            return False

        # outcome == "split": halve and retry each half independently, each
        # with its own full retry budget
        mid = len(events) // 2
        left_ok = self._send_and_resolve(ids[:mid], events[:mid])
        right_ok = self._send_and_resolve(ids[mid:], events[mid:])
        return left_ok and right_ok

    def _send_with_retry(self, events: List[dict]) -> str:
        """POST one chunk to the Gateway.

        Returns one of:
          "sent"      → 200, caller should delete these events from buffer
          "discard"   → permanently rejected, caller should delete (no retry)
          "split"     → 413 on more than one event, caller should halve and retry
          "exhausted" → retries ran out, caller should leave events in buffer

        Status mapping (from CUSTOMER_AGENT_DESIGN.md §3.4):
          200 → sent OK, delete
          400 → bad payload, discard (whole chunk, no retry)
          401/403 → auth rejected (bad/revoked key, tenant mismatch, disabled agent);
                keep buffer and backoff-retry so data is not lost while the operator
                fixes the key / re-enables the agent (see AGENT_MANAGEMENT §3.2)
          413 → body too large; halve the chunk and retry each half, unless
                already down to a single event, in which case discard it
          503 → Kafka down, keep buffer, exponential backoff retry
        """
        # 批次信封層帶一次 agent_id（非逐筆）；權威身分仍以 Bearer key 對應為準。
        payload = {"events": events}
        if self._agent_id:
            payload["agent_id"] = self._agent_id
        delay = self._base_delay

        for attempt in range(1, self._max_attempts + 1):
            try:
                t0 = time.monotonic()
                resp = requests.post(
                    self._url,
                    json=payload,
                    timeout=30,
                    headers=self._headers,
                )
                elapsed = time.monotonic() - t0

                if resp.status_code == 200:
                    body = resp.json()
                    logger.info(
                        "sent %d events — queued=%s failed=%s (%.2fs)",
                        len(events), body.get("queued"), body.get("failed"), elapsed,
                    )
                    return "sent"

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

                elif resp.status_code in (401, 403):
                    # 憑證/授權被拒：換 key 或重新啟用 Agent 後即可恢復，故保留 buffer
                    # 並退避重試，不丟資料（重試耗盡則留待下個 flush 週期）。
                    logger.warning(
                        "HTTP %d auth rejected — keeping %d events, attempt %d/%d, retry in %.0fs",
                        resp.status_code, len(events), attempt, self._max_attempts, delay,
                    )
                    if attempt < self._max_attempts:
                        time.sleep(delay)
                        delay = min(delay * 2, self._max_delay)

                elif resp.status_code == 413:
                    if len(events) == 1:
                        logger.error(
                            "HTTP 413 on a single event — discarding (cannot split further)",
                        )
                        return "discard"
                    logger.warning(
                        "HTTP 413 — splitting %d events into 2 chunks and retrying",
                        len(events),
                    )
                    return "split"

                elif resp.status_code == 400:
                    # Payload permanently rejected; discard so the queue unblocks
                    logger.error(
                        "HTTP 400 — discarding %d events (no retry)",
                        len(events),
                    )
                    return "discard"

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
        return "exhausted"
