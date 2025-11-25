# 🛡️ RBAC/ABAC 權限控制測試指南

## 📖 目錄

- [簡介](#簡介)
- [權限架構](#權限架構)
- [測試前準備](#測試前準備)
- [快速測試](#快速測試)
- [完整測試流程](#完整測試流程)
- [手動測試範例](#手動測試範例)
- [常見問題](#常見問題)
- [錯誤碼說明](#錯誤碼說明)

---

## 簡介

TixMaster 系統實現了兩種權限控制機制：

### RBAC (Role-Based Access Control)
**基於角色的權限控制** - 根據使用者的角色決定可以存取哪些功能。

### ABAC (Attribute-Based Access Control)
**基於屬性的權限控制** - 根據使用者的屬性（如是否為資源擁有者）決定存取權限。

---

## 權限架構

### 角色定義

| 角色 | 說明 | 權限 |
|------|------|------|
| **`user`** | 一般使用者（預設） | • 查看/編輯自己的資料<br>• 購買票券<br>• 查看活動列表 |
| **`organizer`** | 活動主辦方 | • User 的所有權限<br>• 建立/編輯/刪除活動<br>• 查看分析數據 |
| **`admin`** | 系統管理員 | • 所有權限<br>• 管理使用者<br>• 管理 Feature Flags |

### 權限對照表

| 功能 | User | Organizer | Admin |
|------|:----:|:---------:|:-----:|
| 查看自己的 Profile | ✅ | ✅ | ✅ |
| 更新自己的 Profile | ✅ | ✅ | ✅ |
| 查看所有使用者 | ❌ | ❌ | ✅ |
| 建立活動 | ❌ | ✅ | ✅ |
| 編輯活動 | ❌ | ✅ (自己的) | ✅ |
| 刪除活動 | ❌ | ✅ (自己的) | ✅ |
| 查看分析數據 | ❌ | ✅ | ✅ |
| 管理 Feature Flags | ❌ | ❌ | ✅ |

### API 端點權限

```
公開端點 (無需認證)
├── POST   /api/users/register      註冊
└── POST   /api/users/login         登入

需認證端點 (ABAC: 僅限本人)
├── GET    /api/users/profile       查看個人資料
├── PUT    /api/users/profile       更新個人資料
└── POST   /api/users/change-password  修改密碼

管理員端點 (RBAC: Admin only)
├── GET    /api/users/all           查看所有使用者
└── POST   /api/feature-flags       管理功能開關

主辦方端點 (RBAC: Organizer + Admin)
├── POST   /api/events              建立活動
├── PUT    /api/events/:id          編輯活動
├── DELETE /api/events/:id          刪除活動
└── GET    /api/analytics/*         查看分析
```

---

## 測試前準備

### 1. 確保後端服務運行

```powershell
cd c:\_AG11\TixMaster\backend
npm start
```

服務應該在 `http://localhost:3000` 運行。

### 2. 確認資料庫連線

```powershell
# 測試資料庫連線
psql -U postgres -d tixmaster -c "SELECT COUNT(*) FROM users;"
```

### 3. 準備測試工具

系統提供三個測試腳本：

| 腳本 | 用途 | 是否需要修改資料庫 |
|------|------|:------------------:|
| `quick-rbac-test.ps1` | 快速測試基本功能 | ❌ |
| `rbac-test.ps1` | 原始測試腳本 | ⚠️ 部分需要 |
| `rbac-abac-full-test.ps1` | 完整測試所有角色 | ✅ |

---

## 快速測試

### 使用快速測試腳本

```powershell
# 進入 backend 目錄
cd c:\_AG11\TixMaster\backend

# 執行快速測試
.\quick-rbac-test.ps1
```

### 預期輸出

```
═══════════════════════════════════════════════
  RBAC/ABAC 快速測試
═══════════════════════════════════════════════

【1】註冊兩個測試使用者
  註冊 User 1 ✓ (201)
  註冊 User 2 ✓ (201)

【2】登入取得 Token
  User 1 Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
  User 2 Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...

【3】ABAC 測試：使用者只能存取自己的資料
  User 1 查看自己的 Profile (✓ 應成功) ✓ (200)
  User 1 更新自己的 Profile (✓ 應成功) ✓ (200)
  User 1 修改自己的密碼 (✓ 應成功) ✓ (200)

【4】RBAC 測試：一般使用者無管理員權限
  User 1 嘗試查看所有使用者 (✗ 應失敗 403) ✓ (403)
  User 2 嘗試查看所有使用者 (✗ 應失敗 403) ✓ (403)

【5】測試其他權限控制
  未登入嘗試查看 Profile (✗ 應失敗 401) ✓ (401)
  錯誤 Token 嘗試查看 Profile (✗ 應失敗 401) ✓ (401)

═══════════════════════════════════════════════
  測試完成！
═══════════════════════════════════════════════

✅ 已測試的 RBAC 控制:
  • 一般使用者無法存取管理員功能 (403 Forbidden)
  • 未認證使用者無法存取受保護資源 (401 Unauthorized)

✅ 已測試的 ABAC 控制:
  • 使用者可以查看自己的 Profile
  • 使用者可以更新自己的 Profile
  • 使用者可以修改自己的密碼
```

---

## 完整測試流程

### 步驟 1: 執行完整測試腳本

```powershell
.\rbac-abac-full-test.ps1
```

### 步驟 2: 腳本會暫停，提示你提升權限

腳本會顯示需要執行的 SQL 指令，例如：

```
┌─ 5. 手動提升權限 ──────────────────────────────────┐

  ⚠️  需要手動執行 SQL 來測試不同角色權限:

  方法 1: 使用 psql 指令
  psql -U postgres -d tixmaster -c "UPDATE users SET role = 'admin' WHERE email = 'admin123@example.com';"
  psql -U postgres -d tixmaster -c "UPDATE users SET role = 'organizer' WHERE email = 'organizer456@example.com';"

  執行完畢後，按任意鍵繼續測試...
```

### 步驟 3: 在另一個終端執行 SQL

```powershell
# 開啟新的 PowerShell 視窗
# 複製腳本提供的指令並執行

psql -U postgres -d tixmaster -c "UPDATE users SET role = 'admin' WHERE email = 'admin123@example.com';"
psql -U postgres -d tixmaster -c "UPDATE users SET role = 'organizer' WHERE email = 'organizer456@example.com';"
```

或使用 pgAdmin：

```sql
-- 在 pgAdmin 的 Query Tool 中執行
UPDATE users SET role = 'admin' WHERE email = 'admin123@example.com';
UPDATE users SET role = 'organizer' WHERE email = 'organizer456@example.com';

-- 驗證
SELECT email, role FROM users WHERE role != 'user';
```

### 步驟 4: 繼續測試

回到測試腳本的視窗，按任意鍵繼續。腳本會測試：

- ✅ Admin 查看所有使用者
- ✅ Admin 查看分析數據
- ✅ Admin 管理 Feature Flags
- ✅ Organizer 建立活動
- ✅ Organizer 查看分析
- ❌ Organizer 無法查看所有使用者（應返回 403）

---

## 手動測試範例

如果你想手動測試 API，可以使用以下範例：

### 1. 註冊新使用者

```powershell
$body = @{
    email = "testuser@example.com"
    password = "SecurePass123!"
    name = "Test User"
    phone = "0911000001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/users/register" -Method POST -Body $body -ContentType "application/json"
```

**預期回應：**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "name": "Test User",
    "phone": "0911000001",
    "role": "user",
    "created_at": "2025-11-25T10:30:00.000Z"
  }
}
```

### 2. 登入取得 Token

```powershell
$loginBody = @{
    email = "testuser@example.com"
    password = "SecurePass123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body $loginBody -ContentType "application/json"
$token = $response.token

Write-Host "Token: $token"
```

**預期回應：**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "name": "Test User",
    "phone": "0911000001",
    "role": "user"
  }
}
```

### 3. 查看個人資料 (需要 Token)

```powershell
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method GET -Headers $headers
```

**預期回應：**
```json
{
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "name": "Test User",
    "phone": "0911000001",
    "role": "user",
    "attributes": {},
    "created_at": "2025-11-25T10:30:00.000Z"
  }
}
```

### 4. 更新個人資料 (ABAC 測試)

```powershell
$updateBody = @{
    name = "Updated Name"
    phone = "0922000002"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method PUT -Headers $headers -Body $updateBody -ContentType "application/json"
```

**預期回應：**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "name": "Updated Name",
    "phone": "0922000002",
    "role": "user"
  }
}
```

### 5. 嘗試存取管理員功能 (RBAC 測試 - 應失敗)

```powershell
try {
    Invoke-RestMethod -Uri "http://localhost:3000/api/users/all" -Method GET -Headers $headers
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $error = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "Status: $statusCode"
    Write-Host "Error: $($error.error)"
    Write-Host "Message: $($error.message)"
}
```

**預期回應：**
```
Status: 403
Error: Forbidden
Message: Requires admin role
```

### 6. 修改密碼

```powershell
$pwdBody = @{
    currentPassword = "SecurePass123!"
    newPassword = "NewSecurePass456!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/users/change-password" -Method POST -Headers $headers -Body $pwdBody -ContentType "application/json"
```

**預期回應：**
```json
{
  "message": "Password changed successfully"
}
```

### 7. 測試 Admin 權限

首先提升權限：

```sql
UPDATE users SET role = 'admin' WHERE email = 'testuser@example.com';
```

重新登入取得新 token（包含 admin 角色）：

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body $loginBody -ContentType "application/json"
$adminToken = $response.token

$adminHeaders = @{
    "Authorization" = "Bearer $adminToken"
}

# 現在可以存取管理員功能
Invoke-RestMethod -Uri "http://localhost:3000/api/users/all" -Method GET -Headers $adminHeaders
```

**預期回應：**
```json
{
  "users": [
    {
      "id": 1,
      "email": "testuser@example.com",
      "name": "Updated Name",
      "phone": "0922000002",
      "role": "admin",
      "created_at": "2025-11-25T10:30:00.000Z"
    },
    // ... 其他使用者
  ]
}
```

---

## 常見問題

### Q1: 為什麼我得到 403 Forbidden？

**A:** 這可能是以下原因：

1. **正常情況**：你的角色沒有權限存取該資源
   - 例如：一般使用者（`user`）嘗試存取 `/api/users/all`
   - **解決方案**：這是預期行為，表示 RBAC 正常運作

2. **需要更高權限**：你需要提升角色
   - **解決方案**：在資料庫中更新角色
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
   ```

### Q2: 401 Unauthorized 和 403 Forbidden 有什麼差別？

| 錯誤碼 | 意義 | 原因 | 解決方法 |
|--------|------|------|----------|
| **401** | 未認證 | • 沒有提供 token<br>• token 無效或過期 | 重新登入取得新 token |
| **403** | 已認證但無權限 | • 角色權限不足<br>• 不是資源擁有者 | 提升角色或確認存取權限 |

### Q3: 如何查看我目前的角色？

**方法 1：查看登入回應**

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body $loginBody -ContentType "application/json"
Write-Host "Your role: $($response.user.role)"
```

**方法 2：查詢資料庫**

```sql
SELECT email, role FROM users WHERE email = 'your@email.com';
```

**方法 3：解析 JWT Token**

```powershell
# Token 的 payload 部分包含角色資訊
# 格式：header.payload.signature
$tokenParts = $token.Split('.')
$payload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($tokenParts[1] + "=="))
$payload | ConvertFrom-Json | Select-Object userId, email, role
```

### Q4: 如何重置角色為一般使用者？

```sql
UPDATE users SET role = 'user' WHERE email = 'your@email.com';
```

### Q5: Token 過期了怎麼辦？

Token 預設有效期為 7 天。如果過期：

```powershell
# 重新登入取得新 token
$loginBody = @{
    email = "your@email.com"
    password = "your-password"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body $loginBody -ContentType "application/json"
$newToken = $response.token
```

### Q6: 如何測試 ABAC（使用者只能存取自己的資料）？

```powershell
# 1. 註冊兩個使用者
# User 1
$user1 = Invoke-RestMethod -Uri "http://localhost:3000/api/users/register" -Method POST -Body (@{
    email = "user1@test.com"
    password = "pass1"
    name = "User One"
} | ConvertTo-Json) -ContentType "application/json"

# User 2
$user2 = Invoke-RestMethod -Uri "http://localhost:3000/api/users/register" -Method POST -Body (@{
    email = "user2@test.com"
    password = "pass2"
    name = "User Two"
} | ConvertTo-Json) -ContentType "application/json"

# 2. 分別登入取得 token
$token1 = (Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body (@{email="user1@test.com";password="pass1"} | ConvertTo-Json) -ContentType "application/json").token

$token2 = (Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body (@{email="user2@test.com";password="pass2"} | ConvertTo-Json) -ContentType "application/json").token

# 3. User 1 查看自己的 Profile（✓ 應成功）
Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method GET -Headers @{"Authorization"="Bearer $token1"}

# 4. User 1 更新自己的 Profile（✓ 應成功）
Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method PUT -Headers @{"Authorization"="Bearer $token1"} -Body (@{name="User One Updated";phone="0911111111"} | ConvertTo-Json) -ContentType "application/json"

# ✅ ABAC 確保使用者只能操作自己的資料
```

### Q7: 如何清理測試資料？

```sql
-- 刪除所有測試使用者（小心使用！）
DELETE FROM users WHERE email LIKE '%@test.com' OR email LIKE '%@example.com';

-- 或只刪除特定使用者
DELETE FROM users WHERE email = 'testuser@example.com';
```

---

## 錯誤碼說明

### HTTP 狀態碼

| 狀態碼 | 說明 | 常見原因 |
|--------|------|----------|
| **200** | 成功 | 請求成功處理 |
| **201** | 已建立 | 資源成功建立（如註冊） |
| **400** | 錯誤請求 | 缺少必要欄位或格式錯誤 |
| **401** | 未認證 | 未登入或 token 無效 |
| **403** | 禁止存取 | 已登入但權限不足 |
| **404** | 找不到 | 資源不存在 |
| **500** | 伺服器錯誤 | 後端內部錯誤 |

### 常見錯誤訊息

```json
// 401 - 未提供 token
{
  "error": "Unauthorized"
}

// 403 - 角色權限不足
{
  "error": "Forbidden",
  "message": "Requires admin role"
}

// 403 - 缺少特定權限
{
  "error": "Forbidden",
  "message": "Missing permission: view_users"
}

// 400 - 缺少必要欄位
{
  "error": "Email, password and name are required"
}

// 401 - 密碼錯誤
{
  "error": "Invalid credentials"
}
```

---

## 測試檢查清單

### RBAC 測試

- [ ] User 角色無法存取 `/api/users/all` (403)
- [ ] User 角色無法存取 `/api/analytics/*` (403)
- [ ] User 角色無法存取 `/api/feature-flags` (403)
- [ ] Admin 角色可以存取所有端點 (200)
- [ ] Organizer 可以建立活動 (201)
- [ ] Organizer 可以查看分析 (200)
- [ ] Organizer 無法存取 `/api/users/all` (403)

### ABAC 測試

- [ ] 使用者可以查看自己的 Profile (200)
- [ ] 使用者可以更新自己的 Profile (200)
- [ ] 使用者可以修改自己的密碼 (200)
- [ ] 使用者無法查看其他人的資料 (403 或設計決策)

### 認證測試

- [ ] 未登入無法存取受保護資源 (401)
- [ ] 錯誤 token 無法存取受保護資源 (401)
- [ ] 過期 token 無法使用 (401)
- [ ] 正確 token 可以存取授權資源 (200)

---

## 進階測試

### 測試 Token 過期

```powershell
# 修改 JWT_SECRET 環境變數（會使現有 token 失效）
$env:JWT_SECRET = "new-secret-key"

# 嘗試使用舊 token（應該失敗）
Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method GET -Headers @{"Authorization"="Bearer $oldToken"}
# 預期：401 Unauthorized
```

### 測試同時登入多個使用者

```powershell
# 建立測試腳本
$users = @(
    @{email="user1@test.com"; password="pass1"; role="user"},
    @{email="user2@test.com"; password="pass2"; role="organizer"},
    @{email="user3@test.com"; password="pass3"; role="admin"}
)

foreach ($user in $users) {
    # 註冊
    Invoke-RestMethod -Uri "http://localhost:3000/api/users/register" -Method POST -Body (@{
        email=$user.email
        password=$user.password
        name="Test User"
    } | ConvertTo-Json) -ContentType "application/json"

    # 提升權限（除了 user）
    if ($user.role -ne "user") {
        psql -U postgres -d tixmaster -c "UPDATE users SET role = '$($user.role)' WHERE email = '$($user.email)';"
    }

    # 登入
    $token = (Invoke-RestMethod -Uri "http://localhost:3000/api/users/login" -Method POST -Body (@{
        email=$user.email
        password=$user.password
    } | ConvertTo-Json) -ContentType "application/json").token

    Write-Host "$($user.role): $token"
}
```

### 併發測試

```powershell
# 同時發送多個請求測試系統穩定性
$jobs = @()
1..10 | ForEach-Object {
    $jobs += Start-Job -ScriptBlock {
        Invoke-RestMethod -Uri "http://localhost:3000/api/users/profile" -Method GET -Headers @{"Authorization"="Bearer $using:token"}
    }
}

# 等待所有任務完成
$jobs | Wait-Job | Receive-Job
```

---

## 相關文件

- [config/roles.js](config/roles.js) - 角色和權限定義
- [middleware/rbac.js](middleware/rbac.js) - RBAC 中介軟體
- [middleware/abac.js](middleware/abac.js) - ABAC 中介軟體
- [middleware/auth.js](middleware/auth.js) - JWT 認證中介軟體
- [routes/users.js](routes/users.js) - 使用者路由

---

## 聯絡資訊

如有問題或建議，請聯絡開發團隊。

**最後更新：** 2025-11-25
