# XDR Agent ↔ Gateway 連線教學

本文件說明如何在本地開發環境將 XDR Customer Agent 連上 log-analysis-core 平台，
並驗證 log 資料確實流進 Kafka → Elasticsearch → Kibana。

---

## 前置條件

| 需求 | 說明 |
|------|------|
| Docker Desktop | 需處於執行中狀態 |
| `log-analysis-core` repo | 與本 repo 在同一台機器 |
| Python 3.10+ | agent 執行環境 |
| `pip3 install PyYAML requests` | agent 依賴 |

---

## Step 1 — 啟動平台 Stack

```bash
cd log-analysis-core

# 若 .env 尚未設定 POSTGRES_PASSWORD，先補上
echo "POSTGRES_PASSWORD=localtest" >> .env

# 啟動全部服務（第一次約需 2~3 分鐘下載 images）
POSTGRES_PASSWORD=localtest docker-compose up -d
```

### 確認各服務健康

```bash
# 等待所有 container 變成 healthy（約 30 秒）
docker-compose ps

# 快速確認 Gateway 可用
curl http://localhost:80/health
# 預期：{"status": "ok"} 或 "healthy"
```

如果 Gateway 還沒好，多等幾秒再試。所有服務的啟動順序：
```
Redpanda → gateway1/2/3 → Nginx(port 80) → log_processor → ml_worker → storage_writer
```

---

## Step 2 — 設定 Agent config

```bash
cd agent
cp config.yaml.example config.yaml
```

編輯 `config.yaml`：

```yaml
tenant_id: "tenant-demo-001"          # 平台預設測試 tenant
gateway_url: "http://localhost:80"    # Nginx → Gateway cluster

sources:
  - type: file
    path: /tmp/xdr-test/access.log    # 測試用假 log 路徑
    format: nginx_combined

batch:
  flush_interval_sec: 30   # 測試時縮短到 30 秒，方便觀察
  chunk_size: 5000

buffer:
  path: /tmp/xdr-test/buffer.db
  max_size_mb: 200

checkpoint:
  path: /tmp/xdr-test/checkpoint.json

logging:
  level: INFO
  path: /tmp/xdr-test/agent.log
```

### （選用）Ingest API Key 憑證

平台 Gateway 導入憑證驗證後（`INGEST_REQUIRE_AUTH=true`），Agent 需帶平台 Portal
產生的 Ingest API Key。Agent 會在所有請求附上 `Authorization: Bearer <api_key>`。
憑證優先從環境變數讀取（不落版控）：

```bash
export XDR_API_KEY="lac_xxxxxxxxxxxxxxxx"
python3 -u agent.py --config config.yaml
```

或在 config.yaml 填 `api_key:` / `agent_id:`（見 config.yaml.example）。
本地測試預設 `INGEST_REQUIRE_AUTH=false`，留空即可（匿名放行）。

---

## Step 3 — 準備測試 log 來源

```bash
mkdir -p /tmp/xdr-test

# 寫入幾筆假 nginx log
cat > /tmp/xdr-test/access.log << 'EOF'
203.0.113.10 - - [08/May/2026:10:00:00 +0000] "GET /api/v1/products HTTP/1.1" 200 1024 "-" "Mozilla/5.0"
198.51.100.5 - - [08/May/2026:10:00:01 +0000] "POST /login HTTP/1.1" 401 212 "-" "curl/7.68.0"
192.0.2.33   - - [08/May/2026:10:00:02 +0000] "GET /admin HTTP/1.1" 403 128 "-" "python-requests/2.31"
EOF
```

---

## Step 4 — 驗證 Gateway 可以接收資料（不需 Agent）

先用 `curl` 直接打 Gateway，確認平台端沒問題再啟動 Agent：

```bash
# 單筆測試
curl -s -X POST http://localhost:80/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo-001",
    "timestamp": "2026-05-08T10:00:00.000Z",
    "source_ip": "1.2.3.4",
    "event_type": "web_access",
    "raw_payload": "1.2.3.4 - - [08/May/2026:10:00:00 +0000] \"GET / HTTP/1.1\" 200 512"
  }' | python3 -m json.tool

# 預期回應：
# {"status": "success", "message": "Log queued"}
```

