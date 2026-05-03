# Customer Agent 設計與需求文件

**版本：** v0.1 (Phase 1 — 本地測試)
**日期：** 2026-05-03
**狀態：** Draft

---

## 1. 背景與目標

本平台為第三方 Web Server Log 分析服務。客戶需要在自己的伺服器上部署一個輕量 Agent，將 Web Server 的 access log 透過 HTTPS 即時傳送至本平台的 Gateway，由平台負責後續的特徵萃取、ML 分析與威脅警示。

**Phase 1 目標（本文件範圍）：**
- Agent 能讀取本地 Web Server log 檔案
- 解析後透過 HTTP POST 傳送至平台 Gateway（本地測試）
- 平台端可在 Kafka / Elasticsearch / Kibana 看到資料流入
- 不含 TLS / API 金鑰認證（留 Phase 2）
- 不含平台端特徵萃取（留後續 Sprint）

---

## 2. 系統架構

### 2.1 整體資料流

```
客戶端 (Customer Server)                      平台端 (Log Analysis Platform)
┌─────────────────────────────────┐         ┌──────────────────────────────────────┐
│                                 │         │                                      │
│  /var/log/nginx/access.log      │         │  Nginx (:80)                         │
│          │                      │         │    │ upstream round-robin            │
│          │ tail / inotify       │         │    ▼                                 │
│          ▼                      │  HTTP   │  Gateway Cluster                     │
│  ┌───────────────────┐          │ ──────► │  (gateway1/2/3 :8090)                │
│  │  Log Collector    │  POST    │         │    │ FastAPI                         │
│  │  + Parser         │  batch   │         │    │ validate + produce              │
│  └───────────────────┘          │         │    ▼                                 │
│          │                      │         │  Redpanda (raw-logs topic)           │
│  ┌───────────────────┐          │         │    │                                 │
│  │  Local WAL Buffer │          │         │    ▼                                 │
│  │  (SQLite)         │          │         │  Log Processor → ML Worker           │
│  └───────────────────┘          │         │    │                                 │
│          │                      │         │    ▼                                 │
│  ┌───────────────────┐          │         │  PostgreSQL + Elasticsearch          │
│  │  Batch Sender     │          │         │    │                                 │
│  │  + Retry          │          │         │    ▼                                 │
│  └───────────────────┘          │         │  Kibana (可視化)                      │
│                                 │         │                                      │
│  config.yaml                    │         └──────────────────────────────────────┘
└─────────────────────────────────┘
```

### 2.2 Agent 內部元件

```
                  ┌─────────────────────────────────────────┐
                  │              XDR Agent                  │
                  │                                         │
  log file ──────►│  FileCollector                          │
                  │    - inotify / polling 監聽新增行        │
                  │    - checkpoint (inode + offset)        │
                  │          │                              │
                  │          ▼                              │
                  │  LogParser                              │
                  │    - 解析 nginx / apache combined       │
                  │    - 輸出標準化 dict                    │
                  │    - 填入 tenant_id / timestamp         │
                  │          │                              │
                  │          ▼                              │
                  │  LocalBuffer (SQLite WAL)               │
                  │    - 暫存待傳 events                    │
                  │    - 斷線時不丟資料                     │
                  │          │                              │
                  │          ▼                              │
                  │  BatchSender                            │
                  │    - 每 N 筆 或 每 T 秒 flush           │
                  │    - POST /api/v1/ingest                │
                  │    - 指數退避重試                       │
                  │          │                              │
                  └──────────┼──────────────────────────────┘
                             │ HTTPS POST
                             ▼
                       Gateway API
```

---

## 3. Gateway API 介面規格（現有）

Agent 必須對應現有 Gateway 的介面，**不允許為了 Agent 修改 Gateway 介面**（Phase 1）。

### 3.1 端點

```
POST http://<gateway_host>/api/v1/ingest
Content-Type: application/json
```

### 3.2 Request Body 欄位

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `tenant_id` | string | **必填** | 平台分配的租戶識別碼 |
| `timestamp` | string | **必填** | 事件時間，ISO 8601 或 `YYYY-MM-DD HH:MM:SS` |
| `source_ip` | string | 建議填 | 請求來源 IP（Gateway 轉換為 `source_ip` 欄位） |
| `event_type` | string | 否 | 預設 `"web_access"`，heartbeat 等特殊事件填對應值 |
| `user_agent` | string | 否 | HTTP User-Agent 字串 |
| `payload` | string / object | 否 | 結構化的額外資訊（可放 method, status, url 等） |
| `raw_payload` | string | 建議填 | **原始 log 行的完整文字**，平台後續特徵萃取用 |

