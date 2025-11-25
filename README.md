# 🎫 TixMaster - 售票系統

> **DevSecOps 售票平台** | 整合 HDD 假設驗證與流量控制

## 📋 專案簡介

TixMaster 是一個現代化的售票系統，採用 **Hypothesis-Driven Development (HDD)** 方法論，透過功能開關 (Feature Toggles) 進行 A/B Testing，同時具備完整的流量控制機制。

**核心特色：**
- ✅ 完整的使用者註冊/登入系統
- ✅ 活動展示與詳細資訊頁面
- ✅ 購票數量選擇與即時價格計算
- ✅ HDD 功能開關（觀看人數、倒數計時）
- ✅ 資料庫完整設計（8 個核心資料表）
- ✅ 安全設計（bcrypt 密碼雜湊）

---

## 📁 檔案結構

```
TixMaster/
├── index.html               # 🏠 首頁（活動列表）
├── register.html            # 📝 使用者註冊頁面
├── login.html               # 🔐 使用者登入頁面
├── event-detail.html        # 🎤 活動詳情頁面（購票）
├── database_schema.md       # 💾 資料庫設計文件
└── README.md                # 📖 本文件
```

---

## 🚀 快速開始

### 方法一：直接開啟 HTML 檔案

1. **瀏覽活動**
   ```
   雙擊開啟 index.html
   ```

2. **註冊帳號**
   ```
   雙擊開啟 register.html
   填寫：姓名、Email、手機、密碼
   ```

3. **登入系統**
   ```
   註冊成功後自動跳轉到 login.html
   輸入 Email 和密碼登入
   ```

4. **查看活動詳情**
   ```
   雙擊開啟 event-detail.html
   選擇票數、查看總價
   ```

### 方法二：使用瀏覽器開啟

```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

---

## 🎯 功能清單

### ✅ 已完成功能

#### 1. 使用者管理
- [x] 註冊頁面（含表單驗證）
  - Email 格式驗證
  - 密碼長度檢查（至少 6 字元）
  - 密碼確認功能
  - 重複 Email 檢測
- [x] 登入頁面
  - Email + 密碼登入
  - localStorage 驗證（模擬）

#### 2. 活動展示
- [x] 活動列表頁面
  - 活動卡片展示
  - 基本資訊（標題、日期、地點、價格）
- [x] 活動詳情頁面
  - Hero 大圖展示
  - 完整活動資訊
  - 觀看人數顯示（HDD 功能）
  - 購票數量選擇器（+/-）
  - 即時總價計算

#### 3. 資料庫設計
- [x] 8 個核心資料表
  - `users` - 使用者
  - `login_sessions` - 登入 Session
  - `oauth_accounts` - 第三方登入
  - `events` - 活動
  - `tickets` - 票種
  - `orders` - 訂單
  - `order_items` - 訂單明細
  - `waiting_queue` - 等待隊列
  - `feature_flags` - 功能開關
  - `analytics_events` - 分析數據

### 🔜 待完成功能

- [ ] 結帳頁面
- [ ] 訂單確認
- [ ] 後端 API 整合
- [ ] 真實的資料庫連接
- [ ] 付款系統整合

---

## 💾 資料庫設計

詳細設計請查看 [`database_schema.md`](database_schema.md)

### 核心資料表

```
users (使用者)
├── id, email, password_hash (bcrypt)
├── name, phone
└── created_at, updated_at

login_sessions (登入狀態)
├── session_token, user_id
├── ip_address, user_agent
└── expires_at

events (活動)
├── title, description
├── event_date, location
└── image_url, status

tickets (票種)
├── event_id, ticket_type
├── price, total_quantity
└── available_quantity

orders (訂單)
├── order_number, user_id
├── event_id, ticket_id
├── quantity, total_amount
└── status, payment_method
```

### 安全機制

1. **密碼加密**
   ```javascript
   // 後端使用 bcrypt
   const hashedPassword = await bcrypt.hash(password, 10);
   ```

2. **Session 管理**
   - 唯一的 session_token
   - 自動過期機制（24 小時或 7 天）

3. **防超賣機制**
   ```sql
   -- 使用交易鎖定
   BEGIN TRANSACTION;
   SELECT available_quantity FROM tickets WHERE id = ? FOR UPDATE;
   UPDATE tickets SET available_quantity = available_quantity - ?;
   COMMIT;
   ```

---

## 🔧 技術細節

### 前端技術
- **HTML5** - 語義化標籤
- **CSS3** - 響應式設計、漸層效果
- **JavaScript (ES6+)** - 表單驗證、DOM 操作

### 資料儲存（目前）
- **localStorage** - 模擬後端資料儲存
- 等待外包廠商完成資料庫後，將所有 `localStorage` 呼叫改為 API

### 表單驗證範例

```javascript
// Email 格式驗證
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
  showError('請輸入有效的 Email');
}

// 密碼長度檢查
if (password.length < 6) {
  showError('密碼至少需要 6 個字元');
}

