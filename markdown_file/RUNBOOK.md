# 📖 TixMaster RUNBOOK - 故障排除手冊

## 📋 目錄
1. [5xx 伺服器錯誤處理](#5xx-伺服器錯誤處理)
2. [Timeout 超時處理](#timeout-超時處理)
3. [資料庫連線失敗處理](#資料庫連線失敗處理)
4. [服務完全宕機處理](#服務完全宕機處理)
5. [高負載與效能問題](#高負載與效能問題)
6. [常用診斷指令](#常用診斷指令)

---

## 🚨 5xx 伺服器錯誤處理

### 症狀
- Grafana 顯示 5xx 錯誤率上升
- 使用者回報「伺服器錯誤」訊息
- Prometheus 警報: `HighErrorRate`

### 嚴重程度
- 🔴 **P0 (緊急)**: 錯誤率 > 5%
- 🟠 **P1 (高)**: 錯誤率 1-5%
- 🟡 **P2 (警告)**: 錯誤率 0.1-1%

---

### 📊 步驟 1: 確認問題範圍

#### 1.1 檢查錯誤率
```bash
# 查看 Grafana Dashboard
open http://localhost:3001

# 或使用 Prometheus 查詢
curl -s "http://localhost:9091/api/v1/query?query=rate(http_errors_total{status_code=~\"5..\"}[5m])"
```

#### 1.2 查看錯誤日誌
```bash
# 查看最近的錯誤日誌
cd backend
tail -f error.log | jq 'select(.level == "error")'

# 或查看最近 100 條錯誤
tail -100 combined.log | jq 'select(.level == "error")'

# 統計錯誤類型
cat error.log | jq -r '.message' | sort | uniq -c | sort -nr
```

#### 1.3 確認受影響的路由
```bash
# 查詢哪些路由錯誤最多
curl -s "http://localhost:9091/api/v1/query?query=sum(rate(http_errors_total{status_code=~\"5..\"}[5m]))by(route)" | jq
```

---

### 🔍 步驟 2: 診斷根本原因

#### 常見原因檢查清單

##### ✅ 2.1 資料庫連線問題
```bash
# 測試資料庫連線
cd backend
node check_db.js

# 查看資料庫連線數
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 檢查是否有長時間執行的查詢
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
```

**預期結果**:
- ✅ 資料庫連線成功
- ✅ 沒有長時間執行的查詢（< 5 秒）

**如果失敗**: 跳到 [資料庫連線失敗處理](#資料庫連線失敗處理)

##### ✅ 2.2 記憶體不足
```bash
# 檢查 Node.js 記憶體使用
curl -s http://localhost:3000/metrics | grep process_resident_memory_bytes

# 檢查系統記憶體
docker stats --no-stream

# 檢查是否有記憶體洩漏
# 觀察記憶體使用是否持續上升
watch -n 5 'curl -s http://localhost:3000/metrics | grep process_resident_memory_bytes'
```

**正常範圍**: < 200MB
**警告**: 200-500MB
**危險**: > 500MB

**解決方案**: 重啟服務
```bash
cd backend
npm restart
# 或
pm2 restart tixmaster-backend
```

##### ✅ 2.3 未處理的例外
```bash
# 搜尋 uncaught exception
cat error.log | jq 'select(.message | contains("uncaught"))'

# 查看 stack trace
cat error.log | jq -r 'select(.level == "error") | "\(.timestamp) - \(.message)\n\(.stack)"' | head -50
```

**解決方案**: 修復程式碼並部署

##### ✅ 2.4 第三方 API 失敗
```bash
# 檢查日誌中的外部 API 錯誤
cat combined.log | jq 'select(.message | contains("API")) | select(.level == "error")'

# 測試外部 API
curl -I https://api.external-service.com/health
```

**解決方案**:
- 啟用 Circuit Breaker
- 實作降級機制
- 聯絡第三方服務商

---

### 🛠️ 步驟 3: 緊急修復

#### 3.1 重啟服務（最快速的修復）
```bash
# 方法 1: npm restart
cd backend
npm restart

# 方法 2: PM2 restart
pm2 restart tixmaster-backend

# 方法 3: Docker restart
docker restart tixmaster-backend

# 驗證服務已恢復
curl http://localhost:3000/health
```

**預期結果**:
```json
{
  "status": "OK",
  "message": "TixMaster API is running"
}
```

#### 3.2 回滾到上一個版本
```bash
# 查看最近的 commit
git log --oneline -5

# 回滾到上一個版本
git revert HEAD
# 或
git reset --hard HEAD~1

# 重啟服務
npm restart
```

#### 3.3 啟用維護模式
```bash
# 建立維護頁面
echo '<!DOCTYPE html><html><body><h1>系統維護中</h1><p>預計 30 分鐘後恢復</p></body></html>' > frontend/maintenance.html

# 修改 Nginx 配置（如果使用）
# 或在 server.js 中加入維護模式
```

---

### 📝 步驟 4: 記錄與通知

#### 4.1 建立事件報告
```bash
# 建立事件記錄檔案
cat > incident_report_$(date +%Y%m%d_%H%M%S).md << 'EOF'
# Incident Report

**事件時間**: YYYY-MM-DD HH:MM
**嚴重程度**: P0 / P1 / P2
**影響範圍**: XX% 使用者
**錯誤率**: XX%
**持續時間**: XX 分鐘

## 症狀
- [描述使用者看到的問題]

## 根本原因
- [診斷出的根本原因]

## 解決方案
- [採取的修復措施]

## 預防措施
- [未來如何避免]

## Timeline
- HH:MM - 發現問題
- HH:MM - 開始診斷
- HH:MM - 確認根本原因
- HH:MM - 實施修復
- HH:MM - 問題解決

EOF
```

#### 4.2 通知利害關係人
```bash
# 發送通知到 Slack
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🔴 5xx 錯誤已解決",
    "attachments": [{
      "color": "good",
      "fields": [
        {"title": "錯誤率", "value": "0.1%", "short": true},
        {"title": "持續時間", "value": "15 分鐘", "short": true}
      ]
    }]
  }'
```

---

### 🔄 步驟 5: 後續追蹤

#### 5.1 監控恢復狀況
```bash
# 持續監控錯誤率（5 分鐘）
for i in {1..5}; do
  echo "=== Check $i/5 ==="
  curl -s "http://localhost:9091/api/v1/query?query=rate(http_errors_total{status_code=~\"5..\"}[1m])" | jq '.data.result[0].value[1]'
  sleep 60
done
```

#### 5.2 檢查 Error Budget
```bash
# 計算今日消耗的 Error Budget
# (假設目標是 99.9% 可用性)
echo "今日錯誤預算消耗: XX%"
```

---

## ⏱️ Timeout 超時處理

### 症狀
- 請求長時間沒有回應
- 使用者回報「載入緩慢」
- Grafana 顯示 P95 延遲 > 1000ms

### 嚴重程度
- 🔴 **P0**: P95 > 5000ms
- 🟠 **P1**: P95 > 2000ms
- 🟡 **P2**: P95 > 1000ms

---

### 📊 步驟 1: 確認延遲問題

#### 1.1 檢查回應時間
```bash
# 查看 P95 延遲
curl -s "http://localhost:9091/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_ms_bucket[5m]))by(le,route))" | jq

# 測試特定端點
time curl http://localhost:3000/api/events
```

#### 1.2 識別慢查詢
```bash
# 查看資料庫慢查詢
docker exec -it tixmaster-postgres psql -U postgres -c "
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query,
  state
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - pg_stat_activity.query_start > interval '1 second'
ORDER BY duration DESC;
"
```

---

### 🔍 步驟 2: 診斷原因

#### 2.1 資料庫查詢優化
```bash
# 分析慢查詢
docker exec -it tixmaster-postgres psql -U postgres -d tixmaster -c "
EXPLAIN ANALYZE
SELECT * FROM events WHERE category = 'concert';
"

# 檢查缺少的索引
docker exec -it tixmaster-postgres psql -U postgres -d tixmaster -c "
SELECT
  schemaname,
  tablename,
  indexname
FROM pg_indexes
WHERE schemaname = 'public';
"
```

**解決方案**: 建立索引
```sql
-- 為常用查詢建立索引
CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_tickets_event_id ON tickets(event_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

#### 2.2 N+1 查詢問題
```bash
# 檢查日誌中的多次查詢
cat combined.log | jq 'select(.message | contains("SELECT"))' | head -20
```

**解決方案**: 使用 JOIN 或 eager loading

#### 2.3 外部 API 延遲
```bash
# 測試外部 API 回應時間
time curl -I https://api.external-service.com/

# 檢查日誌中的外部 API 呼叫
cat combined.log | jq 'select(.message | contains("external")) | select(.duration > 1000)'
```

**解決方案**:
- 增加 timeout 設定
- 實作快取
- 使用非同步處理

---

### 🛠️ 步驟 3: 優化措施

#### 3.1 啟用快取
```javascript
// Redis 快取範例
const redis = require('redis');
const client = redis.createClient();

async function getCachedEvents() {
  const cached = await client.get('events');
  if (cached) return JSON.parse(cached);

  const events = await db.query('SELECT * FROM events');
  await client.setex('events', 300, JSON.stringify(events)); // 5 分鐘
  return events;
}
```

#### 3.2 增加資料庫連線池
```javascript
// config/database.js
const pool = new Pool({
  max: 20,  // 從 10 增加到 20
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});
```

#### 3.3 實作分頁
```javascript
// 限制查詢結果數量
app.get('/api/events', async (req, res) => {
  const page = req.query.page || 1;
  const limit = 20;
  const offset = (page - 1) * limit;

  const events = await db.query(
    'SELECT * FROM events LIMIT $1 OFFSET $2',
    [limit, offset]
  );

  res.json({ events, page, limit });
});
```

---

## 💾 資料庫連線失敗處理

### 症狀
- 錯誤訊息: "Connection refused" 或 "ECONNREFUSED"
- 所有 API 回應 500 錯誤
- 日誌顯示資料庫連線失敗

### 嚴重程度
- 🔴 **P0 (緊急)**: 完全無法連線

---

### 📊 步驟 1: 確認資料庫狀態

#### 1.1 檢查資料庫是否運行
```bash
# 檢查 Docker 容器
docker ps | grep postgres

# 檢查資料庫 logs
docker logs tixmaster-postgres --tail 50

# 嘗試連線
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT 1;"
```

**預期結果**:
```
 ?column?
----------
        1
```

#### 1.2 檢查網路連線
```bash
# 從 backend 容器測試連線
docker exec -it tixmaster-backend nc -zv postgres 5432

# 檢查環境變數
echo $DATABASE_URL
```

---

### 🛠️ 步驟 2: 修復措施

#### 2.1 資料庫未運行
```bash
# 啟動資料庫
docker start tixmaster-postgres

# 或使用 docker-compose
docker-compose up -d postgres

# 驗證
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT version();"
```

#### 2.2 資料庫連線數已滿
```bash
# 檢查當前連線數
docker exec -it tixmaster-postgres psql -U postgres -c "
SELECT count(*) as connections,
       max_connections
FROM pg_stat_activity,
     (SELECT setting::int as max_connections FROM pg_settings WHERE name = 'max_connections') as mc
GROUP BY max_connections;
"

# 關閉閒置連線
docker exec -it tixmaster-postgres psql -U postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '5 minutes';
"
```

#### 2.3 資料庫損壞
```bash
# 檢查資料庫完整性
docker exec -it tixmaster-postgres psql -U postgres -d tixmaster -c "
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;
"

# 從備份恢復（如果必要）
docker exec -i tixmaster-postgres psql -U postgres < backup.sql
```

#### 2.4 網路問題
```bash
# 重新建立網路
docker network ls
docker network inspect tixmaster_default

# 重啟所有容器
docker-compose restart
```

---

### 🔄 步驟 3: 預防措施

#### 3.1 設定連線池
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  max: 20,  // 最大連線數
  idleTimeoutMillis: 30000,  // 閒置逾時
  connectionTimeoutMillis: 2000,  // 連線逾時
});

// 處理錯誤
pool.on('error', (err) => {
  logger.error('Unexpected database error', { error: err.message });
});
```

#### 3.2 實作健康檢查
```javascript
app.get('/health/db', async (req, res) => {
  try {
    const result = await pool.query('SELECT 1');
    res.json({ status: 'healthy', database: 'connected' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', database: 'disconnected' });
  }
});
```

#### 3.3 設定自動備份
```bash
# 建立備份腳本
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec tixmaster-postgres pg_dump -U postgres tixmaster > backups/tixmaster_$DATE.sql
# 保留最近 7 天的備份
find backups/ -name "tixmaster_*.sql" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# 設定 crontab（每天凌晨 2 點備份）
crontab -e
# 加入：
# 0 2 * * * /path/to/backup_db.sh
```

---

## 🔥 服務完全宕機處理

### 症狀
- 無法存取任何端點
- Prometheus Target 顯示 DOWN
- 健康檢查失敗

---

### 🚨 緊急檢查清單（2 分鐘內完成）

```bash
# 1. 檢查服務是否運行
ps aux | grep node
docker ps | grep tixmaster

# 2. 檢查 port 是否被佔用
netstat -tulpn | grep :3000
lsof -i :3000

# 3. 檢查最近的日誌
tail -50 error.log

# 4. 嘗試重啟
npm restart
# 或
docker restart tixmaster-backend

# 5. 驗證恢復
curl http://localhost:3000/health
```

---

### 📋 詳細診斷步驟

#### 1. 檢查程式當機原因
```bash
# 查看 crash log
cat error.log | grep -i "crash\|fatal\|killed"

# 檢查 OOM (Out of Memory)
dmesg | grep -i "out of memory"
docker logs tixmaster-backend | grep -i "oom"

# 檢查磁碟空間
df -h
```

#### 2. 檢查依賴服務
```bash
# 資料庫
curl http://localhost:5432
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT 1;"

# Redis (如果使用)
redis-cli ping

# 其他服務
docker ps -a
```

#### 3. 檢查環境變數
```bash
# 確認 .env 檔案存在
ls -la .env

# 檢查關鍵變數
echo $DATABASE_URL
echo $PORT
echo $NODE_ENV
```

---

### 🛠️ 修復步驟

```bash
# 步驟 1: 停止所有相關服務
pkill -f node
docker stop tixmaster-backend

# 步驟 2: 清理
rm -rf node_modules/.cache
npm cache clean --force

# 步驟 3: 重新安裝依賴（如果需要）
npm install

# 步驟 4: 啟動服務
npm start
# 或使用 PM2
pm2 start server.js --name tixmaster-backend

# 步驟 5: 驗證
curl http://localhost:3000/health
curl http://localhost:3000/metrics

# 步驟 6: 檢查監控
open http://localhost:3001  # Grafana
open http://localhost:9091  # Prometheus
```

---

## 📊 高負載與效能問題

### 症狀
- CPU 使用率 > 80%
- 記憶體使用率 > 85%
- 回應時間變慢
- 活躍請求數異常高

---

### 🔍 診斷步驟

```bash
# 1. 檢查系統資源
top
htop
docker stats

# 2. 檢查 Node.js 效能
node --prof server.js  # 生成效能分析檔
node --prof-process isolate-*.log > processed.txt

# 3. 檢查請求分佈
curl -s http://localhost:9091/api/v1/query?query='sum(rate(http_requests_total[1m]))by(route)' | jq

# 4. 檢查慢端點
cat combined.log | jq 'select(.duration > 1000) | {route, duration}' | head -20
```

---

### 🛠️ 優化措施

#### 1. 垂直擴展（增加資源）
```bash
# Docker 增加記憶體限制
docker update --memory 2g tixmaster-backend

# PM2 增加實例
pm2 scale tixmaster-backend +2
```

#### 2. 水平擴展（增加實例）
```bash
# 使用 PM2 Cluster Mode
pm2 start server.js -i max  # 使用所有 CPU 核心
```

#### 3. 實作 Rate Limiting
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 分鐘
  max: 100,  // 最多 100 個請求
  message: 'Too many requests from this IP'
});

app.use('/api/', limiter);
```

---

## 🛠️ 常用診斷指令

### 快速檢查腳本

建立一個快速診斷腳本：

```bash
cat > quick_check.sh << 'EOF'
#!/bin/bash

echo "=== TixMaster 快速診斷 ==="
echo ""

# 1. 服務狀態
echo "📊 服務狀態:"
curl -s http://localhost:3000/health | jq '.'
echo ""

# 2. 錯誤率
echo "❌ 5xx 錯誤率:"
curl -s "http://localhost:9091/api/v1/query?query=100*sum(rate(http_errors_total{status_code=~\"5..\"}[5m]))/sum(rate(http_requests_total[5m]))" | jq -r '.data.result[0].value[1]' | awk '{printf "%.2f%%\n", $1}'
echo ""

# 3. P95 延遲
echo "⏱️ P95 回應時間:"
curl -s "http://localhost:9091/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_ms_bucket[5m]))by(le))" | jq -r '.data.result[0].value[1]' | awk '{printf "%.2f ms\n", $1}'
echo ""

# 4. CPU 使用率
echo "💻 CPU 使用率:"
curl -s http://localhost:3000/metrics | grep process_cpu_user_seconds_total | tail -1
echo ""

# 5. 記憶體使用
echo "💾 記憶體使用:"
curl -s http://localhost:3000/metrics | grep process_resident_memory_bytes | tail -1 | awk '{print $2/1024/1024 " MB"}'
echo ""

# 6. 資料庫連線
echo "💾 資料庫狀態:"
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null || echo "無法連接"
echo ""

# 7. Docker 容器狀態
echo "🐳 Docker 容器:"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""

echo "=== 檢查完成 ==="
EOF

chmod +x quick_check.sh
```

使用方式：
```bash
./quick_check.sh
```

---

### 常用指令速查表

| 任務 | 指令 |
|------|------|
| 查看錯誤日誌 | `tail -f error.log \| jq` |
| 重啟服務 | `npm restart` 或 `pm2 restart tixmaster-backend` |
| 檢查資料庫 | `docker exec -it tixmaster-postgres psql -U postgres -c "SELECT 1;"` |
| 查看 metrics | `curl http://localhost:3000/metrics` |
| 測試健康檢查 | `curl http://localhost:3000/health` |
| 查看 Docker logs | `docker logs -f tixmaster-backend` |
| 檢查 port | `lsof -i :3000` |
| 查看 CPU/記憶體 | `docker stats --no-stream` |

---

## 📞 升級路徑

### 何時需要升級？

| 情況 | 升級對象 | 回應時間 |
|------|---------|---------|
| 無法在 30 分鐘內解決 | Tech Lead | 立即 |
| 影響 > 50% 使用者 | CTO | 立即 |
| 資料遺失風險 | DBA + CTO | 立即 |
| 安全問題 | Security Team | 立即 |

### 聯絡資訊

- **On-Call Engineer**: [Slack #oncall]
- **Tech Lead**: [手機號碼]
- **DBA**: [Email/Slack]
- **DevOps**: [Slack #devops]

---

## 📝 事後檢討 (Post-Mortem)

每次重大事件後，必須進行事後檢討：

### Post-Mortem Template

```markdown
# Post-Mortem: [事件標題]

**日期**: YYYY-MM-DD
**嚴重程度**: P0/P1/P2
**持續時間**: XX 分鐘
**影響範圍**: XX% 使用者

## 事件摘要
[簡述發生什麼事]

## Timeline
- HH:MM - 事件開始
- HH:MM - 發現問題
- HH:MM - 開始診斷
- HH:MM - 確認根本原因
- HH:MM - 實施修復
- HH:MM - 完全恢復

## 根本原因
[詳細說明根本原因]

## 影響
- 受影響使用者數: XX
- 損失交易數: XX
- Error Budget 消耗: XX%

## 解決方案
[描述如何修復]

## 學到的教訓
- [教訓 1]
- [教訓 2]

## 行動項目
- [ ] [預防措施 1] - [負責人] - [期限]
- [ ] [預防措施 2] - [負責人] - [期限]
- [ ] [流程改進] - [負責人] - [期限]
```

---

**RUNBOOK 版本**: 1.0
**最後更新**: 2025-11-30
**維護者**: TixMaster DevOps Team

**🆘 緊急聯絡**: [Slack #emergency] | [On-Call Phone]

--- 

🧪 測試 RUNBOOK
你可以實際測試這些診斷腳本：
# 1. 執行快速檢查
./quick_check.sh

# 2. 模擬 5xx 錯誤（觸發 crash API）
curl -X POST http://localhost:3000/api/crash

# 3. 觀察監控系統反應
# 前往 Grafana 查看錯誤率上升

# 4. 使用 RUNBOOK 修復
# 按照 RUNBOOK 的步驟重啟服務
Phase 9 完成！ 🎉 我們已經建立了完整的故障排除文件和診斷工具。現在團隊成員都能快速診斷和修復問題！ 接下來的 Phase:
Phase 10: 測試與截圖 📸
Phase 11: 文件整理 📚
Phase 12: 最終驗收 ✅