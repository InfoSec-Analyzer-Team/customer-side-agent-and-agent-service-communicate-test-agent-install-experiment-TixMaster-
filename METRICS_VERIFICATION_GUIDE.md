# 📊 Payment Completion Rate 驗證指南

## 概述

本指南說明如何驗證 **Hypothesis 1: Urgency Tactic** 的核心指標：**Payment Completion Rate (付款完成率)**。

### 📌 Hypothesis 1: Urgency Tactic

**假設陳述**：「若在結帳頁面加入『倒數計時器』，將能製造稀缺感，進而提升用戶的結帳完成率。」

**關鍵指標**：Payment Completion Rate (付款完成率)
- 定義：進入結帳頁面後成功完成付款的比例
- 計算公式：`(完成付款人數 / 進入結帳頁人數) × 100%`

**成功標準**：付款完成率提升 **≥ 10%**

---

## 🏗️ 系統架構

### 1. 數據庫表格：`analytics_events`

```sql
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    feature_flags_snapshot JSONB,
    session_id VARCHAR(100),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 追蹤事件類型

| 事件類型 | 說明 | 觸發時機 |
|---------|------|---------|
| `checkout_timer_shown` | 顯示倒數計時器 | 進入結帳頁 + 計時器啟用時 |
| `payment_attempted` | 嘗試付款 | 點擊「確認付款」按鈕 |
| `payment_completed` | 付款完成 | 付款成功處理完成 |
| `checkout_timeout` | 結帳逾時 | 倒數計時器歸零 |
| `checkout_abandoned` | 放棄結帳 | 點擊「返回」或關閉頁面 |

### 3. Feature Flag 狀態

- `ENABLE_CHECKOUT_TIMER: false` → Control Group (對照組)
- `ENABLE_CHECKOUT_TIMER: true` → Treatment Group (實驗組)

---

## 🧪 測試流程

### Step 1: 準備環境

1. **啟動後端服務器**：
   ```bash
   cd backend
   npm start
   ```

2. **確認數據庫表格已建立**：
   ```bash
   cd backend
   node scripts/setup-analytics.js
   ```

### Step 2: Control Group 測試 (無倒數計時器)

1. **在 Admin Dashboard 停用計時器**：
   - 打開 [admin-dashboard.html](admin-dashboard.html)
   - 將 `ENABLE_CHECKOUT_TIMER` 切換為 **OFF** (停用)

2. **執行購票流程 (建議 10-20 次)**：
   - 打開 [index.html](index.html)
   - 點擊任一活動 → 進入活動詳情頁
   - 點擊「立即購票」→ 進入結帳頁
   - **重點：此時應該看不到倒數計時器**
   - 填寫購買人資訊
   - 點擊「確認付款」→ 完成付款

3. **模擬各種行為**：
   - ✅ 完成付款 (payment_completed)
   - ❌ 放棄結帳 (checkout_abandoned)
   - ⏱️ 長時間停留但未付款

### Step 3: Treatment Group 測試 (有倒數計時器)

1. **在 Admin Dashboard 啟用計時器**：
   - 打開 [admin-dashboard.html](admin-dashboard.html)
   - 將 `ENABLE_CHECKOUT_TIMER` 切換為 **ON** (啟用)

2. **執行購票流程 (建議 10-20 次)**：
   - 打開 [index.html](index.html)
   - 點擊任一活動 → 進入活動詳情頁
   - 點擊「立即購票」→ 進入結帳頁
   - **重點：此時應該看到紅色倒數計時器橫幅**
   - 觀察計時器從 15:00 開始倒數
   - 填寫購買人資訊
   - 點擊「確認付款」→ 完成付款

3. **模擬各種行為**：
   - ✅ 快速完成付款
   - ✅ 在最後一分鐘完成付款
   - ❌ 時間到期 (checkout_timeout)
   - ❌ 放棄結帳

### Step 4: 驗證指標

運行驗證腳本：

```bash
node verify-metrics.js
```

**輸出範例**：

```
================================================================================
📊 Hypothesis 1: Urgency Tactic - Payment Completion Rate
================================================================================

  假設：在結帳頁面加入倒數計時器，將能製造稀缺感，提升結帳完成率
  成功標準：付款完成率提升 ≥ 10%

  Control Group (無倒數計時器):
  總進入結帳頁次數                         15 sessions
  完成付款次數                               9 payments
  付款完成率                               60.00%

  Treatment Group (有倒數計時器):
  總進入結帳頁次數                         18 sessions
  完成付款次數                              14 payments
  付款完成率                               77.78%

  📈 結果分析:
  提升幅度 (Lift)                        +29.63%
  ✅ 達成成功標準！(提升 ≥ 10%)
```

---

## 📊 計算公式

### Payment Completion Rate

```
Control Group完成率 = (Control Group 完成付款次數 / Control Group 進入結帳頁次數) × 100%
Treatment Group完成率 = (Treatment Group 完成付款次數 / Treatment Group 進入結帳頁次數) × 100%
```

### Lift (提升幅度)

```
Lift% = ((Treatment完成率 - Control完成率) / Control完成率) × 100%
```

**範例**：
- Control: 60%
- Treatment: 77.78%
- Lift = ((77.78 - 60) / 60) × 100% = **+29.63%**

---

## 🔍 SQL 查詢範例

### 查看所有事件

```sql
SELECT * FROM analytics_events
ORDER BY created_at DESC
LIMIT 20;
```

### 查看特定 Session 的完整旅程

```sql
SELECT
    event_type,
    event_data,
    feature_flags_snapshot->>'ENABLE_CHECKOUT_TIMER' as has_timer,
    created_at
