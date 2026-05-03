# Smoke Test — XDR Customer Agent (Phase 1)

所有測試都在 `agent/` 目錄下執行。

---

## 什麼是 Log Rotation？

Web server 的 access log 如果一直寫進同一個檔案，幾天後檔案會大到幾 GB。
所以 Linux 系統（logrotate）會定期把舊檔「轉走」：

```
# logrotate 做的事（每天凌晨）：
mv /var/log/nginx/access.log   /var/log/nginx/access.log.1   # 舊檔改名
touch /var/log/nginx/access.log                              # 開一個新的空檔
nginx reload                                                  # nginx 開始寫新檔
```

**問題：** agent 用 `open()` 拿到的是舊檔的 file handle，
rotation 之後 nginx 寫進新檔，agent 還在讀舊檔 → 漏掉所有新 log。

**collector.py 的解法：**
- 記住目前開著的檔案的 **inode number**（OS 給每個檔案的唯一 ID，rename 不會改變它）
- 每次 `readline()` 回空字串時，檢查磁碟上 `access.log` 的 inode 是否跟記住的一樣
- 如果 inode 變了（或檔案大小比 offset 還小，代表 truncate）→ **關掉舊 handle，重新 open 新檔**
- 新檔從 offset 0 開始讀，一行都不漏

---

## 安裝依賴

```bash
pip3 install PyYAML requests
```

---

## Test 1 — Parser 單元測試

直接執行以下 Python 程式碼，驗證解析正確性（不需要任何設定檔）：

```python
# 可直接貼進 python3 互動模式，或存成 test_parser.py 執行

import json, sys
sys.path.insert(0, ".")          # 確保能 import 到 parser.py
from parser import parse_line

TENANT = "tenant-demo-001"

cases = [
    # (描述, 輸入行, 預期能解析)
    ("nginx combined 正常行",
     '203.0.113.45 - - [03/May/2026:10:30:15 +0000] "GET /api/v1/users HTTP/1.1" 200 1024 "https://example.com/" "Mozilla/5.0"',
     True),
    ("apache combined（有 auth user）",
     '198.51.100.7 - frank [03/May/2026:10:30:16 +0000] "POST /login HTTP/1.1" 401 212 "-" "curl/7.68.0"',
     True),
    ("bytes = - (zero)",
     '10.0.0.1 - - [03/May/2026:11:00:00 +0000] "HEAD / HTTP/1.1" 200 - "-" "-"',
     True),
    ("無 referer / UA（短格式）",
     '1.2.3.4 - - [03/May/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 512',
     True),
    ("空行",
     "",
     False),
    ("完全不合格的行",
     "this is not a log line",
     False),
]

PASS, FAIL = 0, 0
for desc, line, expect_ok in cases:
    result = parse_line(line, "nginx_combined", TENANT)
    ok = result is not None
    status = "PASS" if ok == expect_ok else "FAIL"
    if status == "FAIL":
        FAIL += 1
    else:
        PASS += 1
    print(f"[{status}] {desc}")
    if result:
        p = result["payload"]
        print(f"       ip={result['source_ip']}  ts={result['timestamp']}  "
              f"method={p['method']}  status={p['status']}  size={p['size']}")

print(f"\n{PASS} passed, {FAIL} failed")
```

**執行方式：**

```bash
cd agent
python3 test_parser.py
```

**預期輸出：**

```
[PASS] nginx combined 正常行
[PASS] apache combined（有 auth user）
[PASS] bytes = - (zero)
[PASS] 無 referer / UA（短格式）
[PASS] 空行
[PASS] 完全不合格的行

6 passed, 0 failed
```

---

## Test 2 — Dry-run 端到端測試

### 2-1 建立測試設定檔與假 log

```bash
# 建立測試工作目錄
mkdir -p /tmp/xdr-test

# 建立 config
cat > /tmp/xdr-test/config.yaml << 'EOF'
tenant_id: "tenant-demo-001"
gateway_url: "http://localhost:80"
sources:
  - type: file
    path: /tmp/xdr-test/access.log
    format: nginx_combined
batch:
  flush_interval_sec: 180
  chunk_size: 5000
buffer:
  path: /tmp/xdr-test/buffer.db
  max_size_mb: 50
checkpoint:
  path: /tmp/xdr-test/checkpoint.json
logging:
  level: INFO
  path: /tmp/xdr-test/agent.log
EOF

# 寫入 2 筆假 log
cat > /tmp/xdr-test/access.log << 'EOF'
203.0.113.45 - - [03/May/2026:10:30:15 +0000] "GET /api/v1/users HTTP/1.1" 200 1024 "https://example.com/" "Mozilla/5.0"
198.51.100.7 - - [03/May/2026:10:30:16 +0000] "POST /login HTTP/1.1" 401 212 "-" "curl/7.68.0"
EOF
```

