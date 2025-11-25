# 認證系統說明

## 系統架構

TixMaster 使用 **OAuth 2.0 (Auth0)** 作為唯一的用戶認證方式。

### 認證流程

1. **用戶點擊登入/註冊** → 前端頁面 ([login.html](login.html) / [register.html](register.html))
2. **導向 Auth0** → 透過後端路由 `/auth/login` 或 `/auth/signup`
3. **Auth0 認證** → 用戶在 Auth0 頁面進行登入/註冊
4. **回調處理** → Auth0 重定向到 `/auth/callback`
5. **JWT 簽發** → 後端簽發 JWT token 並透過 URL fragment 返回
6. **Token 儲存** → 前端解析並儲存 token 到 localStorage
7. **導向首頁** → 用戶完成登入

## 頁面說明

### 1. [register.html](register.html) - 註冊頁面
- 提供 "使用 Auth0 註冊" 按鈕
- 點擊後導向 `http://localhost:3000/auth/signup`
- 顯示錯誤處理（如有）

### 2. [login.html](login.html) - 登入頁面
- 提供 "使用 Auth0 登入" 按鈕
- 提供 "管理員登入" 按鈕（導向 [admin-login.html](admin-login.html)）
- 處理 OAuth callback 返回的 token
- 自動解析 token 並儲存用戶資訊

### 3. [admin-login.html](admin-login.html) - 管理員登入
- 使用傳統帳密登入（Email + Password）
- 調用後端 API `/api/users/login`
- 驗證用戶 role 必須為 `admin`
- 成功後導向 [admin-dashboard.html](admin-dashboard.html)

## 後端路由

### OAuth 路由 ([backend/routes/oauth.js](backend/routes/oauth.js))

| 路由 | 方法 | 說明 |
|------|------|------|
| `/auth/login` | GET | 啟動 Auth0 登入流程 |
| `/auth/signup` | GET | 啟動 Auth0 註冊流程 |
| `/auth/callback` | GET | 處理 Auth0 回調並簽發 JWT |
| `/auth/logout` | GET | 登出功能 |
| `/auth/status` | GET | 檢查登入狀態 |

### 用戶 API 路由 ([backend/routes/users.js](backend/routes/users.js))

| 路由 | 方法 | 說明 |
|------|------|------|
| `/api/users/register` | POST | 傳統註冊（已停用前端） |
| `/api/users/login` | POST | 傳統登入（僅供管理員） |
| `/api/users/profile` | GET | 獲取用戶資料（需認證） |
| `/api/users/profile` | PUT | 更新用戶資料（需認證） |

## Token 管理

### localStorage 結構

```javascript
// 一般用戶
localStorage.setItem('authToken', '<JWT_TOKEN>');
localStorage.setItem('currentUser', JSON.stringify({
    id: userId,
    email: email,
    role: role
}));

// 管理員
localStorage.setItem('adminUser', JSON.stringify({
    username: name,
    email: email,
    token: '<JWT_TOKEN>',
    role: 'admin',
    loginTime: timestamp
}));
```

### JWT Payload 結構

```json
{
  "userId": 123,
  "email": "user@example.com",
  "role": "user",
  "loginMethod": "auth0",
  "iat": 1234567890,
  "exp": 1234567890
}
```

## 使用方式

### 1. 啟動後端伺服器

```bash
cd backend
npm start
```

伺服器會在 `http://localhost:3000` 運行

### 2. 設置 Auth0（如果尚未設置）

在 `backend/.env` 中配置：

```env
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_DOMAIN=your_domain.auth0.com
AUTH0_CALLBACK_URL=http://localhost:3000/auth/callback
JWT_SECRET=your_jwt_secret
```

### 3. 訪問登入頁面

- 一般用戶登入: http://localhost:3000/login.html
- 註冊新用戶: http://localhost:3000/register.html
- 管理員登入: http://localhost:3000/admin-login.html

## 管理員設置

### 創建管理員帳號

```powershell
# 方法 1: 使用腳本
.\create_admin.ps1

# 方法 2: 手動執行 SQL
psql -U postgres -d tixmaster -f create_admin.sql
```

### 管理員登入資訊

- **URL**: http://localhost:3000/admin-login.html
- **Email**: `admin@tixmaster.com`
- **密碼**: `admin123`

## 安全性考量

### 已實施的安全措施

1. ✅ JWT Token 認證
2. ✅ RBAC 權限控制
3. ✅ 密碼 bcrypt 加密
4. ✅ OAuth 2.0 認證
5. ✅ Token 過期機制（7天）

### 建議的額外措施（正式環境）

1. 🔒 啟用 HTTPS
2. 🔒 實施 CSRF 保護
3. 🔒 添加 Rate Limiting
4. 🔒 啟用雙因素認證 (2FA)
5. 🔒 Token Refresh 機制
6. 🔒 定期更換 JWT Secret

## 故障排除

### 問題 1: 登入後出現 ERR_FILE_NOT_FOUND

**原因**: 使用 `file://` 協議打開頁面，無法訪問後端 API

**解決**:
- 使用 `http://localhost:3000/login.html` 訪問
- 確保後端伺服器正在運行

### 問題 2: OAuth 認證失敗

**檢查**:
1. Auth0 設定是否正確
2. Callback URL 是否配置正確
3. `.env` 檔案是否存在且正確

### 問題 3: 管理員無法更新 Feature Flags (401 錯誤)

**解決**: 參考 [ADMIN_SETUP.md](ADMIN_SETUP.md)

1. 確認已創建管理員帳號
2. 使用管理員帳號登入
3. 確認 localStorage 中有 `adminUser.token`

## 相關文件

- [ADMIN_SETUP.md](ADMIN_SETUP.md) - 管理員設置說明
- [backend/RBAC-ABAC-GUIDE.md](backend/RBAC-ABAC-GUIDE.md) - 權限控制指南
- [backend/API_TESTING_GUIDE.md](backend/API_TESTING_GUIDE.md) - API 測試指南

## 開發資訊

### 測試帳號（開發用）

建議在開發環境中創建測試帳號：

```sql
-- 一般用戶測試帳號
INSERT INTO users (email, password_hash, name, role)
VALUES ('test@example.com', '$2b$10$...', 'Test User', 'user');

-- 主辦方測試帳號
INSERT INTO users (email, password_hash, name, role)
VALUES ('organizer@example.com', '$2b$10$...', 'Organizer', 'organizer');
```

### API 測試

使用 Postman 或 curl 測試 API：

```bash
# 測試登入
curl -X POST http://localhost:3000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tixmaster.com","password":"admin123"}'

# 測試受保護的路由
curl -X GET http://localhost:3000/api/users/profile \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## 更新日誌

### 2024-11-25
- ✅ 修復 401 Unauthorized 錯誤
- ✅ 重構 register.html 和 login.html 使用 OAuth
- ✅ 添加管理員認證支持
- ✅ 改進錯誤處理和用戶體驗
