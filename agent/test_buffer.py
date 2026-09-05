"""Buffer unit tests — run: python3 test_buffer.py"""

import os
import sys

sys.path.insert(0, ".")
from buffer import LocalBuffer

DB = "/tmp/xdr-buf-unit.db"
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
    for f in [DB, DB + "-wal", DB + "-shm"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def run_tests() -> None:
    # ── Test A: push / count / peek / delete ─────────────────────────────────
    cleanup()
    buf = LocalBuffer(DB, max_size_mb=10)

    events = [
        {"tenant_id": "t", "timestamp": f"2026-05-04T0{i}:00:00Z", "source_ip": f"1.1.1.{i}"}
        for i in range(5)
    ]
    buf.push(events)
    check("push 5: count == 5", buf.count() == 5)

    rows = buf.peek(3)
    check("peek(3): returns 3 rows", len(rows) == 3)
    # peek must return oldest-first so the sender always sends in arrival order
    check("peek: oldest first (id ascending)", rows[0][0] < rows[1][0] < rows[2][0])
    check("peek: event data round-trips correctly", rows[0][1]["source_ip"] == "1.1.1.0")

    buf.delete([rows[0][0], rows[1][0]])
    check("delete 2: count == 3", buf.count() == 3)

    # ── Test B: peek after partial delete ─────────────────────────────────
    rows2 = buf.peek(10)
    check("peek after delete: 3 rows remain", len(rows2) == 3)
    # After deleting ids 1 and 2, the first remaining event should be the third one
    check("peek after delete: correct first event", rows2[0][1]["source_ip"] == "1.1.1.2")

    # ── Test C: delete with empty list must not raise ──────────────────────
    try:
        buf.delete([])
        check("delete []: no exception", True)
    except Exception as exc:
        check(f"delete []: no exception (got {exc})", False)

    buf.close()
    cleanup()

    # ── Test D: data survives close + reopen ────────────────────────────────
    buf = LocalBuffer(DB, max_size_mb=10)
    buf.push([{"tenant_id": "t", "timestamp": "2026-05-04T09:00:00Z", "source_ip": "9.9.9.9"}])
    buf.close()

    buf2 = LocalBuffer(DB, max_size_mb=10)
    rows3 = buf2.peek(10)
    check("reopen: event persisted across close/open", len(rows3) == 1)
    check("reopen: event data intact", rows3[0][1]["source_ip"] == "9.9.9.9")
    buf2.close()
    cleanup()

    # ── Test E: overflow eviction ───────────────────────────────────────────
    # max_size_mb=1 → 1 MB limit.
    # Push ~12 MB of data; eviction should kick in and keep the DB under the limit.
    buf = LocalBuffer(DB, max_size_mb=1)
    big_event = {
        "tenant_id": "t",
        "timestamp": "2026-05-04T00:00:00Z",
        "raw_payload": "x" * 1000,   # ~1 KB per event
    }
    total_pushed = 0
    for _ in range(200):             # 200 batches × 50 events × ~1 KB ≈ 10 MB
        buf.push([big_event] * 50)
        total_pushed += 50

    count_after = buf.count()
    check("overflow: eviction ran (count < total pushed)", count_after < total_pushed)
    check("overflow: some events still in buffer", count_after > 0)
    buf.close()
    cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    # 這份檔案是手刻的獨立測試腳本（見檔頭 docstring：`python3 test_buffer.py`），
    # 不是給 pytest 收集用的——但檔名符合 test_*.py，pytest 掃到目錄時還是會
    # 嘗試 import 它。用這個 guard 讓 import 本身是無副作用的（不會真的跑測試、
    # 不會呼叫 sys.exit()），只有真的用 `python test_buffer.py` 執行才會跑。
    # 少了這個 guard，pytest import 這個模組時會執行到底部的 sys.exit()，
    # 在 collection 階段觸發 SystemExit，讓 pytest 整個 INTERNALERROR、
    # 後面所有測試都不會跑（曾經在 CI 實際發生過）。
    run_tests()