### 2-2 執行 dry-run

```bash
cd agent
python3 -u agent.py \
  --config /tmp/xdr-test/config.yaml \
  --dry-run \
  --from-beginning &

AGENT_PID=$!
sleep 2
kill $AGENT_PID
wait $AGENT_PID 2>/dev/null
```

**預期看到（stdout）：**

```
... INFO agent XDR Agent v0.1.0  config=...  dry_run=True  from_beginning=True
... INFO agent DRY-RUN: events printed to stdout, not sent to gateway
{"tenant_id": "tenant-demo-001", "timestamp": "2026-05-03T10:30:15+00:00", "source_ip": "203.0.113.45", ...}
{"tenant_id": "tenant-demo-001", "timestamp": "2026-05-03T10:30:16+00:00", "source_ip": "198.51.100.7", ...}
```

---

## Test 3 — Checkpoint 斷點續傳測試

驗證 agent 重啟後不重送、也不漏送。

```bash
# 步驟 1：清掉舊 checkpoint，寫 3 筆 log
rm -f /tmp/xdr-test/checkpoint.json
cat > /tmp/xdr-test/access.log << 'EOF'
1.1.1.1 - - [03/May/2026:10:00:00 +0000] "GET /a HTTP/1.1" 200 100 "-" "-"
2.2.2.2 - - [03/May/2026:10:00:01 +0000] "GET /b HTTP/1.1" 200 200 "-" "-"
3.3.3.3 - - [03/May/2026:10:00:02 +0000] "GET /c HTTP/1.1" 200 300 "-" "-"
EOF

# 步驟 2：啟動 agent（--from-beginning 讀全部），讓它讀完後停止
python3 -u agent.py \
  --config /tmp/xdr-test/config.yaml \
  --dry-run \
  --from-beginning &
AGENT_PID=$!
sleep 2
kill $AGENT_PID
wait $AGENT_PID 2>/dev/null

echo "=== checkpoint 內容 ==="
cat /tmp/xdr-test/checkpoint.json

# 步驟 3：追加第 4 筆 log
echo '4.4.4.4 - - [03/May/2026:10:00:03 +0000] "GET /d HTTP/1.1" 200 400 "-" "-"' \
  >> /tmp/xdr-test/access.log

# 步驟 4：重啟 agent（不加 --from-beginning，從 checkpoint 續傳）
echo ""
echo "=== 第二次啟動，應只看到 /d 這筆 ==="
python3 -u agent.py \
  --config /tmp/xdr-test/config.yaml \
  --dry-run &
AGENT_PID=$!
sleep 2
kill $AGENT_PID
wait $AGENT_PID 2>/dev/null
```

**預期：** 第二次啟動只印出 `4.4.4.4` 這筆，不重印前 3 筆。

---

## Test 4 — Log Rotation 測試

驗證 collector 在 log rotation 後能自動切換到新檔。

```bash
# 步驟 1：準備乾淨環境
rm -f /tmp/xdr-test/checkpoint.json
printf '10.0.0.1 - - [03/May/2026:10:00:00 +0000] "GET /before-rotation HTTP/1.1" 200 111 "-" "-"\n' \
  > /tmp/xdr-test/access.log

# 步驟 2：啟動 agent（持續跑）
python3 -u agent.py \
  --config /tmp/xdr-test/config.yaml \
  --dry-run \
  --from-beginning &
AGENT_PID=$!

sleep 1   # 等 agent 讀完 /before-rotation 那筆

# 步驟 3：模擬 logrotate
mv /tmp/xdr-test/access.log /tmp/xdr-test/access.log.1
touch /tmp/xdr-test/access.log

sleep 1   # 等 agent 偵測到 inode 改變

# 步驟 4：往新檔寫一筆
printf '10.0.0.2 - - [03/May/2026:10:01:00 +0000] "GET /after-rotation HTTP/1.1" 200 222 "-" "-"\n' \
  >> /tmp/xdr-test/access.log

sleep 1   # 等 agent 讀到新行

kill $AGENT_PID
wait $AGENT_PID 2>/dev/null
```

**預期 stdout 看到兩筆（順序）：**
1. `"url": "/before-rotation"` — rotation 前
2. `"url": "/after-rotation"` — rotation 後，agent 自動切換新檔讀到

**預期 INFO log 看到：**
```
collector rotation detected (inode changed): /tmp/xdr-test/access.log
collector opened /tmp/xdr-test/access.log (inode=<新號> offset=0)
```

---

## 清理測試資料

```bash
rm -rf /tmp/xdr-test
```
