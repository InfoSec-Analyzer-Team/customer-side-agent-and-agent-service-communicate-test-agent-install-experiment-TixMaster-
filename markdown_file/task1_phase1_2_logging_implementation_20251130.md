# Task 1 - Phase 1 & 2: 日誌系統與 Crash API 實作報告

## 📅 實作日期
2025-11-30

## ✅ 完成項目

### Phase 1: 後端日誌系統建置
- ✅ 安裝 winston logging 套件
- ✅ 建立結構化日誌配置檔案 `backend/config/logger.js`
- ✅ 建立 `backend/logs` 目錄
- ✅ 整合 logger middleware 到 `backend/server.js`
- ✅ 修改所有主要 API 路由加入日誌
- ✅ 測試日誌輸出（Console + File）

### Phase 2: Crash API 實作
- ✅ 建立 `POST /api/crash` 端點
- ✅ 實作伺服器故意當機邏輯
- ✅ 加入錯誤日誌記錄

---

## 🔧 技術實作細節

### 1. Logger 配置 (`backend/config/logger.js`)

#### 1.1 日誌格式
採用 **JSON 結構化日誌**，包含以下欄位：

| 欄位 | 說明 | 範例 |
|------|------|------|
| `timestamp` | 時間戳記 | `2025-11-30 03:49:48` |
| `level` | 日誌等級 | `info`, `error`, `warn` |
| `message` | 日誌訊息 | `Incoming request` |
| `requestId` | Correlation ID | `1764445788376-aw0na8t2h` |
| `userId` | 使用者 ID | `anonymous` 或實際 user ID |
| `method` | HTTP Method | `GET`, `POST` |
| `path` | 請求路徑 | `/api/orders` |
| `ip` | 客戶端 IP | `::1` |
| `service` | 服務名稱 | `tixmaster-api` |
| `environment` | 環境 | `development` / `production` |

#### 1.2 輸出目標（Transports）

**Console 輸出**（開發環境友善格式）：
```
2025-11-30 03:49:48 [info]: Incoming request {"requestId":"...","userId":"anonymous",...}
```

**檔案輸出**（JSON 格式）：
- `logs/combined.log` - 所有日誌
- `logs/error.log` - 僅錯誤日誌

#### 1.3 Correlation ID 生成

每個 HTTP 請求自動產生唯一的 Request ID：

```javascript
function generateRequestId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
```

格式：`時間戳-隨機字串`
範例：`1764445788376-aw0na8t2h`

#### 1.4 Request Logger Middleware

自動為每個請求記錄：
- **請求開始**：記錄 method, url, userAgent, query
- **請求完成**：記錄 statusCode, duration
- **自動分級**：
  - `5xx` → `error`
  - `4xx` → `warn`
  - `2xx/3xx` → `info`

```javascript
logger.middleware = (req, res, next) => {
    req.id = req.headers['x-request-id'] || generateRequestId();
    const requestLogger = logger.createRequestLogger(req);

    requestLogger.info('Incoming request', { method, url, userAgent, query });

    res.on('finish', () => {
        const duration = Date.now() - startTime;
        const logLevel = res.statusCode >= 500 ? 'error' :
                        res.statusCode >= 400 ? 'warn' : 'info';
        requestLogger.log(logLevel, 'Request completed', { statusCode, duration });
    });

    req.logger = requestLogger;
    next();
};
```

---

### 2. Server.js 整合

#### 2.1 Middleware 順序

```javascript
app.use(express.json());              // 1. Body Parser
app.use(express.urlencoded());        // 2. URL Encoded Parser
app.use(session({ ... }));            // 3. Session
app.use(passport.initialize());       // 4. Passport Init
app.use(passport.session());          // 5. Passport Session
app.use(logger.middleware);           // 6. Logger (在所有路由之前)
app.use(featureFlagsMiddleware);      // 7. Feature Flags
app.use('/api/users', usersRouter);   // 8. Routes
app.use(errorHandler);                // 9. Error Handler (最後)
```

#### 2.2 Console.log 替換

