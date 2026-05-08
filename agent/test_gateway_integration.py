"""Gateway 整合測試 — 需要平台 stack 正在執行

執行前請確認 Gateway 已啟動：
  cd log-analysis-core
  POSTGRES_PASSWORD=localtest docker-compose up -d
  # 等待約 30 秒讓所有服務健康

執行方式：
  cd agent
  python3 test_gateway_integration.py                       # 預設連 localhost:80
  python3 test_gateway_integration.py --gateway http://1.2.3.4:80
"""

import argparse
import json
import sys
import threading
import time
import os

sys.path.insert(0, ".")
import requests
from buffer import LocalBuffer
from config import (
    AgentConfig, BatchConfig, BufferConfig, CheckpointConfig,
    LoggingConfig, RetryConfig, SourceConfig,
)
from sender import BatchSender

# ── CLI ───────────────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--gateway", default="http://localhost:80",
                help="Gateway base URL（預設 http://localhost:80）")
ap.add_argument("--tenant", default="tenant-demo-001",
                help="tenant_id（預設 tenant-demo-001）")
ARGS = ap.parse_args()

GATEWAY = ARGS.gateway.rstrip("/")
TENANT  = ARGS.tenant

PASS, FAIL = 0, 0

def check(desc: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    line = f"[{status}] {desc}"
    if detail:
        line += f"\n       ↳ {detail}"
    print(line)

def cleanup():
    for f in ["/tmp/xdr-integ.db", "/tmp/xdr-integ.db-wal",
              "/tmp/xdr-integ.db-shm", "/tmp/xdr-integ-ckpt.json"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

print(f"=== Gateway 整合測試  ({GATEWAY}) ===\n")

# ── Test A: health check ──────────────────────────────────────────────────────
print("--- A: Health Check ---")
try:
    r = requests.get(f"{GATEWAY}/health", timeout=5)
    check("GET /health 回傳 200", r.status_code == 200,
          f"status={r.status_code} body={r.text[:80]}")
    # Gateway 回傳 "healthy" 或 {"status":"ok"} 均視為正常
    body_ok = "ok" in r.text.lower() or "healthy" in r.text.lower()
    check("GET /health body 包含 ok/healthy", body_ok, r.text[:80])
except requests.RequestException as e:
    check("GET /health 可連線", False, str(e))
    print("\n⚠  Gateway 無法連線，後續測試略過。")
    print(f"   請先啟動平台：cd log-analysis-core && POSTGRES_PASSWORD=localtest docker-compose up -d\n")
    sys.exit(1)

# ── Test B: 單筆 /api/v1/ingest ───────────────────────────────────────────────
print("\n--- B: 單筆 POST /api/v1/ingest ---")
single_event = {
    "tenant_id": TENANT,
    "timestamp": "2026-05-08T10:00:00.000Z",
    "source_ip": "203.0.113.1",
    "event_type": "web_access",
    "user_agent": "xdr-agent-integration-test/1.0",
    "payload": {"method": "GET", "url": "/integ-test-single", "status": 200, "size": 512},
    "raw_payload": '203.0.113.1 - - [08/May/2026:10:00:00 +0000] "GET /integ-test-single HTTP/1.1" 200 512 "-" "xdr-agent-integration-test/1.0"',
}
try:
    r = requests.post(
        f"{GATEWAY}/api/v1/ingest",
        json=single_event,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    check("POST /api/v1/ingest 回傳 200", r.status_code == 200,
          f"status={r.status_code} body={r.text[:120]}")
    if r.status_code == 200:
        body = r.json()
        check("response 包含 status=success", body.get("status") == "success",
              json.dumps(body))
except requests.RequestException as e:
    check("POST /api/v1/ingest 可連線", False, str(e))

# ── Test C: 批次 /api/v1/ingest/batch ────────────────────────────────────────
print("\n--- C: 批次 POST /api/v1/ingest/batch ---")
batch_events = [
    {
        "tenant_id": TENANT,
        "timestamp": f"2026-05-08T10:01:0{i}.000Z",
        "source_ip": f"203.0.113.{10 + i}",
        "event_type": "web_access",
        "user_agent": "xdr-agent-integration-test/1.0",
        "payload": {"method": "GET", "url": f"/integ-test-batch-{i}", "status": 200, "size": 256},
        "raw_payload": f'203.0.113.{10 + i} - - [08/May/2026:10:01:0{i} +0000] "GET /integ-test-batch-{i} HTTP/1.1" 200 256',
    }
    for i in range(5)
]
try:
    r = requests.post(
        f"{GATEWAY}/api/v1/ingest/batch",
        json={"events": batch_events},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    check("POST /api/v1/ingest/batch 回傳 200", r.status_code == 200,
          f"status={r.status_code} body={r.text[:120]}")
    if r.status_code == 200:
        body = r.json()
        check("response status=success", body.get("status") == "success",
              json.dumps(body))
        check(f"queued={body.get('queued')} (應為 5)",
              body.get("queued") == 5, json.dumps(body))
        check("failed=0（無 schema 錯誤）", body.get("failed") == 0,
              json.dumps(body))
except requests.RequestException as e:
    check("POST /api/v1/ingest/batch 可連線", False, str(e))

# ── Test D: 透過 BatchSender + LocalBuffer 端到端送出 ─────────────────────────
print("\n--- D: BatchSender 端到端（buffer → POST → buffer 清空）---")
cleanup()

cfg = AgentConfig(
    tenant_id=TENANT,
    gateway_url=GATEWAY,
    sources=[],
    batch=BatchConfig(flush_interval_sec=9999, chunk_size=100),
    buffer=BufferConfig(path="/tmp/xdr-integ.db", max_size_mb=50),
    retry=RetryConfig(max_attempts=3, base_delay_sec=0.5, max_delay_sec=5.0),
    checkpoint=CheckpointConfig(path="/tmp/xdr-integ-ckpt.json"),
    logging=LoggingConfig(level="WARNING", path="/tmp/xdr-integ-agent.log"),
)

buf = LocalBuffer(cfg.buffer.path, cfg.buffer.max_size_mb)

# 推入 10 筆 events
sender_events = [
    {
        "tenant_id": TENANT,
        "timestamp": f"2026-05-08T10:02:{i:02d}.000Z",
        "source_ip": "10.0.0.1",
        "event_type": "web_access",
        "payload": {"method": "GET", "url": f"/sender-test-{i}", "status": 200, "size": 128},
        "raw_payload": f'10.0.0.1 - - [08/May/2026:10:02:{i:02d} +0000] "GET /sender-test-{i} HTTP/1.1" 200 128',
    }
    for i in range(10)
]
buf.push(sender_events)
check("push 10 events 進 buffer", buf.count() == 10)

# 手動 flush（不啟動 background thread，避免測試超時）
sender = BatchSender(cfg, buf)
sender._flush()

check("flush 後 buffer 清空（events 已送出）", buf.count() == 0,
      f"剩餘 count={buf.count()}")
buf.close()
cleanup()

# ── Test E: 超大批次 — 驗證 chunking（6 筆，chunk_size=2 → 3 次 POST）────────
print("\n--- E: chunk_size=2，6 筆 events → 應送出 3 次 POST ---")
cleanup()

# 在 Gateway 和 BatchSender 之間加一個 proxy counter
_original_post = requests.post
_post_count = 0

def _counting_post(url, **kwargs):
    global _post_count
    if "/ingest/batch" in url:
        _post_count += 1
    return _original_post(url, **kwargs)

requests.post = _counting_post

cfg_small = AgentConfig(
    tenant_id=TENANT,
    gateway_url=GATEWAY,
    sources=[],
    batch=BatchConfig(flush_interval_sec=9999, chunk_size=2),  # 強制每次只送 2 筆
    buffer=BufferConfig(path="/tmp/xdr-integ.db", max_size_mb=50),
    retry=RetryConfig(max_attempts=2, base_delay_sec=0.1, max_delay_sec=1.0),
    checkpoint=CheckpointConfig(path="/tmp/xdr-integ-ckpt.json"),
    logging=LoggingConfig(level="WARNING", path="/tmp/xdr-integ-agent.log"),
)
buf2 = LocalBuffer(cfg_small.buffer.path, cfg_small.buffer.max_size_mb)
buf2.push([
    {"tenant_id": TENANT, "timestamp": f"2026-05-08T10:03:{i:02d}.000Z",
     "source_ip": "10.0.0.2", "event_type": "web_access",
     "raw_payload": f"chunk-test line {i}"}
    for i in range(6)
])
sender2 = BatchSender(cfg_small, buf2)
sender2._flush()

requests.post = _original_post  # 還原

check("chunking: 6 events / chunk_size=2 → 3 次 POST", _post_count == 3,
      f"實際 POST 次數={_post_count}")
check("chunking: buffer 全部清空", buf2.count() == 0)
buf2.close()
cleanup()

# ── 結果 ──────────────────────────────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"結果：{PASS} passed, {FAIL} failed")
if FAIL > 0:
    print("\n提示：若 Test B/C/D/E 失敗，請確認：")
    print(f"  1. Gateway 已啟動（curl {GATEWAY}/health）")
    print(f"  2. tenant_id '{TENANT}' 在平台端已存在")
    print(f"  3. Redpanda 正常（docker-compose ps redpanda）")
sys.exit(0 if FAIL == 0 else 1)
