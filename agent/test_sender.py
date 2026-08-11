"""Sender tests with an in-process mock HTTP gateway.

Run: python3 test_sender.py

The mock server listens on a random port so tests can run in parallel without
port conflicts. Each test case gets a fresh buffer DB and mock state.
"""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, ".")
from buffer import LocalBuffer
from config import (
    AgentConfig, BatchConfig, BufferConfig, CheckpointConfig,
    LoggingConfig, RetryConfig, SourceConfig,
)
from sender import BatchSender

# ── helpers ───────────────────────────────────────────────────────────────────

DB = "/tmp/xdr-sender-test.db"
PASS, FAIL = 0, 0


def check(desc: str, cond: bool) -> None:
    global PASS, FAIL
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"[{status}] {desc}")


def cleanup() -> None:
    for f in [DB, DB + "-wal", DB + "-shm", "/tmp/xdr-sender-ckpt.json"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


# ── mock gateway ──────────────────────────────────────────────────────────────

class _MockHandler(BaseHTTPRequestHandler):
    """Stateful mock that returns pre-configured responses in order."""

    # Class-level state shared across all requests to this handler class.
    # Each test resets these via reset_mock().
    responses: list = []   # [(status_code, body_dict), ...]
    received: list = []    # request JSON bodies received so far

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _MockHandler.received.append(json.loads(body))

        if _MockHandler.responses:
            status, resp_body = _MockHandler.responses.pop(0)
        else:
            # Default fallback if test didn't pre-load a response
            status, resp_body = 200, {"status": "success", "queued": 0, "failed": 0}

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp_body).encode())

    def log_message(self, *args) -> None:
        pass  # suppress per-request noise in test output


def reset_mock() -> None:
    _MockHandler.responses.clear()
    _MockHandler.received.clear()


def _start_mock_server() -> tuple:
    # Port 0 → OS picks a free port; avoids conflicts when tests run in parallel
    server = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, f"http://127.0.0.1:{port}"


def _make_cfg(gateway_url: str) -> AgentConfig:
    return AgentConfig(
        tenant_id="test-tenant",
        gateway_url=gateway_url,
        sources=[],
        batch=BatchConfig(flush_interval_sec=9999, chunk_size=100),
        buffer=BufferConfig(path=DB, max_size_mb=50),
        # Very short delays so retry tests finish in milliseconds
        retry=RetryConfig(max_attempts=3, base_delay_sec=0.01, max_delay_sec=0.05),
        checkpoint=CheckpointConfig(path="/tmp/xdr-sender-ckpt.json"),
        logging=LoggingConfig(level="WARNING", path="/tmp/xdr-sender-test.log"),
    )


def _make_event() -> dict:
    return {"tenant_id": "test-tenant", "timestamp": "2026-05-04T00:00:00Z",
            "source_ip": "1.2.3.4", "event_type": "web_access"}


# ── start shared mock server ──────────────────────────────────────────────────

server, GATEWAY_URL = _start_mock_server()

# ── Test A: 200 → buffer is emptied ──────────────────────────────────────────
cleanup(); reset_mock()
_MockHandler.responses = [(200, {"status": "success", "queued": 2, "failed": 0})]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event(), _make_event()])

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("200: buffer emptied after send", buf.count() == 0)
check("200: gateway received 1 POST", len(_MockHandler.received) == 1)
check("200: gateway saw 2 events", len(_MockHandler.received[0]["events"]) == 2)
buf.close()

# ── Test B: 400 → events discarded (buffer emptied, no retry) ────────────────
cleanup(); reset_mock()
_MockHandler.responses = [(400, {"detail": "bad request"})]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event()])

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("400: buffer emptied (discard, no retry)", buf.count() == 0)
# Only 1 POST should have been made — 400 must not trigger retries
check("400: only 1 POST sent (no retry)", len(_MockHandler.received) == 1)
buf.close()

# ── Test C: 503 then 200 → retry succeeds, buffer emptied ────────────────────
cleanup(); reset_mock()
_MockHandler.responses = [
    (503, {}),
    (200, {"status": "success", "queued": 1, "failed": 0}),
]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event()])

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("503→200: buffer emptied after retry", buf.count() == 0)
check("503→200: gateway received exactly 2 POSTs", len(_MockHandler.received) == 2)
buf.close()

# ── Test D: 503 all attempts exhausted → events remain in buffer ──────────────
cleanup(); reset_mock()
# More 503s than max_attempts (3) so all retries fail
_MockHandler.responses = [(503, {})] * 10

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event()])

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("503 exhausted: events still in buffer", buf.count() == 1)
check("503 exhausted: exactly max_attempts POSTs sent",
      len(_MockHandler.received) == 3)   # max_attempts=3
buf.close()

# ── Test E: chunk_size splits large batches into multiple POSTs ───────────────
cleanup(); reset_mock()
# chunk_size=3 → 7 events should become ceil(7/3)=3 POSTs
cfg_small_chunk = _make_cfg(GATEWAY_URL)
cfg_small_chunk.batch.chunk_size = 3
_MockHandler.responses = [
    (200, {"status": "success", "queued": 3, "failed": 0}),
    (200, {"status": "success", "queued": 3, "failed": 0}),
    (200, {"status": "success", "queued": 1, "failed": 0}),
]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event()] * 7)

sender = BatchSender(cfg_small_chunk, buf)
sender._flush()

check("chunking: buffer empty after 3 POSTs", buf.count() == 0)
check("chunking: 3 POST requests made", len(_MockHandler.received) == 3)
check("chunking: first chunk has 3 events", len(_MockHandler.received[0]["events"]) == 3)
check("chunking: last chunk has 1 event",  len(_MockHandler.received[2]["events"]) == 1)
buf.close()

# ── Test F: 413 → chunk is halved and each half retried successfully ─────────
cleanup(); reset_mock()
_MockHandler.responses = [
    (413, {}),
    (200, {"status": "success", "queued": 2, "failed": 0}),
    (200, {"status": "success", "queued": 2, "failed": 0}),
]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event()] * 4)

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("413 split: buffer emptied", buf.count() == 0)
check("413 split: 3 POSTs made (1 rejected + 2 halves)", len(_MockHandler.received) == 3)
check("413 split: first half has 2 events", len(_MockHandler.received[1]["events"]) == 2)
check("413 split: second half has 2 events", len(_MockHandler.received[2]["events"]) == 2)
buf.close()

# ── Test G: 413 down to a single event → that event is discarded, sibling sent ─
cleanup(); reset_mock()
_MockHandler.responses = [
    (413, {}),                                              # whole batch (2 events)
    (413, {}),                                              # left half (1 event) — still too big, discard
    (200, {"status": "success", "queued": 1, "failed": 0}),  # right half (1 event) — sent
]

buf = LocalBuffer(DB, max_size_mb=50)
buf.push([_make_event(), _make_event()])

sender = BatchSender(_make_cfg(GATEWAY_URL), buf)
sender._flush()

check("413 min-split: buffer emptied (1 discarded + 1 sent)", buf.count() == 0)
check("413 min-split: exactly 3 POSTs (no retry on the discarded event)",
      len(_MockHandler.received) == 3)
buf.close()

# ── teardown ──────────────────────────────────────────────────────────────────
server.shutdown()
cleanup()

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(0 if FAIL == 0 else 1)
