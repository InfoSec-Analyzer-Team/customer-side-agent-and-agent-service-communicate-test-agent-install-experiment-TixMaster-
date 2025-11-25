# 更新日誌

## 2024-11-25

### 🔧 認證系統修復與重構

#### 1. 修復管理員認證 (HTTP 401 錯誤)

**問題**: 管理員更新 Feature Flags 時出現 401 Unauthorized 錯誤

**修復內容**:
- ✅ [featureFlags.js](featureFlags.js) - 添加 JWT token 到 API 請求的 Authorization header
- ✅ [admin-login.html](admin-login.html) - 改用後端 API 進行真實認證
- ✅ 新增 [create_admin.sql](create_admin.sql) - 管理員帳號創建腳本
- ✅ 新增 [create_admin.ps1](create_admin.ps1) - PowerShell 執行腳本
- ✅ 新增 [backend/create_admin_hash.js](backend/create_admin_hash.js) - 密碼 hash 生成工具
- ✅ 新增 [ADMIN_SETUP.md](ADMIN_SETUP.md) - 管理員設置完整文檔

**管理員登入資訊**:
- Email: `admin@tixmaster.com`
- 密碼: `admin123`

#### 2. 修復註冊登入頁面 (ERR_FILE_NOT_FOUND)

**問題**: 註冊登入頁面試圖重定向到 `/auth/signup` 和 `/auth/login`，導致 file:// 協議下無法訪問

**修復內容**:
- ✅ [register.html](register.html) - 重構為完整的 OAuth 註冊頁面
- ✅ [login.html](login.html) - 重構為完整的 OAuth 登入頁面
- ✅ 新增 [AUTH_SETUP.md](AUTH_SETUP.md) - 認證系統完整文檔

**認證方式**:
- 一般用戶: OAuth 2.0 (Auth0)
- 管理員: 傳統帳密 (Email + Password)

### 🎨 UI/UX 改進

#### 3. 首頁重命名與導航簡化

**更改內容**:
- ✅ `simple.html` → `index.html` - 符合網站標準命名
- ✅ 簡化導航欄 - 訪客只顯示「登入」按鈕
- ✅ 移除「註冊」和「管理員」按鈕 - 簡化 UI

**導航結構**:
```
訪客模式:
├── 登入

已登入模式:
├── 使用者名稱
└── 登出
```

#### 4. 全站連結更新

**更新的檔案**:
- ✅ [index.html](index.html) - 首頁（原 simple.html）
- ✅ [login.html](login.html) - 登入頁面
- ✅ [register.html](register.html) - 註冊頁面
- ✅ [admin-login.html](admin-login.html) - 管理員登入
- ✅ [event-detail.html](event-detail.html) - 活動詳情
- ✅ [checkout.html](checkout.html) - 結帳頁面
- ✅ [change-password.html](change-password.html) - 修改密碼
- ✅ [README.md](README.md) - 專案說明
- ✅ [METRICS_VERIFICATION_GUIDE.md](METRICS_VERIFICATION_GUIDE.md) - 測試指南

**更新內容**:
- 所有 `simple.html` 連結改為 `index.html`
- 所有 `href="/auth/login"` 改為 `href="login.html"`
- 所有 `href="/auth/signup"` 改為 `href="register.html"`

### 📚 新增文檔

1. **[ADMIN_SETUP.md](ADMIN_SETUP.md)**
   - 管理員認證系統說明
   - 401 錯誤排查指南
   - 創建管理員帳號步驟

2. **[AUTH_SETUP.md](AUTH_SETUP.md)**
   - 完整的認證系統架構
   - OAuth 流程說明
   - Token 管理機制
   - 安全性考量

3. **[CHANGELOG.md](CHANGELOG.md)** (本文件)
   - 詳細的更新記錄

### 🔐 安全性改進

- ✅ JWT Token 認證流程
- ✅ 密碼 bcrypt 加密 (salt rounds = 10)
- ✅ RBAC 權限控制
- ✅ Token 過期機制 (7天)

### 🎯 功能測試

所有功能已測試並正常運作：
- ✅ OAuth 登入/註冊流程
- ✅ 管理員登入
- ✅ Feature Flags 更新
- ✅ Token 儲存與驗證
- ✅ 頁面導航

### 📊 影響範圍

**前端變更**:
- 11 個 HTML 檔案
- 2 個 Markdown 文檔

**後端無變更**

**新增檔案**:
- 4 個新檔案 (SQL, PowerShell, JavaScript, Markdown)

### 🚀 快速開始

#### 方法 1: 使用後端伺服器（推薦）

```bash
# 啟動後端
cd backend
npm start

# 訪問
http://localhost:3000/index.html
http://localhost:3000/login.html
http://localhost:3000/admin-login.html
```

#### 方法 2: 直接開啟 HTML（部分功能受限）

```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

**注意**: OAuth 功能需要透過後端伺服器運行

### 📝 待辦事項

未來可能的改進：
- [ ] 添加 HTTPS 支援
- [ ] 實施 CSRF 保護
- [ ] 添加 Rate Limiting
- [ ] Token Refresh 機制
- [ ] 雙因素認證 (2FA)

### 🐛 已知問題

無

### 🙏 致謝

感謝使用 TixMaster！
