# TixMaster 資料庫設計

## 核心資料表

### 1. users (使用者)
管理所有註冊使用者的基本資料

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 使用者ID | Primary Key, Auto Increment |
| email | VARCHAR(255) | Email | Unique, Not Null |
| password_hash | VARCHAR(255) | 密碼雜湊 (bcrypt) | Not Null |
| name | VARCHAR(100) | 姓名 | Not Null |
| phone | VARCHAR(20) | 電話 | |
| created_at | TIMESTAMP | 建立時間 | Default CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新時間 | On Update CURRENT_TIMESTAMP |

---

### 2. login_sessions (登入Session)
管理使用者的登入狀態和 Session

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | Session ID | Primary Key, Auto Increment |
| user_id | INT | 使用者ID | Foreign Key -> users(id) |
| session_token | VARCHAR(255) | Session Token | Unique, Not Null |
| ip_address | VARCHAR(45) | IP地址 | 支援 IPv6 |
| user_agent | VARCHAR(500) | 瀏覽器資訊 | |
| expires_at | TIMESTAMP | 過期時間 | Not Null |
| created_at | TIMESTAMP | 建立時間 | Default CURRENT_TIMESTAMP |
| last_activity | TIMESTAMP | 最後活動時間 | On Update CURRENT_TIMESTAMP |

**索引：**
- UNIQUE INDEX on `session_token`
- INDEX on `user_id`
- INDEX on `expires_at`

**說明：**
- 使用者登入後產生唯一的 `session_token`
- Session 有效期限通常為 24 小時或 7 天（記住我）
- 定時清理過期的 Session

---


**用途：**
- 安全監控（偵測異常登入）
- 帳號安全提醒
- 防暴力破解（同一 IP 短時間內多次失敗）

---

### 5. oauth_accounts (第三方登入)
儲存 OAuth 登入資訊（Google、Facebook 等）

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | ID | Primary Key, Auto Increment |
| user_id | INT | 使用者ID | Foreign Key -> users(id) |
| provider | VARCHAR(50) | 提供者 | 'google', 'facebook', 'line' |
| provider_user_id | VARCHAR(255) | 第三方使用者ID | |
| access_token | TEXT | Access Token | 加密儲存 |
| refresh_token | TEXT | Refresh Token | 加密儲存 |
| token_expires_at | TIMESTAMP | Token過期時間 | |
| created_at | TIMESTAMP | 綁定時間 | Default CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新時間 | On Update CURRENT_TIMESTAMP |

**索引：**
- INDEX on `user_id`
- UNIQUE INDEX on `provider`, `provider_user_id`

---

### 6. events (活動)
儲存所有活動的基本資訊

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 活動ID | Primary Key, Auto Increment |
| title | VARCHAR(200) | 活動標題 | Not Null |
| description | TEXT | 活動說明 | |
| event_date | DATETIME | 活動日期時間 | Not Null |
| location | VARCHAR(200) | 地點 | Not Null |
| image_url | VARCHAR(500) | 圖片網址 | |
| status | ENUM | 狀態 | 'draft', 'published', 'sold_out', 'cancelled' |
| created_at | TIMESTAMP | 建立時間 | Default CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新時間 | On Update CURRENT_TIMESTAMP |

---

### 3. tickets (票種)
定義每個活動的票種和價格

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 票種ID | Primary Key, Auto Increment |
| event_id | INT | 活動ID | Foreign Key -> events(id) |
| ticket_type | VARCHAR(50) | 票種名稱 | 例如：一般票、VIP票 |
| price | DECIMAL(10,2) | 票價 | Not Null |
| total_quantity | INT | 總數量 | Not Null |
| available_quantity | INT | 剩餘數量 | Not Null, 初始值 = total_quantity |
| created_at | TIMESTAMP | 建立時間 | Default CURRENT_TIMESTAMP |

**索引：**
- INDEX on `event_id`

---

### 4. orders (訂單)
所有購票訂單記錄

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 訂單ID | Primary Key, Auto Increment |
| order_number | VARCHAR(50) | 訂單編號 | Unique, 例如：TM20251124-001 |
| user_id | INT | 使用者ID | Foreign Key -> users(id) |
| event_id | INT | 活動ID | Foreign Key -> events(id) |
| ticket_id | INT | 票種ID | Foreign Key -> tickets(id) |
| quantity | INT | 購買數量 | Not Null |
| total_amount | DECIMAL(10,2) | 總金額 | Not Null |
| status | ENUM | 訂單狀態 | 'pending', 'paid', 'cancelled', 'expired' |
| payment_method | VARCHAR(50) | 付款方式 | 例如：信用卡、ATM |
| created_at | TIMESTAMP | 建立時間 | Default CURRENT_TIMESTAMP |
| paid_at | TIMESTAMP | 付款時間 | Nullable |
| expired_at | TIMESTAMP | 逾期時間 | 10分鐘後 |

