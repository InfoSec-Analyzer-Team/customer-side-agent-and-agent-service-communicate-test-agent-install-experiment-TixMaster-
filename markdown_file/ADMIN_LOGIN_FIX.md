# 管理員登入問題修復指南

## 問題描述

管理員無法登入 - 已完全修復！✅

## 根本原因

1. ❌ **資料庫缺少 `password_hash` 欄位** - users 表中沒有存儲密碼的欄位
2. ❌ **管理員帳號未創建** - 資料庫中沒有管理員記錄

## 解決方案

### ✅ 已執行的修復步驟

1. **添加 password_hash 欄位**
   ```bash
   cd backend
   node migrate_database.js
   ```
   - 執行了資料庫遷移
   - 添加了 `password_hash VARCHAR(255)` 欄位到 users 表

2. **創建管理員帳號**
   ```bash
   node create_admin_account.js
   ```
   - 創建了管理員帳號
   - Email: admin@tixmaster.com
   - 密碼: admin123 (bcrypt hash)
   - 角色: admin

3. **驗證登入 API**
   ```bash
   node test_admin_login.js
   ```
   - ✅ API 測試通過
   - ✅ Token 生成成功
   - ✅ 角色驗證通過

## 現在可以登入了！

### 登入步驟

1. **確保後端運行**
   ```bash
   cd backend
   npm start
   ```
   服務器應該在 http://localhost:3000 運行

2. **訪問管理員登入頁面**
   ```
   http://localhost:3000/admin-login.html
   ```

3. **輸入登入資訊**
   - Email: `admin@tixmaster.com`
   - 密碼: `admin123`

4. **點擊「登入管理後台」**
   - 系統會調用 `/api/users/login` API
   - 驗證帳密並生成 JWT token
   - 檢查角色是否為 admin
   - 成功後導向 admin-dashboard.html

## 新增的工具腳本

在 `backend/` 目錄下新增了以下工具：

### 1. `check_admin.js` - 檢查管理員帳號
```bash
node check_admin.js
```
顯示管理員帳號是否存在及其詳細資訊

### 2. `check_schema.js` - 檢查資料庫結構
```bash
node check_schema.js
```
顯示 users 表的完整結構

### 3. `migrate_database.js` - 執行資料庫遷移
```bash
node migrate_database.js
```
添加缺少的 password_hash 欄位

### 4. `create_admin_account.js` - 創建管理員帳號
```bash
node create_admin_account.js
```
在資料庫中創建管理員帳號

### 5. `test_admin_login.js` - 測試登入 API
```bash
node test_admin_login.js
```
測試管理員登入是否正常運作

### 6. `add_password_hash.sql` - SQL 遷移腳本
直接執行的 SQL 腳本，用於添加 password_hash 欄位

## 快速設置（一鍵完成）

如果需要重新設置或在新環境中部署：

```bash
cd backend

# 1. 遷移資料庫（添加 password_hash 欄位）
node migrate_database.js

# 2. 創建管理員帳號
node create_admin_account.js

# 3. 測試登入（可選）
node test_admin_login.js
```

## 驗證清單

完成以下檢查確保一切正常：

- [x] users 表有 password_hash 欄位
- [x] 管理員帳號已創建 (admin@tixmaster.com)
- [x] 登入 API 測試通過
- [x] Token 生成正常
- [x] 角色驗證為 admin

## 故障排除

### 問題 1: 登入時出現 "Invalid credentials"

**可能原因**:
- 密碼錯誤
- 管理員帳號不存在

**解決方法**:
```bash
# 檢查帳號是否存在
node check_admin.js

# 如不存在，重新創建
node create_admin_account.js
```

### 問題 2: 登入成功但提示 "此帳號沒有管理員權限"

**可能原因**:
- 用戶角色不是 'admin'

**解決方法**:
```sql
-- 手動更新角色
UPDATE users SET role = 'admin' WHERE email = 'admin@tixmaster.com';
```

### 問題 3: 出現 "password_hash column does not exist"

**可能原因**:
- 資料庫遷移未執行

**解決方法**:
```bash
node migrate_database.js
```

### 問題 4: 無法連接到資料庫

**檢查**:
1. PostgreSQL 是否運行
2. `.env` 檔案設置是否正確
3. 資料庫 tixmaster 是否存在

## 資料庫結構

### 更新後的 users 表

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),      -- 新增：用於傳統帳密登入
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) DEFAULT 'user', -- RBAC 角色
    attributes JSONB DEFAULT '{}',   -- ABAC 屬性
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## 安全提醒

⚠️ **正式環境注意事項**:

1. **修改預設密碼**
   ```sql
   -- 生成新的 hash（在 Node.js 中）
   const bcrypt = require('bcrypt');
   const hash = await bcrypt.hash('your-new-password', 10);

   -- 更新資料庫
   UPDATE users SET password_hash = 'new-hash' WHERE email = 'admin@tixmaster.com';
   ```

2. **使用環境變數**
   - 不要在程式碼中硬編碼密碼
   - JWT_SECRET 要足夠複雜

3. **啟用 HTTPS**
   - 正式環境必須使用 HTTPS
   - 保護 token 和密碼傳輸

4. **定期更換密碼**
   - 建議每 90 天更換一次

## 相關文檔

- [ADMIN_SETUP.md](ADMIN_SETUP.md) - 管理員設置詳細指南
- [AUTH_SETUP.md](AUTH_SETUP.md) - 認證系統架構
- [CHANGELOG.md](CHANGELOG.md) - 更新記錄

## 更新記錄

### 2024-11-25

- ✅ 修復資料庫 schema（添加 password_hash 欄位）
- ✅ 創建管理員帳號
- ✅ 驗證登入流程
- ✅ 新增診斷和設置工具
- ✅ 更新文檔

---

**狀態**: ✅ 已完全修復，可以正常登入！
