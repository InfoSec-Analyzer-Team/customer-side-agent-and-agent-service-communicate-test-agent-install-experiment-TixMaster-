# 🛠️ TixMaster 開發策略文件

## 📋 目錄
1. [Logging 策略](#logging-策略)
2. [Correlation ID 使用指南](#correlation-id-使用指南)
3. [錯誤處理策略](#錯誤處理策略)
4. [最佳實踐](#最佳實踐)

---

## 📝 Logging 策略

### 1. Logging 格式 - JSON 結構化日誌

我們使用 **Winston** 作為 logging 函式庫，採用 **JSON 格式** 的結構化日誌。

#### 為什麼使用 JSON 格式？

✅ **機器可讀**: 容易被 log aggregator (如 ELK, Loki) 解析
✅ **結構化**: 欄位明確，查詢方便
✅ **可擴展**: 容易添加新欄位
✅ **一致性**: 所有 log 格式統一

#### 標準 Log 格式

```json
{
  "level": "info",
  "message": "User login successful",
  "timestamp": "2025-11-30T10:30:45.123Z",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": 123,
  "service": "tixmaster-api",
  "environment": "production",
  "route": "/api/users/login",
  "method": "POST",
  "statusCode": 200,
  "duration": 45,
  "metadata": {
    "ip": "192.168.1.100",
    "userAgent": "Mozilla/5.0..."
  }
}
```

#### 必要欄位

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `level` | String | 日誌等級 | `info`, `warn`, `error` |
| `message` | String | 日誌訊息 | "User login successful" |
| `timestamp` | ISO 8601 | 時間戳記 | "2025-11-30T10:30:45.123Z" |
| `correlationId` | UUID | 追蹤 ID | "550e8400-..." |
| `service` | String | 服務名稱 | "tixmaster-api" |
| `environment` | String | 環境 | "development", "production" |

#### 選用欄位（依情境）

| 欄位 | 使用時機 | 範例 |
|------|---------|------|
| `userId` | 已登入用戶 | 123 |
| `route` | HTTP 請求 | "/api/users/login" |
| `method` | HTTP 請求 | "POST" |
| `statusCode` | HTTP 回應 | 200 |
| `duration` | 計時操作 | 45 (毫秒) |
| `error` | 錯誤情況 | { name, message, stack } |

---

### 2. Log Level 使用指南

#### Log Level 定義

| Level | 使用時機 | 範例 |
|-------|---------|------|
| **error** | 系統錯誤、例外狀況 | 資料庫連線失敗、未預期的錯誤 |
| **warn** | 潛在問題、降級服務 | API 回應變慢、快取失效 |
| **info** | 重要業務事件 | 用戶登入、訂單建立、付款成功 |
| **debug** | 除錯資訊 | 函式參數、查詢條件 |
| **verbose** | 詳細追蹤 | 每個步驟的細節 |

#### 使用範例

```javascript
const logger = require('./config/logger');

// ✅ ERROR - 系統錯誤
logger.error('Database connection failed', {
  error: err.message,
  stack: err.stack,
  dbHost: process.env.DATABASE_HOST
});

// ✅ WARN - 警告
logger.warn('API response time exceeds threshold', {
  route: '/api/events',
  duration: 1500,
  threshold: 1000
});

// ✅ INFO - 業務事件
logger.info('User logged in successfully', {
  userId: user.id,
  email: user.email,
  loginMethod: 'oauth-google'
});

// ✅ DEBUG - 除錯資訊
logger.debug('Fetching events from database', {
  query: { category: 'concert', limit: 10 }
});
```

---

### 3. 生產環境 vs 開發環境

#### 開發環境 (Development)
```javascript
{
  level: 'debug',  // 顯示 debug 和以上
  format: winston.format.combine(
    winston.format.colorize(),  // 彩色輸出
    winston.format.simple()     // 簡單格式，方便閱讀
  ),
  transports: [
    new winston.transports.Console()  // 只輸出到終端機
  ]
}
```

#### 生產環境 (Production)
```javascript
{
  level: 'info',  // 只顯示 info 和以上
  format: winston.format.json(),  // JSON 格式
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
}
```

---

### 4. 實作範例

#### Logger 配置 (config/logger.js)

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'tixmaster-api',
    environment: process.env.NODE_ENV || 'development'
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

module.exports = logger;
```

#### Logging Middleware

```javascript
const logger = require('./config/logger');
const { v4: uuidv4 } = require('uuid');

function loggingMiddleware(req, res, next) {
  // 生成或取得 Correlation ID
  req.correlationId = req.headers['x-correlation-id'] || uuidv4();

  // 記錄請求開始
  logger.info('HTTP request received', {
    correlationId: req.correlationId,
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.headers['user-agent']
  });

  // 記錄請求結束
  res.on('finish', () => {
    logger.info('HTTP request completed', {
      correlationId: req.correlationId,
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: Date.now() - req.startTime
    });
  });

  req.startTime = Date.now();
  next();
}
```

---

## 🔗 Correlation ID 使用指南

### 1. 什麼是 Correlation ID？

**Correlation ID** (關聯 ID) 是一個唯一識別碼，用來追蹤單一請求在整個系統中的流程。

#### 使用場景

```
使用者請求 → Frontend → Backend → Database → External API
      ↓            ↓          ↓          ↓           ↓
  [同一個 Correlation ID 貫穿整個流程]
```

### 2. 為什麼需要 Correlation ID？

✅ **分散式追蹤**: 在微服務架構中追蹤請求流程
✅ **除錯效率**: 快速找到相關的所有 log
✅ **效能分析**: 追蹤請求在各個服務的延遲
✅ **錯誤排查**: 找出錯誤發生的完整上下文

### 3. Correlation ID 格式

使用 **UUID v4** 格式:
```
550e8400-e29b-41d4-a716-446655440000
```

#### 生成方式

```javascript
const { v4: uuidv4 } = require('uuid');

// 生成新的 Correlation ID
const correlationId = uuidv4();

// 範例: "550e8400-e29b-41d4-a716-446655440000"
```

---

### 4. Correlation ID 傳遞機制

#### HTTP Header

使用自訂 Header `X-Correlation-ID`:

```javascript
// Frontend 發送請求
fetch('/api/events', {
  headers: {
    'X-Correlation-ID': correlationId
  }
});

// Backend 接收並傳遞
app.use((req, res, next) => {
  req.correlationId = req.headers['x-correlation-id'] || uuidv4();
  res.setHeader('X-Correlation-ID', req.correlationId);
  next();
});
```

#### 資料庫查詢

```javascript
async function createOrder(orderData, correlationId) {
  logger.info('Creating order', {
    correlationId,
    orderData
  });

  try {
    const order = await db.query('INSERT INTO orders...', orderData);

    logger.info('Order created successfully', {
      correlationId,
      orderId: order.id
    });

    return order;
  } catch (error) {
    logger.error('Failed to create order', {
      correlationId,
      error: error.message
    });
    throw error;
  }
}
```

#### 外部 API 呼叫

```javascript
async function callPaymentAPI(paymentData, correlationId) {
  logger.info('Calling payment API', {
    correlationId,
    amount: paymentData.amount
  });

  const response = await axios.post('https://payment-api.com/charge', paymentData, {
    headers: {
      'X-Correlation-ID': correlationId
    }
  });

  logger.info('Payment API response', {
    correlationId,
    status: response.status
  });

  return response.data;
}
```

---

### 5. 使用 Correlation ID 查詢 Log

#### 使用 grep

```bash
# 找出特定 Correlation ID 的所有 log
cat combined.log | grep "550e8400-e29b-41d4-a716-446655440000"

# 使用 jq 解析 JSON log
cat combined.log | jq 'select(.correlationId == "550e8400-e29b-41d4-a716-446655440000")'
```

#### 使用 Grafana Loki

```logql
{service="tixmaster-api"} |= "550e8400-e29b-41d4-a716-446655440000"
```

#### 使用 Elasticsearch

```json
{
  "query": {
    "match": {
      "correlationId": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

## ❌ 錯誤處理策略

### 1. 錯誤分類

#### 客戶端錯誤 (4xx)

| 錯誤碼 | 說明 | 處理方式 |
|-------|------|---------|
| **400** Bad Request | 請求格式錯誤 | 回傳具體錯誤訊息 |
| **401** Unauthorized | 未授權 | 要求登入 |
| **403** Forbidden | 無權限 | 回傳權限不足訊息 |
| **404** Not Found | 資源不存在 | 回傳 404 訊息 |
| **422** Unprocessable Entity | 驗證失敗 | 回傳驗證錯誤詳情 |
| **429** Too Many Requests | 超過速率限制 | 回傳 Retry-After header |

#### 伺服器錯誤 (5xx)

| 錯誤碼 | 說明 | 處理方式 |
|-------|------|---------|
| **500** Internal Server Error | 未預期錯誤 | 記錄 log，回傳通用錯誤訊息 |
| **502** Bad Gateway | 上游服務錯誤 | 重試或降級 |
| **503** Service Unavailable | 服務暫時不可用 | 回傳維護訊息 |
| **504** Gateway Timeout | 請求超時 | 增加 timeout 或優化查詢 |

---

### 2. 錯誤回應格式

#### 標準錯誤回應

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "message": "Email must be a valid email address"
      }
    ],
    "correlationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-11-30T10:30:45.123Z"
  }
}
```

#### 錯誤欄位說明

| 欄位 | 說明 | 範例 |
|------|------|------|
| `code` | 錯誤代碼 | "VALIDATION_ERROR" |
| `message` | 人類可讀的錯誤訊息 | "Invalid email format" |
| `details` | 詳細錯誤資訊 | [ { field, message } ] |
| `correlationId` | 追蹤 ID | "550e8400-..." |
| `timestamp` | 錯誤發生時間 | ISO 8601 格式 |

---

### 3. 錯誤處理實作

#### 自訂錯誤類別

```javascript
// errors/AppError.js
class AppError extends Error {
  constructor(message, statusCode, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;  // 可預期的錯誤
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, details = []) {
    super(message, 422, 'VALIDATION_ERROR');
    this.details = details;
  }
}

class NotFoundError extends AppError {
  constructor(resource) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 401, 'UNAUTHORIZED');
  }
}

module.exports = { AppError, ValidationError, NotFoundError, UnauthorizedError };
```

#### 全域錯誤處理中間件

```javascript
// middleware/errorHandler.js
const logger = require('../config/logger');

function errorHandler(err, req, res, next) {
  // 設定預設值
  err.statusCode = err.statusCode || 500;
  err.code = err.code || 'INTERNAL_ERROR';

  // 記錄錯誤
  if (err.statusCode >= 500) {
    logger.error('Server error', {
      correlationId: req.correlationId,
      error: err.message,
      stack: err.stack,
      route: req.path,
      method: req.method
    });
  } else {
    logger.warn('Client error', {
      correlationId: req.correlationId,
      error: err.message,
      statusCode: err.statusCode,
      route: req.path
    });
  }

  // 回應錯誤
  res.status(err.statusCode).json({
    error: {
      code: err.code,
      message: err.statusCode >= 500 ? 'Internal server error' : err.message,
      details: err.details || [],
      correlationId: req.correlationId,
      timestamp: new Date().toISOString()
    }
  });
}

module.exports = errorHandler;
```

#### 使用範例

```javascript
const { NotFoundError, ValidationError } = require('./errors/AppError');

// Route handler
app.get('/api/events/:id', async (req, res, next) => {
  try {
    const event = await Event.findById(req.params.id);

    if (!event) {
      throw new NotFoundError('Event');
    }

    res.json({ event });
  } catch (error) {
    next(error);  // 傳遞給錯誤處理中間件
  }
});

// Validation example
app.post('/api/users', async (req, res, next) => {
  try {
    const { email, password } = req.body;

    const errors = [];
    if (!email || !email.includes('@')) {
      errors.push({ field: 'email', message: 'Invalid email format' });
    }
    if (!password || password.length < 8) {
      errors.push({ field: 'password', message: 'Password must be at least 8 characters' });
    }

    if (errors.length > 0) {
      throw new ValidationError('Validation failed', errors);
    }

    // 建立用戶...
  } catch (error) {
    next(error);
  }
});
```

---

### 4. 重試策略

#### 指數退避 (Exponential Backoff)

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      const delay = Math.pow(2, i) * 1000;  // 1s, 2s, 4s...

      logger.warn('Retry attempt', {
        attempt: i + 1,
        maxRetries,
        delay,
        error: error.message
      });

      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// 使用範例
const result = await retryWithBackoff(async () => {
  return await externalAPI.call();
});
```

#### Circuit Breaker (斷路器)

```javascript
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED';  // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }

  async execute(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
      logger.error('Circuit breaker opened', {
        failureCount: this.failureCount,
        threshold: this.threshold
      });
    }
  }
}
```

---

## 🎯 最佳實踐

### 1. Log 最佳實踐

✅ **DO**:
- 使用結構化 JSON 日誌
- 包含 Correlation ID
- 記錄重要業務事件
- 敏感資料脫敏 (密碼、信用卡號)
- 使用適當的 log level

❌ **DON'T**:
- 記錄明文密碼
- 過度 logging (影響效能)
- 使用 `console.log` (使用 logger)
- 忽略錯誤 stack trace

### 2. Correlation ID 最佳實踐

✅ **DO**:
- 每個請求都有 Correlation ID
- 在所有 log 中包含 Correlation ID
- 透過 HTTP header 傳遞
- 在錯誤回應中回傳 Correlation ID

❌ **DON'T**:
- 使用遞增數字 (不唯一)
- 忘記在外部 API 呼叫中傳遞

### 3. 錯誤處理最佳實踐

✅ **DO**:
- 區分可預期與不可預期錯誤
- 記錄完整的 stack trace
- 提供清晰的錯誤訊息
- 實作重試機制
- 使用 Circuit Breaker

❌ **DON'T**:
- 忽略錯誤 (silent fail)
- 洩漏內部實作細節
- 回傳 stack trace 給客戶端
- 無限重試

---

**文件版本**: 1.0
**最後更新**: 2025-11-30
**負責人**: TixMaster Development Team