所有 `console.log` / `console.error` / `console.warn` 已替換為 `logger` 方法：

**修改前：**
```javascript
console.log('[static] Found index.html in', path);
console.error('Failed to initialize feature flags:', error);
```

**修改後：**
```javascript
logger.info('[static] Found index.html in ${c}');
logger.error('Failed to initialize feature flags', { error: error.message, stack: error.stack });
```

---

### 3. 路由檔案整合

#### 3.1 OAuth 路由 (`routes/oauth.js`)

```javascript
const logger = require('../config/logger');

router.get('/callback', (req, res, next) => {
    req.logger.info('[Auth0] /auth/callback query', { query: req.query });
    // ...
});

router.get('/logout', (req, res) => {
    req.logout((err) => {
        if (err) {
            req.logger.error('❌ 登出錯誤', { error: err.message, stack: err.stack });
            return res.status(500).json({ error: 'Logout failed' });
        }
        req.logger.info('👋 使用者登出');
        res.json({ message: 'Logged out successfully' });
    });
});
```

#### 3.2 Analytics 路由 (`routes/analytics.js`)

```javascript
router.get('/metrics', async (req, res, next) => {
    try {
        const { start_date, end_date } = req.query;
        req.logger.info('[Analytics Metrics] Calculating metrics', { start_date, end_date });

        // ... 查詢邏輯 ...

        req.logger.info('[Analytics Metrics] H1 Results', { h1Count: h1Result.rows.length });
        res.json({ ... });
    } catch (err) {
        req.logger.error('[Analytics Metrics] Error', { error: err.message, stack: err.stack });
        next(err);
    }
});
```

#### 3.3 Feature Flags 路由 (`routes/featureFlags.js`)

```javascript
router.put('/:key', authenticateToken, checkPermission(PERMISSIONS.MANAGE_FEATURE_FLAGS),
    async (req, res, next) => {
        const { key } = req.params;
        const { enabled } = req.body;

        req.logger.info(`[FeatureFlags API] PUT /${key}`, { key, enabled, type: typeof enabled });

        if (typeof enabled !== 'boolean') {
            req.logger.error(`[FeatureFlags API] Invalid type for enabled`,
                { key, type: typeof enabled, value: enabled });
            return res.status(400).json({ error: 'enabled must be a boolean value' });
        }

        // ... 更新邏輯 ...

        req.logger.info(`[FeatureFlags API] Successfully updated`, { key, updatedFlag });
        res.json(updatedFlag);
    }
);
```

---

### 4. Crash API 實作

#### 4.1 端點定義

**路徑：** `POST /api/crash`
**用途：** 測試監控系統、日誌系統、警報系統

#### 4.2 實作邏輯

```javascript
app.post('/api/crash', (req, res) => {
    logger.error('💥 CRASH API called - Server will crash intentionally', {
        endpoint: '/api/crash',
        method: 'POST',
        timestamp: new Date().toISOString()
    });

    // 延遲 100ms 讓 log 能寫入檔案
    setTimeout(() => {
        process.exit(1);  // 強制退出程式（exit code 1 = 錯誤）
    }, 100);

    res.status(200).json({
        message: 'Server crashing...',
        note: 'This is intentional for monitoring testing'
    });
});
```

#### 4.3 設計考量

1. **日誌優先寫入**：延遲 100ms 確保 winston 有時間將錯誤日誌寫入檔案
2. **Exit Code 1**：表示異常退出，監控系統可偵測
3. **明確記錄**：在日誌中標註這是故意的當機（`intentionally`）
4. **HTTP 200 回應**：雖然伺服器會當機，但這是預期行為

---

## 📊 測試結果

### 日誌輸出範例

#### Console 輸出（開發模式）
```
2025-11-30 03:49:48 [info]: 🚀 TixMaster API server running on http://localhost:3000
2025-11-30 03:49:48 [info]: 📊 Health check: http://localhost:3000/health
2025-11-30 03:49:48 [info]: 💥 Crash API: http://localhost:3000/api/crash (POST)
2025-11-30 03:49:48 [info]: Incoming request {"requestId":"1764445786415-kun3i004n","userId":"anonymous","method":"GET","path":"/health","ip":"::1"}
2025-11-30 03:49:48 [info]: Request completed {"requestId":"1764445786415-kun3i004n","statusCode":200,"duration":"1893ms"}
```