```bash
# 批次測試（5 筆）
curl -s -X POST http://localhost:80/api/v1/ingest/batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"tenant_id":"tenant-demo-001","timestamp":"2026-05-08T10:01:00Z","source_ip":"10.0.0.1","raw_payload":"line1"},
      {"tenant_id":"tenant-demo-001","timestamp":"2026-05-08T10:01:01Z","source_ip":"10.0.0.2","raw_payload":"line2"},
      {"tenant_id":"tenant-demo-001","timestamp":"2026-05-08T10:01:02Z","source_ip":"10.0.0.3","raw_payload":"line3"},
      {"tenant_id":"tenant-demo-001","timestamp":"2026-05-08T10:01:03Z","source_ip":"10.0.0.4","raw_payload":"line4"},
      {"tenant_id":"tenant-demo-001","timestamp":"2026-05-08T10:01:04Z","source_ip":"10.0.0.5","raw_payload":"line5"}
    ]
  }' | python3 -m json.tool

# 預期回應：
# {"status": "success", "queued": 5, "failed": 0}
```

---

## Step 5 — 執行整合測試腳本

```bash
cd agent
python3 test_gateway_integration.py
```

預期全部通過：

```
=== Gateway 整合測試  (http://localhost:80) ===

--- A: Health Check ---
[PASS] GET /health 回傳 200
[PASS] GET /health body 包含 ok/healthy

--- B: 單筆 POST /api/v1/ingest ---
[PASS] POST /api/v1/ingest 回傳 200
[PASS] response 包含 status=success

--- C: 批次 POST /api/v1/ingest/batch ---
[PASS] POST /api/v1/ingest/batch 回傳 200
[PASS] response status=success
[PASS] queued=5 (應為 5)
[PASS] failed=0（無 schema 錯誤）

--- D: BatchSender 端到端（buffer → POST → buffer 清空）---
[PASS] push 10 events 進 buffer
[PASS] flush 後 buffer 清空（events 已送出）

--- E: chunk_size=2，6 筆 events → 應送出 3 次 POST ---
[PASS] chunking: 6 events / chunk_size=2 → 3 次 POST
[PASS] chunking: buffer 全部清空

========================================
結果：12 passed, 0 failed
```

---

## Step 6 — 啟動 Agent 並觀察資料流入

```bash
# 方式 A：dry-run（只解析，不傳送）
python3 -u agent.py --config config.yaml --dry-run --from-beginning

# 方式 B：實際傳送
python3 -u agent.py --config config.yaml --from-beginning
```

啟動後在另一個終端機持續往 log 檔追加資料：

```bash
# 每秒產生一筆假 log
while true; do
  echo "$(date +'%-d/%b/%Y:%H:%M:%S +0000') - 203.0.113.$((RANDOM % 255)) - - [$(date +'%d/%b/%Y:%H:%M:%S +0000')] \"GET /path/$RANDOM HTTP/1.1\" 200 $((RANDOM % 5000)) \"-\" \"test-agent/1.0\"" \
    >> /tmp/xdr-test/access.log
  sleep 1
done
```

---

## Step 7 — 驗收：確認資料進了平台

### 7-1 Redpanda Console（Kafka UI）

```
http://localhost:18080
```

- 進入 `Topics` → `raw-logs`
- 應看到新訊息不斷進來

### 7-2 Kibana

```
http://localhost:5601
```

- `Discover` → 選 index pattern `logs-*`（或依平台設定）
- 應看到剛才傳送的 events

### 7-3 直接查 Redpanda topic 筆數（CLI）

```bash
docker exec -it log-analysis-redpanda \
  rpk topic consume raw-logs --num 5
```

---

## 常見問題

| 症狀 | 原因 | 解法 |
|------|------|------|
| `curl: (7) Failed to connect` | Gateway 未啟動 | `docker-compose up -d`，等健康 |
| HTTP 503 | Kafka/Redpanda 未就緒 | `docker-compose ps redpanda`；多等幾秒 |
| HTTP 400 `missing required field` | payload 缺 `tenant_id` 或 `timestamp` | 確認 config.yaml 的 `tenant_id` 有填 |
| Agent log 只有 `DRY-RUN` 沒有事件 | 沒有 `--from-beginning` | 加 `--from-beginning` 或往 log 檔追加新行 |
| Kibana 看不到資料 | es_sync_worker 延遲 | 等 10~30 秒後重新整理 |

---

## 停止平台

```bash
cd log-analysis-core
docker-compose down          # 停止但保留 volumes（資料不刪）
docker-compose down -v       # 停止並刪除所有 volumes（資料全清）
```