**索引：**
- INDEX on `user_id`
- INDEX on `event_id`
- INDEX on `status`
- INDEX on `created_at`

---

### 5. order_items (訂單明細)
訂單中的每張票券（如果需要更細的控制）

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 明細ID | Primary Key, Auto Increment |
| order_id | INT | 訂單ID | Foreign Key -> orders(id) |
| ticket_code | VARCHAR(50) | 票券代碼 | Unique, 例如：TM-ABC123 |
| qr_code | TEXT | QR Code | Base64 或路徑 |
| status | ENUM | 票券狀態 | 'valid', 'used', 'cancelled' |
| used_at | TIMESTAMP | 使用時間 | Nullable |

**索引：**
- INDEX on `order_id`
- UNIQUE INDEX on `ticket_code`

---

### 6. waiting_queue (等待隊列)
流量控制用的等待隊列

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | 隊列ID | Primary Key, Auto Increment |
| session_id | VARCHAR(100) | Session ID | Unique |
| user_id | INT | 使用者ID | Foreign Key -> users(id), Nullable |
| event_id | INT | 活動ID | Foreign Key -> events(id), Nullable |
| queue_position | INT | 隊列位置 | |
| status | ENUM | 狀態 | 'waiting', 'processing', 'completed' |
| created_at | TIMESTAMP | 加入時間 | Default CURRENT_TIMESTAMP |
| expires_at | TIMESTAMP | 逾期時間 | |

**索引：**
- INDEX on `session_id`
- INDEX on `event_id`
- INDEX on `status`

---

### 7. feature_flags (功能開關)
HDD 實驗用的功能開關

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | ID | Primary Key, Auto Increment |
| flag_key | VARCHAR(100) | 功能鍵 | Unique, 例如：ENABLE_CHECKOUT_TIMER |
| flag_value | BOOLEAN | 開關狀態 | Default FALSE |
| description | VARCHAR(255) | 說明 | |
| updated_at | TIMESTAMP | 更新時間 | On Update CURRENT_TIMESTAMP |

---

### 8. analytics_events (分析數據)
追蹤使用者行為（A/B Testing）

| 欄位名稱 | 資料類型 | 說明 | 備註 |
|---------|---------|------|------|
| id | INT | ID | Primary Key, Auto Increment |
| user_id | INT | 使用者ID | Foreign Key -> users(id), Nullable |
| session_id | VARCHAR(100) | Session ID | |
| event_type | VARCHAR(50) | 事件類型 | 例如：page_view, button_click |
| event_data | JSON | 事件資料 | 儲存額外資訊 |
| feature_flags | JSON | 當時的功能開關 | 記錄實驗組 |
| created_at | TIMESTAMP | 發生時間 | Default CURRENT_TIMESTAMP |

**索引：**
- INDEX on `user_id`
- INDEX on `event_type`
- INDEX on `created_at`

---

## 資料表關聯圖

```
users (1) ----< (N) orders
events (1) ----< (N) tickets
events (1) ----< (N) orders
tickets (1) ----< (N) orders
orders (1) ----< (N) order_items
```

---

## 重要說明

### 票券庫存控制
- 使用 `tickets.available_quantity` 追蹤剩餘票數
- 下單時需要使用**交易鎖定 (Row-level lock)** 避免超賣：
  ```sql
  BEGIN TRANSACTION;
  SELECT available_quantity FROM tickets WHERE id = ? FOR UPDATE;
  -- 檢查庫存 > 需求量
  UPDATE tickets SET available_quantity = available_quantity - ? WHERE id = ?;
  COMMIT;
  ```

### 訂單逾期處理
- `orders.expired_at` = `created_at` + 10分鐘
- 定時任務 (Cron Job) 每分鐘掃描逾期未付款訂單
- 逾期後：
  1. 更新 `orders.status = 'expired'`
  2. 釋放票券：`UPDATE tickets SET available_quantity = available_quantity + quantity`

### 索引建議
- 所有 Foreign Key 都應該建立索引
- 經常用於查詢條件的欄位建立索引（如 `status`, `created_at`）
- 定期分析查詢性能，調整索引策略

---