#### 檔案輸出（`logs/combined.log`）
```json
{"level":"info","message":"🚀 TixMaster API server running on http://localhost:3000","service":"tixmaster-api","environment":"development","timestamp":"2025-11-30 03:49:48"}
{"level":"info","message":"Incoming request","requestId":"1764445786415-kun3i004n","userId":"anonymous","method":"GET","path":"/health","ip":"::1","service":"tixmaster-api","environment":"development","url":"/health","userAgent":"Mozilla/5.0...","query":{},"timestamp":"2025-11-30 03:49:48"}
{"level":"info","message":"Request completed","requestId":"1764445786415-kun3i004n","userId":"anonymous","method":"GET","path":"/health","ip":"::1","service":"tixmaster-api","environment":"development","statusCode":200,"duration":"1893ms","timestamp":"2025-11-30 03:49:48"}
```

### 驗證項目

✅ **Level 正確分類**
- `info` - 正常請求、伺服器啟動
- `warn` - 4xx 錯誤、配置警告
- `error` - 5xx 錯誤、異常

✅ **Timestamp 格式正確**
- 格式：`YYYY-MM-DD HH:mm:ss`
- 範例：`2025-11-30 03:49:48`

✅ **UserID 正確記錄**
- 未登入：`anonymous`
- 已登入：實際 user ID（由 JWT token 提取）

✅ **Request ID (Correlation ID) 正確產生**
- 每個請求唯一
- 格式：`timestamp-randomstring`
- 可用於追蹤同一請求的所有日誌

✅ **JSON 格式正確**
- 可被日誌分析工具解析
- 結構化資料便於查詢

---

## 🎯 符合任務要求

### 開發者角色需求

| 需求 | 實作狀態 | 說明 |
|------|---------|------|
| Structured logs | ✅ 完成 | JSON 格式，包含所有必要欄位 |
| Severity levels | ✅ 完成 | info / warn / error 自動分級 |
| Correlation IDs | ✅ 完成 | 每個請求唯一 Request ID |
| Logging format 說明 | ✅ 完成 | 本文件詳細記錄 |
| Error handling strategy | ✅ 完成 | 統一使用 req.logger，錯誤包含 stack trace |

### 日誌系統設計選擇說明

#### 1. **為什麼選擇 Winston？**
- ✅ 成熟穩定，業界標準
- ✅ 支援多種 transports（Console, File, Database, Cloud）
- ✅ 支援自訂格式（JSON, 彩色 Console）
- ✅ 效能優異，非同步寫入
- ✅ 社群活躍，文件完整

#### 2. **Correlation ID 設計**
- **用途**：追蹤單一請求在系統中的完整生命週期
- **格式**：`timestamp-randomstring`
- **優點**：
  - 唯一性高（時間戳 + 隨機字串）
  - 可排序（依時間戳）
  - 易讀（可直接看出請求時間）
- **使用場景**：
  - 前端可透過 `X-Request-ID` header 傳入自己的 ID
  - 後端自動產生 ID 並附加到所有該請求的日誌
  - 可串聯前後端、微服務之間的請求鏈

#### 3. **錯誤處理策略**
1. **路由層級錯誤處理**：
   ```javascript
   try {
       // 業務邏輯
   } catch (err) {
       req.logger.error('Operation failed', {
           error: err.message,
           stack: err.stack
       });
       next(err);  // 傳給全域錯誤處理器
   }
   ```

2. **全域錯誤處理器**（`middleware/errorHandler.js`）：
   - 統一格式回傳錯誤
   - 生產環境不暴露敏感資訊
   - 自動記錄到 `error.log`

3. **非同步錯誤處理**：
   - 使用 `try-catch` 包裹 async/await
   - 避免 unhandled promise rejection

