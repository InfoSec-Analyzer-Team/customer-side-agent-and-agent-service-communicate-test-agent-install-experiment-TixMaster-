# TixMaster API 手動測試指南

## Windows PowerShell 測試方法

### 基本語法

```powershell
# 方法 1: 使用 Invoke-WebRequest (完整資訊)
Invoke-WebRequest -Uri "http://localhost:3000/health" -Method GET

# 方法 2: 使用 curl (簡潔)
curl http://localhost:3000/health

# 方法 3: 只看回應內容
(Invoke-WebRequest -Uri "http://localhost:3000/health").Content
```

---

## 📋 測試端點範例

### ✅ 1. Health Check（健康檢查）

```powershell
curl http://localhost:3000/health
```

**預期回應：**
```json
{"status":"OK","message":"TixMaster API is running"}
```

---

### ✅ 2. 取得功能開關

```powershell
curl http://localhost:3000/api/feature-flags
```

**預期回應：**
```json
{
  "flags": {
    "ENABLE_CHECKOUT_TIMER": {"enabled": false, ...},
    "ENABLE_VIEWING_COUNT": {"enabled": false, ...}
  }
}
```

---

### ✅ 3. 取得活動列表

```powershell
curl http://localhost:3000/api/events
```

**預期回應：**
```json
{"events":[]}
```
（目前資料庫沒有活動資料）

---

### ❌ 4. 測試 404 錯誤（錯誤的端點）

```powershell
curl http://localhost:3000/api/wrong-endpoint
```

**預期回應：**
```json
{"error":"Endpoint not found"}
```

這就是你看到的 404 錯誤！這是正常的，代表端點不存在。

---

## 📤 POST 請求測試

### 註冊新使用者

```powershell
$body = @{
    email = "test@example.com"
    password = "password123"
    name = "測試使用者"
    phone = "0912345678"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:3000/api/users/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**預期回應（成功）：**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "name": "測試使用者",
    "phone": "0912345678"
  }
}
```

---

### 使用者登入

```powershell
$loginBody = @{
    email = "test@example.com"
    password = "password123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:3000/api/users/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody

# 查看回應
$response.Content

# 解析 JSON 並取得 token
$data = $response.Content | ConvertFrom-Json
$token = $data.token
Write-Host "Token: $token"
```

**預期回應：**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "name": "測試使用者"
  }
}
```

---

## 🔐 測試需要認證的端點

### 取得個人資料（需要 JWT token）

```powershell
# 先登入取得 token（如上）
$token = "your-jwt-token-here"

# 使用 token 呼叫 API
Invoke-WebRequest -Uri "http://localhost:3000/api/users/profile" `
    -Method GET `
    -Headers @{Authorization = "Bearer $token"}
```

---

## 🔄 PUT 請求測試

### 更新功能開關

```powershell
$flagBody = @{
    enabled = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:3000/api/feature-flags/ENABLE_CHECKOUT_TIMER" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $flagBody

# 驗證是否更新成功
curl http://localhost:3000/api/feature-flags/ENABLE_CHECKOUT_TIMER
```

---

## 🛠️ 完整測試流程範例

```powershell
# 1. 測試伺服器是否運行
Write-Host "=== 測試 Health Check ===" -ForegroundColor Cyan
curl http://localhost:3000/health

# 2. 註冊新使用者
Write-Host "`n=== 註冊新使用者 ===" -ForegroundColor Cyan
$registerBody = @{
    email = "demo@tixmaster.com"
    password = "demo123456"
    name = "Demo User"
    phone = "0987654321"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/users/register" `
        -Method POST `
        -ContentType "application/json" `
        -Body $registerBody
    
    Write-Host "註冊成功！" -ForegroundColor Green
    $registerResponse.Content
} catch {
    Write-Host "註冊失敗（可能已存在）" -ForegroundColor Yellow
}

# 3. 登入
Write-Host "`n=== 登入 ===" -ForegroundColor Cyan
$loginBody = @{
    email = "demo@tixmaster.com"
    password = "demo123456"
} | ConvertTo-Json

$loginResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/users/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody

$loginData = $loginResponse.Content | ConvertFrom-Json
$token = $loginData.token

Write-Host "登入成功！Token: $($token.Substring(0,20))..." -ForegroundColor Green

# 4. 取得個人資料
Write-Host "`n=== 取得個人資料 ===" -ForegroundColor Cyan
$profileResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/users/profile" `
    -Method GET `
    -Headers @{Authorization = "Bearer $token"}

$profileResponse.Content

# 5. 查看功能開關
Write-Host "`n=== 功能開關 ===" -ForegroundColor Cyan
curl http://localhost:3000/api/feature-flags

Write-Host "`n✅ 測試完成！" -ForegroundColor Green
```

---

## 🧪 使用 Postman 測試（推薦）

如果你想要更視覺化的測試工具，建議安裝 **Postman**：

1. 下載：https://www.postman.com/downloads/
2. 建立新的 Collection: "TixMaster API"
3. 新增請求並測試

**優點：**
- 視覺化介面
- 自動儲存 token
- 可以匯出測試集合

---

## ⚠️ 常見錯誤

### 1. `{"error":"Endpoint not found"}`
- **原因：** 端點路徑錯誤或不存在
- **解決：** 檢查 URL 是否正確（參考 README.md）

### 2. `{"error":"Access token required"}`
- **原因：** 端點需要認證但沒有提供 token
- **解決：** 先登入取得 token，然後在 Header 加入 `Authorization: Bearer <token>`

### 3. `無法連線到伺服器`
- **原因：** 伺服器未啟動
- **解決：** 執行 `npm start`

### 4. `{"error":"Invalid credentials"}`
- **原因：** Email 或密碼錯誤
- **解決：** 檢查登入資訊是否正確

---

## 📊 狀態碼說明

| 狀態碼 | 意義 | 範例 |
|--------|------|------|
| 200 | 成功 | GET 請求成功 |
| 201 | 已建立 | 註冊/建立訂單成功 |
| 400 | 請求錯誤 | 缺少必填欄位 |
| 401 | 未認證 | 需要登入 |
| 403 | 禁止存取 | Token 無效 |
| 404 | 找不到 | 端點或資源不存在 |
| 409 | 衝突 | Email 已存在 |
| 500 | 伺服器錯誤 | 資料庫錯誤等 |

---

## 🎯 快速測試腳本

儲存為 `test-api.ps1`：

```powershell
# 測試所有公開端點
$baseUrl = "http://localhost:3000"

Write-Host "開始測試 TixMaster API..." -ForegroundColor Cyan

# Health Check
Write-Host "`n[1/3] Health Check..." -ForegroundColor Yellow
(Invoke-WebRequest "$baseUrl/health").Content

# Feature Flags
Write-Host "`n[2/3] Feature Flags..." -ForegroundColor Yellow
(Invoke-WebRequest "$baseUrl/api/feature-flags").Content

# Events
Write-Host "`n[3/3] Events..." -ForegroundColor Yellow
(Invoke-WebRequest "$baseUrl/api/events").Content

Write-Host "`n✅ 所有測試完成！" -ForegroundColor Green
```

執行：
```powershell
.\test-api.ps1
```