> **設計決策：** 特徵萃取（`has_sql_injection`、`ip_type`、`is_bot` 等）由平台端 `log_processor` 負責，Agent 不需計算。Agent 只需填入能從 raw log 直接讀取的基本欄位，並完整保留 `raw_payload`。

### 3.3 Request 限制

| 端點 | 項目 | 限制 | 環境變數 |
|------|------|------|---------|
| 單筆 `/ingest` | Body 大小 | ≤ 1 MB | `MAX_INGEST_BODY_BYTES` |
| 批次 `/ingest/batch` | Body 大小 | ≤ 10 MB（可調整） | `MAX_BATCH_BODY_BYTES` |
| 批次 `/ingest/batch` | 單次最多筆數 | ≤ 5,000 筆 | `MAX_BATCH_SIZE` |
| 兩者 | Content-Type | 必須為 `application/json` | — |

> **Agent 分 chunk 策略：** Agent 每 3 分鐘 flush 一次，若累積筆數超過 5,000 則自動切成多次 POST，每次 ≤ 5,000 筆。

### 3.4 Response

**單筆 `/ingest`：**

| HTTP Code | 意義 | Agent 行為 |
|-----------|------|-----------|
| `200` | 成功入隊 | 從 buffer 刪除 |
| `400` | JSON 格式錯誤 / 缺必填欄位 | 丟棄，不重試 |
| `413` | 超過 1 MB | 丟棄，不重試 |
| `415` | Content-Type 錯誤 | 修正後重試 |
| `503` | Kafka 連線失敗 | 保留 buffer，指數退避後重試 |

**批次 `/ingest/batch`：**

| HTTP Code | 意義 | Agent 行為 |
|-----------|------|-----------|
| `200` | `{"status":"success","queued":N,"failed":M}` — 成功入隊 N 筆，M 筆 schema 錯誤已進 DLQ | 從 buffer 刪除整批 |
| `400` | body 格式錯誤 / events 全數 schema 失敗 | 丟棄，不重試 |
| `413` | 超過 10 MB | 縮小 chunk 後重試 |
| `503` | Kafka 全數失敗 | 保留 buffer，指數退避後重試 |

### 3.5 範例 Payload

```json
{
  "tenant_id": "tenant-demo-001",
  "timestamp": "2026-05-03T10:30:15.000Z",
  "source_ip": "203.0.113.45",
  "event_type": "web_access",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
  "payload": {
    "method": "GET",
    "url": "/api/v1/users",
    "status": 200,
    "size": 1024,
    "referer": "https://example.com/"
  },
  "raw_payload": "203.0.113.45 - - [03/May/2026:10:30:15 +0000] \"GET /api/v1/users HTTP/1.1\" 200 1024 \"https://example.com/\" \"Mozilla/5.0...\""
}
```

**批次 `/api/v1/ingest/batch` Payload 範例：**

```json
{
  "events": [
    {
      "tenant_id": "tenant-demo-001",
      "timestamp": "2026-05-03T10:30:15.000Z",
      "source_ip": "203.0.113.45",
      "event_type": "web_access",
      "user_agent": "Mozilla/5.0 ...",
      "payload": {"method": "GET", "url": "/api/v1/users", "status": 200, "size": 1024},
      "raw_payload": "203.0.113.45 - - [03/May/2026:10:30:15 +0000] \"GET /api/v1/users HTTP/1.1\" 200 1024"
    },
    {
      "tenant_id": "tenant-demo-001",
      "timestamp": "2026-05-03T10:30:16.000Z",
      "source_ip": "198.51.100.7",
      "event_type": "web_access",
      "payload": {"method": "POST", "url": "/login", "status": 401, "size": 212},
      "raw_payload": "198.51.100.7 - - [03/May/2026:10:30:16 +0000] \"POST /login HTTP/1.1\" 401 212"
    }
  ]
}
```

**批次回應範例：**

```json
{"status": "success", "queued": 2, "failed": 0}
```

---

## 4. 功能需求 (Functional Requirements)