// 密碼確認
if (password !== confirmPassword) {
  showError('密碼不一致');
}
```

---

## 🎨 HDD 功能開關

### 觀看人數顯示
- **位置**：活動詳情頁
- **功能**：顯示「X 人正在瀏覽此活動」
- **目的**：利用社交證明 (Social Proof) 提升購票意願

### 倒數計時器
- **位置**：結帳頁面
- **功能**：10 分鐘倒數計時
- **目的**：製造急迫感，提升結帳完成率

---

## 📊 API 端點規劃

待後端整合時實作：

```
POST   /api/register        # 使用者註冊
POST   /api/login           # 使用者登入
GET    /api/events          # 取得活動列表
GET    /api/events/:id      # 取得活動詳情
POST   /api/orders          # 建立訂單
GET    /api/orders/:id      # 查詢訂單
```

---

## 🔐 安全建議

### 生產環境必須實作

1. **HTTPS**
   - 所有連線必須使用 SSL/TLS 加密

2. **CSRF Protection**
   - 使用 CSRF Token 防止跨站請求偽造

3. **Rate Limiting**
   - 限制 API 呼叫頻率，防止暴力破解

4. **SQL Injection 防護**
   - 使用 Prepared Statements
   - 永不直接拼接 SQL 字串

5. **XSS 防護**
   - 所有使用者輸入需經過 HTML 轉義

---

## 📝 開發團隊

| 角色 | 成員 | 職責 |
|------|------|------|
| **Project Manager** | YeMiao1026 | 專案管理、HDD 假設制定 |
| **Full-Stack Developer** | Galin12341 | 前端開發、Feature Toggles |
| **DB Manager / Ops** | Saisai568 | 資料庫設計、部署 |
| **Tester** | ww123 | 測試、品質保證 |

---

## 📞 聯絡資訊

有任何問題請聯繫專案團隊成員。

---

## 📜 授權

本專案為 DevSecOps 課程作業，僅供教學使用。

---

## 🎉 下一步

1. ✅ 完成前端頁面
2. ⏳ 等待外包完成資料庫
3. 🔜 串接後端 API
4. 🔜 實作結帳流程
5. 🔜 部署到雲端平台

**目前進度：前端完成 ✅ | 資料庫設計完成 ✅** 

---

## 🧪 CI / 自動化測試 (GitHub Actions)

已將測試整合到 GitHub Actions：工作流程檔案位於 `.github/workflows/ci.yml`。CI 會在 push / pull_request 到 `main` 或 `dev_front_end` 時執行：

- 依序安裝 Python 與 Node 環境
- 安裝 Python 與 npm 開發套件
- 執行 `pytest`（產生 `reports/test-report.html` 與 `reports/tests-junit.xml`）
- 執行 Playwright E2E（產生 `reports/playwright-report`）
- 上傳 `reports/` 作為工作產物

必要的 GitHub Secret（請在 repo Settings -> Secrets 中設定）：

- `JWT_SECRET`：用來在 CI 中產生本地 admin JWT（`tools/gen_admin_jwt.js` 會從 `backend/.env` 或此 secret 讀取），建議只在 CI 中以 secrets 提供。

如何在 CI 中產生 admin token：

- workflow 內會把 `JWT_SECRET` 寫入 `backend/.env`（當 secret 存在時），然後執行 `node tools/gen_admin_jwt.js` 並把輸出放入 `ADMIN_TOKEN` 環境變數，供 Playwright 與 pytest 使用。

注意：`tools/gen_admin_jwt.js` 現在會優先使用環境變數 `JWT_SECRET`（例如 CI secrets），如果本地未提供，會回退到 `backend/.env` 中的 `JWT_SECRET`（若存在）。建議在 CI/自動化環境使用 `JWT_SECRET` secret，並在本機開發時透過環境變數或臨時 `backend/.env` 提供。

查看報告：

- Playwright HTML report：`reports/playwright-report/index.html`（或在 CI 用 `npx playwright show-report`）
- pytest HTML report：`reports/test-report.html`
- JUnit XML：`reports/tests-junit.xml`

本地模擬 CI（單機開發環境）指令：

PowerShell (Windows):
```powershell
# 產生 admin token (選填，若使用 backend/.env 的 JWT_SECRET)
node tools/gen_admin_jwt.js > admin.token
$env:ADMIN_TOKEN = Get-Content admin.token -Raw

# 安裝（一次）
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
npm ci
npx playwright install --with-deps

# 執行 pytest
pytest -q --junitxml=reports/tests-junit.xml --html=reports/test-report.html

# 執行 Playwright
npx playwright test --reporter=html

# 打開 Playwright report（本機）
npx playwright show-report
```

Linux / macOS (bash):
```bash
# (同上)
node tools/gen_admin_jwt.js > admin.token
export ADMIN_TOKEN=$(cat admin.token)
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
npm ci
npx playwright install --with-deps
pytest -q --junitxml=reports/tests-junit.xml --html=reports/test-report.html
npx playwright test --reporter=html
npx playwright show-report
```

安全與 CI 建議：

- 在 CI 中使用 GitHub Secrets 提供 `JWT_SECRET`，請不要把機敏資料直接加入 repo。
- 若將來要加入真實資料庫測試，請在 CI 使用受控的測試資料庫（或 GitHub Actions 的 ephemeral DB）並把連線字串放入 secrets（例如 `DATABASE_URL`）。
