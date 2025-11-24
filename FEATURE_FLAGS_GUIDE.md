# TixMaster Feature Flags 功能開關系統

## 目錄
- [概述](#概述)
- [架構設計](#架構設計)
- [使用指南](#使用指南)
- [API 文檔](#api-文檔)
- [實作範例](#實作範例)
- [最佳實踐](#最佳實踐)
- [故障排除](#故障排除)

---

## 概述

Feature Flags (功能開關) 是一種軟體開發技術，允許在不重新部署代碼的情況下動態啟用或停用功能。

### 為什麼需要 Feature Flags？

1. **A/B 測試**: 測試不同版本的功能對用戶行為的影響
2. **逐步推出**: 先對一小部分用戶開放新功能，逐步擴大範圍
3. **快速回滾**: 出現問題時可立即停用功能，無需重新部署
4. **持續部署**: 代碼可以合併到主分支，但功能保持隱藏直到準備好發布
5. **HDD (假設驅動開發)**: 驗證產品假設，根據數據做決策

### 系統特性

- ✅ 資料庫驅動 (PostgreSQL)
- ✅ 前端快取機制 (5分鐘)
- ✅ 後端快取機制 (1分鐘)
- ✅ 管理後台 UI 控制
- ✅ RESTful API
- ✅ 前端 JavaScript SDK
- ✅ 後端 Express 中介軟體

---

## 架構設計

### 資料流

```
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                   │
│                  feature_flags table                     │
│  (flag_key, flag_value, description, updated_at)        │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ SQL Query
                     │
        ┌────────────┴─────────────┐
        │                          │
        ▼                          ▼
┌───────────────┐          ┌──────────────┐
│   Backend     │          │   Frontend   │
│   (Node.js)   │          │  (Browser)   │
│               │          │              │
│ • Middleware  │◄────────►│ • SDK        │
│ • Cache (1m)  │   API    │ • Cache (5m) │
│ • Routes      │          │ • UI         │
└───────────────┘          └──────────────┘
```

### 資料庫 Schema

```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) UNIQUE NOT NULL,
    flag_value BOOLEAN DEFAULT FALSE,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 預設功能開關

| Flag Key | 預設值 | 說明 |
|----------|--------|------|
| `ENABLE_CHECKOUT_TIMER` | `true` | 結帳倒數計時器 (15分鐘) |
| `ENABLE_VIEWING_COUNT` | `true` | 活動觀看人數顯示 |

---

## 使用指南

### 1. 前端使用 (Frontend)

#### 引入 SDK

```html
<script src="featureFlags.js"></script>
```

#### 初始化並檢查功能

```javascript
// 初始化 (只需一次)
await FeatureFlags.init();

// 檢查功能是否啟用
if (FeatureFlags.isEnabled('ENABLE_VIEWING_COUNT')) {
    showViewingCount();
} else {
    hideViewingCount();
}

// 取得所有功能開關
const allFlags = FeatureFlags.getAll();
console.log(allFlags);

// 取得單一功能開關詳情
const flag = FeatureFlags.getFlag('ENABLE_CHECKOUT_TIMER');
console.log(flag); // { enabled: true, description: '...', updatedAt: '...' }
```

#### 管理功能開關 (管理員)

```javascript
// 更新功能開關
await FeatureFlags.updateFlag('ENABLE_VIEWING_COUNT', false);

// 強制刷新快取
await FeatureFlags.refresh();

// 清除本地快取
FeatureFlags.clearCache();
```

#### 完整範例: event-detail.html

```javascript
async function initPage() {
    // 初始化 Feature Flags
    await FeatureFlags.init();

    // 根據功能開關顯示/隱藏功能
    if (FeatureFlags.isEnabled('ENABLE_VIEWING_COUNT')) {
        document.getElementById('viewingBadge').style.display = 'block';
    }

    if (FeatureFlags.isEnabled('ENABLE_CHECKOUT_TIMER')) {
        startCountdownTimer();
    }
}

initPage();
```

---

### 2. 後端使用 (Backend)

#### 在路由中檢查功能開關

```javascript
const express = require('express');
const router = express.Router();

// 方法 1: 使用 req.featureFlags (已自動附加)
router.get('/some-endpoint', (req, res) => {
    if (req.featureFlags.isEnabled('ENABLE_NEW_FEATURE')) {
        // 新功能的邏輯
        res.json({ message: 'New feature enabled!' });
    } else {
        // 舊功能的邏輯
        res.json({ message: 'Using old feature' });
    }
});

// 方法 2: 使用 middleware 強制要求功能開關
const { requireFeatureFlag } = require('../middleware/featureFlags');

router.get('/beta-feature',
    requireFeatureFlag('ENABLE_BETA'),
    (req, res) => {
        // 只有當 ENABLE_BETA 為 true 時才會執行
        res.json({ message: 'Beta feature' });
    }
);
```

#### 直接使用 Feature Flags 模組

```javascript
const featureFlags = require('../middleware/featureFlags');

async function someFunction() {
    const isEnabled = await featureFlags.isEnabled('ENABLE_NEW_FEATURE');

    if (isEnabled) {
        // 執行新功能
    } else {
        // 執行舊功能
    }
}
```

---

## API 文檔

### 取得所有功能開關

**GET** `/api/feature-flags`

**回應:**
```json
{
    "flags": {
        "ENABLE_CHECKOUT_TIMER": {
            "enabled": true,
            "description": "結帳倒數計時器",
            "updatedAt": "2025-11-25T10:30:00.000Z"
        },
        "ENABLE_VIEWING_COUNT": {
            "enabled": true,
            "description": "活動觀看人數顯示",
            "updatedAt": "2025-11-25T10:30:00.000Z"
        }
    }
}
```

### 取得單一功能開關

**GET** `/api/feature-flags/:key`

**範例:** `/api/feature-flags/ENABLE_CHECKOUT_TIMER`

**回應:**
```json
{
    "key": "ENABLE_CHECKOUT_TIMER",
    "enabled": true,
    "description": "結帳倒數計時器",
    "updatedAt": "2025-11-25T10:30:00.000Z"
}
```

### 更新功能開關

**PUT** `/api/feature-flags/:key`

**請求 Body:**
```json
{
    "enabled": false
}
```

**回應:**
```json
{
    "message": "Feature flag updated",
    "flag": {
        "key": "ENABLE_CHECKOUT_TIMER",
        "enabled": false,
        "description": "結帳倒數計時器"
    }
}
```

---

## 實作範例

### 範例 1: 新增功能開關

#### 步驟 1: 在資料庫中新增

```sql
INSERT INTO feature_flags (flag_key, flag_value, description)
VALUES ('ENABLE_DISCOUNT_CODE', false, '折扣碼功能');
```

#### 步驟 2: 在前端使用

```javascript
// 在結帳頁面
await FeatureFlags.init();

if (FeatureFlags.isEnabled('ENABLE_DISCOUNT_CODE')) {
    document.getElementById('discountCodeInput').style.display = 'block';
}
```

#### 步驟 3: 在後端使用

```javascript
// 在訂單 API
router.post('/orders', async (req, res) => {
    const { ticketId, quantity, discountCode } = req.body;

    // 檢查折扣碼功能是否啟用
    if (discountCode && req.featureFlags.isEnabled('ENABLE_DISCOUNT_CODE')) {
        // 驗證折扣碼
        const discount = await validateDiscountCode(discountCode);
        total = total * (1 - discount);
    }

    // 建立訂單...
});
```

---

### 範例 2: A/B 測試

假設你想測試「紅色購買按鈕」vs「藍色購買按鈕」哪個轉換率更高。

#### 步驟 1: 新增功能開關

```sql
INSERT INTO feature_flags (flag_key, flag_value, description)
VALUES ('ENABLE_RED_BUY_BUTTON', false, 'A/B 測試：紅色購買按鈕');
```

#### 步驟 2: 前端實作

```javascript
await FeatureFlags.init();

const buyButton = document.getElementById('buyButton');

if (FeatureFlags.isEnabled('ENABLE_RED_BUY_BUTTON')) {
    buyButton.style.backgroundColor = 'red';
    // 記錄分析事件
    trackAnalyticsEvent('variant', 'red_button');
} else {
    buyButton.style.backgroundColor = 'blue';
    trackAnalyticsEvent('variant', 'blue_button');
}
```

#### 步驟 3: 分析結果

1. 先對 50% 用戶啟用紅色按鈕
2. 收集 1-2 週的數據
3. 比較兩組的轉換率
4. 根據數據決定使用哪個版本

---

## 最佳實踐

### 1. 命名規範

功能開關的 key 應該:
- 使用大寫字母和底線: `ENABLE_NEW_FEATURE`
- 以 `ENABLE_` 開頭表示功能開關
- 描述性強，清楚表達功能

```javascript
// ✅ 好的命名
ENABLE_CHECKOUT_TIMER
ENABLE_DISCOUNT_CODE
ENABLE_NEW_PAYMENT_METHOD

// ❌ 不好的命名
feature1
newStuff
test
```

### 2. 快取策略

- **前端**: 5分鐘快取 (平衡即時性與效能)
- **後端**: 1分鐘快取 (更即時的更新)
- **資料庫**: 即時更新

```javascript
// 前端: 如果需要立即更新
await FeatureFlags.refresh();

// 後端: 如果需要立即更新
await featureFlagsMiddleware.refreshFlagCache();
```

### 3. 預設值策略

新功能開關應該根據情況設定預設值:

- **新功能**: 預設 `false` (逐步推出)
- **穩定功能**: 預設 `true` (隨時可停用)

### 4. 清理舊的功能開關

功能完全推出或完全移除後，記得清理:

```sql
-- 刪除不再使用的功能開關
DELETE FROM feature_flags WHERE flag_key = 'OLD_FEATURE';
```

### 5. 文檔化

每個功能開關都應該有清楚的說明:

```sql
INSERT INTO feature_flags (flag_key, flag_value, description)
VALUES (
    'ENABLE_NEW_CHECKOUT',
    false,
    '新版結帳流程：整合信用卡快速支付和 Apple Pay'
);
```

### 6. 監控與警報

設定監控來追蹤:
- 功能開關的變更歷史
- 功能啟用後的錯誤率
- 功能啟用後的效能影響

### 7. 測試策略

```javascript
// 單元測試
describe('Feature Flags', () => {
    it('should show viewing count when enabled', async () => {
        // Mock feature flag
        FeatureFlags.isEnabled = jest.fn().mockReturnValue(true);

        renderEventDetail();

        expect(document.getElementById('viewingBadge').style.display)
            .toBe('block');
    });
});
```

---

## 故障排除

### 問題 1: 功能開關沒有更新

**症狀**: 在管理後台更新了功能開關，但前端沒有反應

**原因**: 快取未失效

**解決方案**:
```javascript
// 強制刷新快取
await FeatureFlags.refresh();

// 或清除快取後重新載入頁面
FeatureFlags.clearCache();
location.reload();
```

### 問題 2: 無法連接到 API

**症狀**: `Failed to load feature flags: HTTP 404`

**原因**:
- 後端伺服器未啟動
- API 路徑錯誤

**解決方案**:
```bash
# 檢查後端是否運行
cd backend
npm start

# 檢查 API 是否可訪問
curl http://localhost:3000/api/feature-flags
```

### 問題 3: 功能開關在資料庫中不存在

**症狀**: `Unknown flag: ENABLE_SOME_FEATURE`

**解決方案**:
```sql
-- 在資料庫中新增該功能開關
INSERT INTO feature_flags (flag_key, flag_value, description)
VALUES ('ENABLE_SOME_FEATURE', false, '功能說明');
```

### 問題 4: 後端 middleware 未生效

**症狀**: `req.featureFlags is undefined`

**原因**: Middleware 未正確註冊

**解決方案**:
```javascript
// 在 server.js 中確認已加入
const featureFlagsMiddleware = require('./middleware/featureFlags');
app.use(featureFlagsMiddleware.attachFeatureFlags);
```

---

## 進階使用

### 1. 用戶分組 (User Segmentation)

未來可以擴展功能開關系統，支援基於用戶屬性的分組:

```javascript
// 範例: 只對特定用戶群組啟用
if (FeatureFlags.isEnabledForUser('ENABLE_BETA', userId)) {
    // 啟用 beta 功能
}
```

### 2. 時間排程 (Scheduled Rollout)

自動在特定時間啟用/停用功能:

```sql
-- 擴展 schema
ALTER TABLE feature_flags
ADD COLUMN enabled_from TIMESTAMP,
ADD COLUMN enabled_until TIMESTAMP;
```

### 3. 百分比推出 (Percentage Rollout)

逐步增加啟用功能的用戶比例:

```sql
-- 擴展 schema
ALTER TABLE feature_flags
ADD COLUMN rollout_percentage INTEGER DEFAULT 100;
```

---

## 相關資源

- [PostgreSQL 文檔](https://www.postgresql.org/docs/)
- [Feature Toggles (Martin Fowler)](https://martinfowler.com/articles/feature-toggles.html)
- [Hypothesis-Driven Development](https://barryoreilly.com/explore/blog/how-to-implement-hypothesis-driven-development/)

---

## 常見問題 (FAQ)

### Q: Feature Flags 會影響效能嗎？

A: 影響很小。前端和後端都有快取機制，大部分時間不會查詢資料庫。

### Q: 可以在生產環境即時切換功能嗎？

A: 可以！這正是 Feature Flags 的主要優勢。更新後 1-5 分鐘內所有用戶都會看到變更。

### Q: 如何追蹤功能開關的變更歷史？

A: 目前系統只記錄最後更新時間。如需完整歷史，可以擴展資料庫 schema 加入 audit log 表格。

### Q: Feature Flags 和環境變數有什麼不同？

A:
- **環境變數**: 部署時設定，需要重啟伺服器才能更新
- **Feature Flags**: 儲存在資料庫，可即時更新無需重啟

---

## 聯絡與支援

如有問題或建議，請聯繫開發團隊或在專案 repository 提交 issue。