### FR-1 Log 來源讀取
- **FR-1.1** Agent 必須支援從本地檔案路徑讀取 log（`file` source type）
- **FR-1.2** 必須支援 log rotation（檔案被 rename/truncate 後能自動重新開啟）
- **FR-1.3** 啟動後必須從上次中斷的位置繼續讀取，不重送也不漏送（checkpoint 機制）
- **FR-1.4** 支援 glob pattern，例如 `/var/log/nginx/*.log`

### FR-2 Log 解析
- **FR-2.1** 必須支援 Nginx combined log format（Phase 1 最低要求）
- **FR-2.2** 必須支援 Apache combined log format
- **FR-2.3** 解析失敗的行應記錄到 Agent 本地 error log，**不應中斷整體運作**
- **FR-2.4** 解析後填入標準化欄位，`raw_payload` 必須保留原始行文字

### FR-3 本地緩衝
- **FR-3.1** 必須有本地 WAL（Write-Ahead Log），防止網路斷線時資料遺失
- **FR-3.2** Buffer 超過設定上限時，丟棄最舊的資料（FIFO），並記錄 warning
- **FR-3.3** Agent 重啟後，Buffer 中未送出的資料必須繼續傳送

### FR-4 傳送
- **FR-4.1** 主要使用 `POST /api/v1/ingest/batch`，每次帶最多 5,000 筆事件
- **FR-4.2** 預設每 **3 分鐘** flush 一次；若 buffer 累積筆數達 chunk 上限則提前 flush
- **FR-4.3** 單次 POST 筆數超過 5,000 時，Agent 自動切成多次請求後依序傳送
- **FR-4.4** 收到 `200`（`queued > 0`）才從 buffer 刪除整批
- **FR-4.5** 遇到 `503` 必須以指數退避重試（初始 1s，最大 60s，最多 N 次可設定）
- **FR-4.6** 遇到 `400` / `413` 必須丟棄，不重試

### FR-5 設定
- **FR-5.1** 所有設定必須從 `config.yaml` 讀取
- **FR-5.2** 敏感設定（`api_key`，Phase 2）支援從環境變數覆蓋

### FR-6 健康與可觀測性
- **FR-6.1** Agent 啟動時印出版本、config 路徑、監聽的 log 路徑
- **FR-6.2** 每次 flush 成功 / 失敗都記錄 structured log（送出筆數、耗時、HTTP 狀態）
- **FR-6.3** 提供 `--dry-run` 模式：解析 log 但不實際傳送，用於本地測試驗證

---

## 5. 非功能需求 (Non-Functional Requirements)

| 類別 | 需求 |
|------|------|
| **效能** | 單核 CPU 下處理吞吐量 ≥ 5,000 行/秒（解析 + 入 buffer） |
| **延遲** | log 產生到抵達 Gateway ≤ flush_interval_sec + 網路傳輸時間（預設 3 分鐘） |
| **資源** | 常駐記憶體 ≤ 100 MB；CPU idle 時 ≤ 1% |
| **可靠性** | 網路中斷 ≤ 30 分鐘後恢復，資料不遺失（buffer 足夠） |
| **相容性** | Python 3.10+；可打包為單一 Docker image |
| **可部署性** | 支援 systemd service 與 Docker container 兩種部署方式 |

---

## 6. 設定規格 (config.yaml)

```yaml
# ─────────────────────────────────────
# XDR Agent Configuration
# ─────────────────────────────────────

# 租戶識別（必填，由平台分配）
tenant_id: "tenant-demo-001"

# Gateway 位址（Phase 1：本地平台 stack）
gateway_url: "http://localhost:80"

# Phase 2 預留（目前可留空）
# api_key: ""

# ─── Log 來源 ───────────────────────
sources:
  - type: file
    path: /var/log/nginx/access.log
    format: nginx_combined
  # 可加多個來源：
  # - type: file
  #   path: /var/log/apache2/access.log
  #   format: apache_combined

# ─── 傳送批次設定 ────────────────────
batch:
  flush_interval_sec: 180  # 每 3 分鐘 flush 一次（可依流量調整）
  chunk_size: 5000         # 單次 POST 最多筆數，超過自動切多次請求

# ─── 本地緩衝 ────────────────────────
buffer:
  path: /var/lib/xdr-agent/buffer.db   # SQLite 檔案路徑
  max_size_mb: 200                     # 超過時丟棄最舊資料

# ─── 重試策略 ────────────────────────
retry:
  max_attempts: 10
  base_delay_sec: 1
  max_delay_sec: 60

# ─── Checkpoint ─────────────────────
checkpoint:
  path: /var/lib/xdr-agent/checkpoint.json

# ─── Agent 本身的 log ────────────────
logging:
  level: INFO              # DEBUG / INFO / WARNING / ERROR
  path: /var/log/xdr-agent/agent.log
```

