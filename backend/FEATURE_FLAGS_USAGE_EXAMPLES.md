# Feature Flags 使用範例

本文檔提供在 TixMaster 專案中使用 Feature Flags 的實際範例。

## 目錄
- [基礎使用](#基礎使用)
- [在路由中使用](#在路由中使用)
- [在中介軟體中使用](#在中介軟體中使用)
- [A/B 測試範例](#ab-測試範例)
- [逐步推出新功能](#逐步推出新功能)

---

## 基礎使用

### 範例 1: 在路由中檢查功能開關

```javascript
// backend/routes/orders.js
const express = require('express');
const router = express.Router();

// 建立訂單
router.post('/', async (req, res, next) => {
    try {
        const { ticketId, quantity, discountCode } = req.body;

        // 檢查折扣碼功能是否啟用
        if (discountCode && req.featureFlags.isEnabled('ENABLE_DISCOUNT_CODE')) {
            // 驗證並套用折扣碼
            const discount = await validateDiscountCode(discountCode);
            if (!discount) {
                return res.status(400).json({ error: 'Invalid discount code' });
            }
            // 套用折扣...
        }

        // 繼續訂單處理...
    } catch (err) {
        next(err);
    }
});

module.exports = router;
```

---

## 在路由中使用

### 範例 2: 使用 requireFeatureFlag 中介軟體保護路由

```javascript
// backend/routes/beta.js
const express = require('express');
const router = express.Router();
const { requireFeatureFlag } = require('../middleware/featureFlags');
const { authenticate } = require('../middleware/auth');

// Beta 功能: 只有當功能開關啟用時才能訪問
router.get('/beta-dashboard',
    authenticate,  // 先驗證使用者
    requireFeatureFlag('ENABLE_BETA_DASHBOARD'),  // 檢查功能開關
    async (req, res) => {
        // 只有當 ENABLE_BETA_DASHBOARD 為 true 時才會執行到這裡
        res.json({
            message: 'Welcome to beta dashboard!',
            features: ['feature1', 'feature2', 'feature3']
        });
    }
);

module.exports = router;
```

### 範例 3: 條件性功能

```javascript
// backend/routes/events.js
const express = require('express');
const router = express.Router();

router.get('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;

        // 基本活動資料
        const event = await getEventById(id);

        // 根據功能開關決定回傳內容
        const response = {
            id: event.id,
            title: event.title,
            description: event.description,
            date: event.date,
            location: event.location
        };

        // 功能: 顯示剩餘票數
        if (req.featureFlags.isEnabled('ENABLE_REMAINING_TICKETS')) {
            const tickets = await getTicketsForEvent(id);
            response.remainingTickets = tickets.available_quantity;
        }

        // 功能: 顯示觀看人數
        if (req.featureFlags.isEnabled('ENABLE_VIEWING_COUNT')) {
            const viewCount = await getViewingCount(id);
            response.viewingCount = viewCount;
        }

        res.json(response);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
```

---

## 在中介軟體中使用

### 範例 4: 動態速率限制

```javascript
// backend/middleware/rateLimiter.js
const rateLimit = require('express-rate-limit');

function createRateLimiter(req, res, next) {
    // 根據功能開關調整速率限制
    const strictMode = req.featureFlags.isEnabled('ENABLE_STRICT_RATE_LIMIT');

    const limiter = rateLimit({
        windowMs: 15 * 60 * 1000, // 15 分鐘
        max: strictMode ? 50 : 100, // 嚴格模式: 50 次, 一般模式: 100 次
        message: strictMode
            ? 'Too many requests, please try again later (strict mode)'
            : 'Too many requests, please try again later'
    });

    limiter(req, res, next);
}

module.exports = createRateLimiter;
```

### 範例 5: 動態日誌級別

```javascript
// backend/middleware/logger.js

function requestLogger(req, res, next) {
    const verboseLogging = req.featureFlags.isEnabled('ENABLE_VERBOSE_LOGGING');

    if (verboseLogging) {
        // 詳細日誌
        console.log({
            timestamp: new Date().toISOString(),
            method: req.method,
            path: req.path,
            query: req.query,
            body: req.body,
            ip: req.ip,
            userAgent: req.get('user-agent')
        });
    } else {
        // 簡單日誌
        console.log(`${req.method} ${req.path}`);
    }

    next();
}

module.exports = requestLogger;
```

---

## A/B 測試範例

### 範例 6: 測試兩種不同的推薦演算法

#### 步驟 1: 新增功能開關

```sql
INSERT INTO feature_flags (flag_key, flag_value, description)
VALUES ('ENABLE_NEW_RECOMMENDATION_ALGORITHM', false, 'A/B 測試：新推薦演算法');
```

#### 步驟 2: 實作兩種演算法

```javascript
// backend/routes/recommendations.js
const express = require('express');
const router = express.Router();

router.get('/events', async (req, res, next) => {
    try {
        const userId = req.user?.id;

        // 根據功能開關選擇演算法
        let recommendations;

        if (req.featureFlags.isEnabled('ENABLE_NEW_RECOMMENDATION_ALGORITHM')) {
            // 新演算法: 基於機器學習
            recommendations = await getMLBasedRecommendations(userId);

            // 記錄 A/B 測試事件
            await trackAnalytics({
                userId,
                eventType: 'recommendation_shown',
                variant: 'ml_algorithm',
                recommendations: recommendations.map(r => r.id)
            });
        } else {
            // 舊演算法: 基於簡單規則
            recommendations = await getRuleBasedRecommendations(userId);

            await trackAnalytics({
                userId,
                eventType: 'recommendation_shown',
                variant: 'rule_based',
                recommendations: recommendations.map(r => r.id)
            });
        }

        res.json({ recommendations });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
```

#### 步驟 3: 追蹤點擊轉換

```javascript
// 當使用者點擊推薦時
router.post('/events/:id/click', async (req, res) => {
    const { id } = req.params;
    const userId = req.user?.id;

    // 記錄點擊事件
    await trackAnalytics({
        userId,
        eventType: 'recommendation_clicked',
        eventId: id,
        featureFlags: req.featureFlags.getAll() // 記錄當時的功能開關狀態
    });

    res.json({ success: true });
});
```

#### 步驟 4: 分析結果

```sql
-- 計算兩種演算法的點擊率
WITH shown AS (
    SELECT
        (feature_flags->>'ENABLE_NEW_RECOMMENDATION_ALGORITHM')::boolean as is_new_algo,
        COUNT(*) as shown_count
    FROM analytics_events
    WHERE event_type = 'recommendation_shown'
    GROUP BY is_new_algo
),
clicked AS (
    SELECT
        (feature_flags->>'ENABLE_NEW_RECOMMENDATION_ALGORITHM')::boolean as is_new_algo,
        COUNT(*) as click_count
    FROM analytics_events
    WHERE event_type = 'recommendation_clicked'
    GROUP BY is_new_algo
)
SELECT
    CASE WHEN shown.is_new_algo THEN 'ML Algorithm' ELSE 'Rule Based' END as algorithm,
    shown.shown_count,
    clicked.click_count,
    ROUND(clicked.click_count::decimal / shown.shown_count * 100, 2) as click_through_rate
FROM shown
LEFT JOIN clicked ON shown.is_new_algo = clicked.is_new_algo;
```

---

## 逐步推出新功能

### 範例 7: 新支付方式的逐步推出

#### 階段 1: 內部測試 (0% 用戶)

```sql
-- 關閉功能，只有開發者能測試
UPDATE feature_flags
SET flag_value = false
WHERE flag_key = 'ENABLE_APPLE_PAY';
```

```javascript
// 開發者可以透過特殊參數強制啟用
router.post('/orders', async (req, res) => {
    const { paymentMethod } = req.body;

    // 檢查功能開關或開發者覆寫
    const applePayEnabled = req.featureFlags.isEnabled('ENABLE_APPLE_PAY') ||
                           req.query.force_apple_pay === 'true';

    if (paymentMethod === 'apple_pay' && !applePayEnabled) {
        return res.status(400).json({
            error: 'Payment method not available'
        });
    }

    // 處理 Apple Pay...
});
```

#### 階段 2: Beta 測試 (5% 用戶)

```sql
-- 啟用功能
UPDATE feature_flags
SET flag_value = true
WHERE flag_key = 'ENABLE_APPLE_PAY';
```

監控錯誤率和使用情況，確保穩定。

#### 階段 3: 全面推出 (100% 用戶)

確認無問題後，移除功能開關檢查，將功能變為永久性的。

```javascript
// 最終: 移除功能開關，變成正式功能
router.post('/orders', async (req, res) => {
    const { paymentMethod } = req.body;

    // Apple Pay 現在是正式支援的支付方式
    if (paymentMethod === 'apple_pay') {
        // 處理 Apple Pay...
    }
});
```

```sql
-- 清理不再需要的功能開關
DELETE FROM feature_flags WHERE flag_key = 'ENABLE_APPLE_PAY';
```

---

## 緊急停用功能

### 範例 8: 發現問題時快速回滾

假設新的搜尋功能導致伺服器負載過高:

```javascript
// backend/routes/search.js
router.get('/events/search', async (req, res) => {
    const { query } = req.query;

    // 檢查新搜尋功能是否啟用
    if (req.featureFlags.isEnabled('ENABLE_NEW_SEARCH')) {
        try {
            // 新的全文搜尋 (可能有效能問題)
            const results = await performFullTextSearch(query);
            return res.json({ results });
        } catch (error) {
            console.error('New search failed:', error);
            // 自動降級到舊搜尋
        }
    }

    // 降級: 使用舊的簡單搜尋
    const results = await performSimpleSearch(query);
    res.json({ results });
});
```

**緊急停用:**

```sql
-- 在管理後台或直接在資料庫停用
UPDATE feature_flags
SET flag_value = false
WHERE flag_key = 'ENABLE_NEW_SEARCH';
```

1 分鐘內所有伺服器會自動切換回舊搜尋，無需重啟！

---

## 複雜範例: 多功能組合

### 範例 9: 根據多個功能開關組合決定行為

```javascript
// backend/routes/checkout.js
router.post('/checkout', async (req, res) => {
    const { orderId } = req.body;

    // 取得所有相關功能開關
    const enableTimer = req.featureFlags.isEnabled('ENABLE_CHECKOUT_TIMER');
    const enablePriority = req.featureFlags.isEnabled('ENABLE_PRIORITY_CHECKOUT');
    const enableEmailNotif = req.featureFlags.isEnabled('ENABLE_EMAIL_NOTIFICATIONS');

    let timeLimit = null;

    // 組合 1: 啟用計時器 + 優先結帳
    if (enableTimer && enablePriority && req.user?.isPremium) {
        timeLimit = 20 * 60; // VIP 用戶: 20 分鐘
    }
    // 組合 2: 只啟用計時器
    else if (enableTimer) {
        timeLimit = 15 * 60; // 一般用戶: 15 分鐘
    }
    // 組合 3: 都不啟用
    else {
        timeLimit = null; // 無時間限制
    }

    // 建立訂單
    const order = await createOrder({
        orderId,
        userId: req.user?.id,
        timeLimit
    });

    // 功能: 寄送 Email 通知
    if (enableEmailNotif && req.user?.email) {
        await sendOrderConfirmationEmail(req.user.email, order);
    }

    res.json({ order });
});
```

---

## 測試範例

### 範例 10: 單元測試 Feature Flags

```javascript
// backend/routes/__tests__/orders.test.js
const request = require('supertest');
const app = require('../server');
const featureFlags = require('../middleware/featureFlags');

describe('Orders API with Feature Flags', () => {
    beforeEach(() => {
        // Mock feature flags
        jest.spyOn(featureFlags, 'isEnabled').mockImplementation((key) => {
            if (key === 'ENABLE_DISCOUNT_CODE') return true;
            return false;
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    test('should apply discount when feature is enabled', async () => {
        const response = await request(app)
            .post('/api/orders')
            .send({
                ticketId: 1,
                quantity: 2,
                discountCode: 'SAVE20'
            })
            .expect(200);

        expect(response.body.total).toBe(4000); // 原價 5000 - 20%
        expect(response.body.discountApplied).toBe(true);
    });

    test('should ignore discount when feature is disabled', async () => {
        // 覆寫 mock
        featureFlags.isEnabled.mockReturnValue(false);

        const response = await request(app)
            .post('/api/orders')
            .send({
                ticketId: 1,
                quantity: 2,
                discountCode: 'SAVE20'
            })
            .expect(200);

        expect(response.body.total).toBe(5000); // 原價
        expect(response.body.discountApplied).toBeUndefined();
    });
});
```

---

## 效能考量

### 範例 11: 快取功能開關檢查結果

如果在同一個請求中需要多次檢查相同的功能開關:

```javascript
// backend/middleware/featureFlagsCache.js
function cacheFeatureFlagsForRequest(req, res, next) {
    const originalIsEnabled = req.featureFlags.isEnabled;

    // 在請求生命週期內快取結果
    const cache = {};

    req.featureFlags.isEnabled = (key) => {
        if (!(key in cache)) {
            cache[key] = originalIsEnabled(key);
        }
        return cache[key];
    };

    next();
}

module.exports = cacheFeatureFlagsForRequest;
```

---

## 小結

Feature Flags 是強大的工具，可以讓你:
1. 安全地推出新功能
2. 快速回滾有問題的功能
3. 進行 A/B 測試
4. 根據數據做產品決策

記得在功能穩定後清理不再需要的功能開關，保持代碼整潔！
