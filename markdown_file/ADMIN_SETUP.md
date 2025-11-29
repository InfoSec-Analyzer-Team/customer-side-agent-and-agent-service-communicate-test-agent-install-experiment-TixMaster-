# 管理員帳號設置說明

## 問題修復

已修復 **HTTP 401 Unauthorized** 錯誤。

### 問題原因

1. 後端 API `/api/feature-flags/:key` (PUT) 需要 JWT token 認證
2. 前端 `featureFlags.js` 沒有在請求中發送 Authorization header
3. 管理員登入只使用 localStorage 存儲，沒有獲取真正的 JWT token

### 已修復的檔案

1. **featureFlags.js** - 添加了 Authorization header 支持
2. **admin-login.html** - 改為調用後端 API 進行真實認證

## 創建管理員帳號

### ⚠️ 重要：先執行資料庫遷移

如果遇到 "password_hash column does not exist" 錯誤，需要先執行遷移：

```bash
cd backend
node migrate_database.js
```

### 方法 1: 使用 Node.js 腳本（推薦）✨

```bash
cd backend
node create_admin_account.js
```

這個方法會：
- ✅ 自動檢查帳號是否已存在
- ✅ 使用正確的密碼 hash
- ✅ 顯示創建結果

### 方法 2: 使用 PowerShell 腳本

```powershell
cd c:\_AG11\TixMaster
.\create_admin.ps1
```

### 方法 3: 手動執行 SQL

```powershell
cd c:\_AG11\TixMaster
psql -U postgres -d tixmaster -f create_admin.sql
```

### 方法 4: 直接執行 SQL 命令

```sql
INSERT INTO users (email, password_hash, name, phone, role)
VALUES ('admin@tixmaster.com', '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG', 'System Admin', '0900000000', 'admin');
```

## 管理員登入資訊

- **URL**: http://localhost:3000/admin-login.html
- **Email**: `admin@tixmaster.com`
- **密碼**: `admin123`

## 使用說明

1. 確保後端伺服器正在運行：
   ```bash
   cd backend
   npm start
   ```

2. 創建管理員帳號（使用上述任一方法）

3. 在瀏覽器打開管理員登入頁面

4. 輸入登入資訊並登入

5. 現在可以正常更新 Feature Flags 了！

## 安全提醒

⚠️ **重要**: 在正式環境中，請務必：
1. 修改預設管理員密碼
2. 使用強密碼
3. 啟用 HTTPS
4. 考慮添加雙因素認證 (2FA)

## 測試

可以使用以下方式測試功能是否正常：

1. 登入管理員後台
2. 嘗試切換任一 Feature Flag 開關
3. 應該會顯示成功訊息，而不是 401 錯誤

## 技術細節

### JWT Token 流程

1. 管理員登入時，後端驗證帳密並返回 JWT token
2. Token 存儲在 localStorage 中
3. 更新 Feature Flag 時，從 localStorage 讀取 token
4. Token 放在 `Authorization: Bearer <token>` header 中發送
5. 後端驗證 token 和權限後執行更新

### 權限檢查

後端使用 RBAC (Role-Based Access Control) 檢查：
- 需要 `authenticateToken` middleware 驗證 JWT
- 需要 `checkPermission(PERMISSIONS.MANAGE_FEATURE_FLAGS)` 驗證權限
- 只有 `role = 'admin'` 的用戶才有權限

## 故障排除

### 問題 1: 無法登入 - "Invalid credentials"

**診斷步驟**:

```bash
cd backend

# 1. 檢查管理員帳號是否存在
node check_admin.js

# 2. 檢查資料庫結構
node check_schema.js
```

**解決方案**:

如果帳號不存在：
```bash
node create_admin_account.js
```

如果缺少 password_hash 欄位：
```bash
node migrate_database.js
```

### 問題 2: "password_hash column does not exist"

**原因**: 資料庫 schema 缺少 password_hash 欄位

**解決方案**:
```bash
cd backend
node migrate_database.js
```

### 問題 3: 仍然出現 401 錯誤

**檢查清單**:

1. ✅ 後端是否正在運行
   ```bash
   cd backend
   npm start
   ```

2. ✅ 檢查瀏覽器 Console 是否有錯誤
   - 按 F12 打開開發者工具
   - 查看 Console 和 Network 標籤

3. ✅ 確認 localStorage 中有 adminUser.token
   ```javascript
   // 在瀏覽器 Console 執行
   JSON.parse(localStorage.getItem('adminUser'))
   ```

4. ✅ 確認用戶的 role 是 'admin'
   ```bash
   node check_admin.js
   ```

### 問題 4: 登入成功但提示沒有權限

**原因**: 用戶角色不是 'admin'

**解決方案**:
```sql
-- 直接在資料庫中更新
UPDATE users SET role = 'admin' WHERE email = 'admin@tixmaster.com';
```

### 測試登入 API

測試後端 API 是否正常：

```bash
cd backend
node test_admin_login.js
```

應該看到：
```
✅ 登入成功！
✅ 角色驗證通過：管理員
```

### 查看用戶角色

```sql
SELECT id, email, name, role FROM users WHERE email = 'admin@tixmaster.com';
```

或使用工具：
```bash
cd backend
node check_admin.js
```

### 重置管理員密碼

```sql
-- 更新為新的密碼 hash（admin123）
UPDATE users
SET password_hash = '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG'
WHERE email = 'admin@tixmaster.com';
```