#### 4. **效能考量**
- ✅ 非同步寫入檔案（不阻塞主線程）
- ✅ 分離檔案（combined.log vs error.log）
- ✅ 可設定日誌等級（生產環境只記錄 warn/error）
- ✅ 日誌輪轉（未來可加入 winston-daily-rotate-file）

---

## 📁 修改檔案清單

### 新增檔案
1. `backend/config/logger.js` - Logger 配置
2. `backend/logs/combined.log` - 所有日誌
3. `backend/logs/error.log` - 錯誤日誌

### 修改檔案
1. `backend/server.js`
   - 引入 logger
   - 加入 logger.middleware
   - 替換所有 console 為 logger
   - 新增 `/api/crash` 端點

2. `backend/routes/oauth.js`
   - 引入 logger
   - 使用 req.logger 記錄 OAuth 流程

3. `backend/routes/analytics.js`
   - 引入 logger
   - 記錄 metrics 計算過程

4. `backend/routes/featureFlags.js`
   - 引入 logger
   - 記錄 feature flags 更新操作

---

## 🚀 下一步（Phase 3）

### Prometheus Metrics 收集

需要安裝：
```bash
npm install prom-client
```

需要實作：
1. ✅ HTTP 請求總數（counter）
2. ✅ HTTP 請求延遲（histogram）
3. ✅ 活躍請求數（gauge）
4. ✅ 錯誤率（counter）
5. ✅ `/metrics` 端點（供 Prometheus 抓取）

---

## 💡 可觀測性如何提升系統可靠性

### 1. **快速定位問題**
- **Correlation ID** 讓我們能追蹤單一請求的完整路徑
- **Structured logs** 可用工具快速查詢、過濾
- **範例**：使用者回報「訂單建立失敗」
  ```bash
  # 查詢特定使用者的所有錯誤
  grep '"userId":"user123"' logs/error.log | grep '"level":"error"'

  # 追蹤特定請求
  grep '"requestId":"1764445786415-kun3i004n"' logs/combined.log
  ```

### 2. **效能監控**
- **Duration 記錄**讓我們知道哪些請求特別慢
- **範例**：找出超過 2 秒的慢請求
  ```bash
  grep '"duration"' logs/combined.log | grep -E '"duration":"[2-9][0-9]{3}ms"'
  ```

### 3. **安全審計**
- **IP 記錄**可偵測異常來源
- **UserID 記錄**可追蹤使用者行為
- **範例**：偵測同一 IP 大量失敗請求（可能是攻擊）

### 4. **錯誤趨勢分析**
- 可統計錯誤頻率、類型
- 可建立告警規則（如：5xx 錯誤率超過 1%）

### 5. **Crash API 的價值**
- 測試監控系統是否正常運作
- 測試日誌是否正確記錄當機前的狀態
- 測試自動重啟機制（如 PM2、Docker restart policy）

---

## 📸 建議截圖項目

### 日誌截圖
- [ ] Terminal 啟動畫面（顯示 logger 初始化）
- [ ] Terminal 請求日誌（彩色輸出）
- [ ] `logs/combined.log` 內容（JSON 格式）
- [ ] `logs/error.log` 內容（錯誤日誌）

### Crash API 測試
- [ ] 使用 Postman/Thunder Client 呼叫 `/api/crash`
- [ ] Terminal 顯示當機前的錯誤日誌
- [ ] `logs/error.log` 記錄的當機日誌

---

## ✅ 總結

**Phase 1 & 2 已完成**：
- ✅ Winston 日誌系統完整建置
- ✅ JSON 結構化日誌（Level, Timestamp, UserID, Request ID）
- ✅ Correlation ID 自動產生
- ✅ Request/Response 自動記錄
- ✅ 所有路由整合 logger
- ✅ Crash API 實作完成
- ✅ 測試通過

**符合任務要求**：
- ✅ Structured logs with severity levels
- ✅ Correlation IDs for request tracing
- ✅ Error handling strategy documented
- ✅ Logging format explained

**準備進入 Phase 3**：Prometheus Metrics 收集