FROM analytics_events
WHERE session_id = 'session_xxx'
ORDER BY created_at;
```

### 手動計算 Payment Completion Rate

```sql
WITH checkout_sessions AS (
    SELECT DISTINCT
        session_id,
        (feature_flags_snapshot->>'ENABLE_CHECKOUT_TIMER')::boolean as has_timer
    FROM analytics_events
    WHERE event_type IN ('checkout_timer_shown', 'payment_attempted')
),
payment_completions AS (
    SELECT DISTINCT session_id
    FROM analytics_events
    WHERE event_type = 'payment_completed'
)
SELECT
    cs.has_timer,
    COUNT(DISTINCT cs.session_id) as total_sessions,
    COUNT(DISTINCT pc.session_id) as completed_payments,
    ROUND(
        (COUNT(DISTINCT pc.session_id)::numeric / NULLIF(COUNT(DISTINCT cs.session_id), 0)) * 100,
        2
    ) as completion_rate_percent
FROM checkout_sessions cs
LEFT JOIN payment_completions pc ON cs.session_id = pc.session_id
GROUP BY cs.has_timer
ORDER BY cs.has_timer;
```

---

## 🎯 決策標準

### ✅ 假設成立 (Lift ≥ 10%)
- **行動**：保留倒數計時器功能
- **後續**：考慮優化計時器時長、視覺設計、文案
- **範例**：Lift = +29.63% → 倒數計時器顯著提升完成率

### ⚠️ 有提升但未達標 (0% < Lift < 10%)
- **行動**：調整設計後重新測試
- **優化方向**：
  - 調整倒數時間 (15分鐘 → 10分鐘？)
  - 改善視覺設計 (更顯著的警示)
  - 優化文案 (更強調稀缺性)
- **範例**：Lift = +5% → 有效果但不足，需優化

### ❌ 假設不成立 (Lift < 0%)
- **行動**：移除倒數計時器功能
- **原因分析**：
  - 計時器造成壓力反而讓用戶放棄
  - 用戶不信任倒數機制
  - 實施方式有問題
- **範例**：Lift = -8% → 倒數計時器反而降低完成率

### 🔄 數據不足
- **行動**：繼續收集數據
- **建議樣本量**：每組至少 30-50 次結帳流程
- **時間範圍**：建議收集 1-2 週數據

---

## 🛠️ API 端點

### 記錄事件

```bash
POST http://localhost:3000/api/analytics/event
Content-Type: application/json

{
  "userId": null,
  "sessionId": "session_xxx",
  "eventType": "payment_completed",
  "eventData": {
    "eventId": "1",
    "quantity": 2,
    "totalAmount": 5000
  },
  "featureFlagsSnapshot": {
    "ENABLE_CHECKOUT_TIMER": true,
    "ENABLE_VIEWING_COUNT": false
  }
}
```

### 查詢事件

```bash
GET http://localhost:3000/api/analytics/events?eventType=payment_completed&limit=50
```

### 獲取指標

```bash
GET http://localhost:3000/api/analytics/metrics
GET http://localhost:3000/api/analytics/metrics?start_date=2025-11-01&end_date=2025-11-30
```

### 獲取摘要

```bash
GET http://localhost:3000/api/analytics/summary
```

---

## 📝 測試檢查清單

- [ ] 數據庫表格 `analytics_events` 已建立
- [ ] Backend server 正常運行於 http://localhost:3000
- [ ] Feature Flags 可正常切換 (admin-dashboard.html)
- [ ] Control Group: 計時器功能關閉，執行至少 10 次購票流程
- [ ] Treatment Group: 計時器功能開啟，執行至少 10 次購票流程
- [ ] 模擬了各種用戶行為 (完成、放棄、逾時)
- [ ] 運行 `node verify-metrics.js` 查看結果
- [ ] Lift 計算正確
- [ ] 根據結果做出決策 (保留/優化/移除)

---

## 🎓 延伸學習

### A/B 測試最佳實踐
- **樣本量計算**：使用統計顯著性計算器
- **實驗時長**：至少 1-2 週，包含工作日和週末
- **流量分配**：50/50 分流 (Control vs Treatment)
- **統計顯著性**：p-value < 0.05

### 進階指標
- **Average Order Value (AOV)**：平均訂單金額
- **Time to Purchase**：從進入結帳到完成的平均時間
- **Abandonment by Timer State**：依計時器剩餘時間分析放棄率

---

## 🆘 常見問題

### Q: 為什麼看不到任何數據？
A:
1. 確認 backend server 正在運行
2. 檢查瀏覽器 Console 是否有 Analytics 追蹤日誌
3. 確認 localStorage 中有 `analytics_session_id`
4. 檢查數據庫中是否有 `analytics_events` 表格

### Q: Control 和 Treatment 組的數據差異很大怎麼辦？
A:
1. 確保樣本量足夠大 (每組至少 30+ sessions)
2. 檢查是否在同一時間段收集數據
3. 確認 Feature Flag 切換正確

### Q: Session ID 是如何生成的？
A:
- 使用 `localStorage` 儲存
- 格式：`session_<timestamp>_<random>`
- 同一瀏覽器/設備會維持相同 session
- 清除 localStorage 會產生新 session

---

## 📚 相關文件

- [HDD_IMPLEMENTATION.md](HDD_IMPLEMENTATION.md) - 完整 HDD 實作文檔
- [backend/routes/analytics.js](backend/routes/analytics.js) - Analytics API 實作
- [verify-metrics.js](verify-metrics.js) - 驗證腳本原始碼
- [checkout.html](checkout.html) - 結帳頁面實作

---

**✨ 祝測試順利！有任何問題歡迎參考文檔或聯繫開發團隊。**