---

## 7. 本地測試環境設置

### 7.1 平台端啟動

```bash
# 1. 在 log-analysis-core 目錄下
cp .env.example .env
# 編輯 .env，填入 POSTGRES_PASSWORD

# 2. 啟動整個平台 stack
docker-compose up -d

# 3. 確認 Gateway 健康
curl http://localhost:80/health
# 預期回應：healthy
```

### 7.2 手動驗證 Gateway（不需 Agent）

```bash
curl -X POST http://localhost:80/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo-001",
    "timestamp": "2026-05-03T10:00:00Z",
    "source_ip": "1.2.3.4",
    "event_type": "web_access",
    "raw_payload": "1.2.3.4 - - [03/May/2026:10:00:00 +0000] \"GET / HTTP/1.1\" 200 512"
  }'
# 預期：{"status": "success", "message": "Log queued"}
```

### 7.3 測試用 Nginx Log 產生器

若本機沒有 Nginx，可用 [tool_script/generate_stress_logs.py](../tool_script/generate_stress_logs.py) 產生模擬 log 檔案供 Agent 讀取。

### 7.4 Agent 連接本地平台

```yaml
# config.yaml（本地測試用）
tenant_id: "tenant-demo-001"
gateway_url: "http://localhost:80"
sources:
  - type: file
    path: /tmp/test-access.log
    format: nginx_combined
```

```bash
# 使用 --dry-run 先驗證解析正確性
python agent.py --config config.yaml --dry-run

# 實際傳送
python agent.py --config config.yaml
```

### 7.5 驗收確認清單

- [ ] Gateway 回傳 `200`，Agent log 顯示 flush 成功
- [ ] Redpanda Console（`http://localhost:18080`）的 `raw-logs` topic 有訊息流入
- [ ] Kibana（`http://localhost:5601`）可見新增的 log 資料
- [ ] 停止 Gateway（`docker-compose stop gateway1 gateway2 gateway3`）後 Agent 保留 buffer，恢復後自動補傳
- [ ] 使 log 檔案 rotate（`mv access.log access.log.1 && touch access.log`）後 Agent 能持續讀取新檔

---

## 8. 目錄結構建議

```
customer-agent/                  ← 獨立 repo 或本 repo 子目錄
├── agent.py                     ← 主程式入口
├── collector.py                 ← FileCollector（tail + checkpoint）
├── parser.py                    ← LogParser（nginx / apache）
├── buffer.py                    ← LocalBuffer（SQLite WAL）
├── sender.py                    ← BatchSender（HTTP + retry）
├── config.py                    ← Config loader（YAML）
├── config.yaml.example          ← 設定範本
├── requirements.txt
├── Dockerfile
└── xdr-agent.service            ← systemd unit file 範本
```

---

## 9. Phase 2 預留項目（本文件不實作）

| 項目 | 說明 |
|------|------|
| **TLS / HTTPS** | Gateway 前加 TLS termination，Agent 改用 `https://` |
| **API Key 認證** | Gateway 加 `Authorization: Bearer <key>` 驗證 middleware |
| **Batch Endpoint** | Gateway 新增 `POST /api/v1/ingest/batch` 減少 HTTP 連線數 |
| **平台端特徵萃取** | `log_processor` 整合 `feature_engineering.py` |
| **Rate Limiting** | Gateway 加 per-tenant rate limit（Redis sliding window） |
| **Agent 自動更新** | 平台推送 agent 版本號，客戶端自動 pull |

---

## 10. 開放問題 (Open Questions)

| # | 問題 | 影響 |
|---|------|------|
| OQ-1 | `tenant_id` 如何分配給客戶？是否有 onboarding API？ | Agent config 產生流程 |
| OQ-2 | Agent 要支援哪些 log format？除 nginx / apache 外有無其他需求？ | Parser 開發工作量 |
| OQ-3 | 客戶端 OS 需求？（純 Linux、還是也需要 Windows？） | 部署打包方式 |
| OQ-4 | 單一客戶預估最高 log 產生速率？（行/秒） | Buffer size & batch 參數預設值 |
