# RBAC/ABAC 完整測試腳本
# 測試所有角色權限和屬性控制

$baseUrl = "http://localhost:3000"
$ErrorActionPreference = "Continue"

# 測試輔助函數
function Test-Endpoint {
    param($name, $url, $method, $token, $body, $expectedStatus)

    Write-Host "`n  Testing: $name" -NoNewline

    $headers = @{}
    if ($token) { $headers["Authorization"] = "Bearer $token" }

    try {
        $params = @{
            Uri         = $url
            Method      = $method
            Headers     = $headers
            ContentType = "application/json"
        }
        if ($body) { $params.Body = ($body | ConvertTo-Json -Depth 10) }

        $response = Invoke-WebRequest @params -ErrorAction Stop
        $status = $response.StatusCode
        $content = $response.Content | ConvertFrom-Json
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($_.ErrorDetails.Message) {
            $content = $_.ErrorDetails.Message | ConvertFrom-Json
        }
    }

    if ($status -eq $expectedStatus) {
        Write-Host " ✓ PASS" -ForegroundColor Green -NoNewline
        Write-Host " (Status: $status)" -ForegroundColor Gray
        if ($content) {
            Write-Host "    Response: $($content | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host " ✗ FAIL" -ForegroundColor Red -NoNewline
        Write-Host " (Expected: $expectedStatus, Got: $status)" -ForegroundColor Yellow
        if ($content) {
            Write-Host "    Response: $($content | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
        }
    }
    return @{ Status = $status; Content = $content }
}

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     RBAC/ABAC 完整測試 - TixMaster                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ============================================================
# 1️⃣  註冊測試使用者
# ============================================================
Write-Host "`n┌─ 1. 註冊測試使用者 ─────────────────────────────────┐" -ForegroundColor Yellow

$rand = Get-Random
$user1Email = "user$rand@example.com"
$user2Email = "user$($rand+1)@example.com"
$adminEmail = "admin$rand@example.com"
$organizerEmail = "organizer$rand@example.com"
$password = "SecurePass123!"

Write-Host "  註冊 User 1..." -NoNewline
$regBody1 = @{ email = $user1Email; password = $password; name = "Test User 1"; phone = "0911000001" }
$reg1 = Test-Endpoint "Register User 1" "$baseUrl/api/users/register" "POST" $null $regBody1 201

Write-Host "  註冊 User 2..." -NoNewline
$regBody2 = @{ email = $user2Email; password = $password; name = "Test User 2"; phone = "0911000002" }
$reg2 = Test-Endpoint "Register User 2" "$baseUrl/api/users/register" "POST" $null $regBody2 201

Write-Host "  註冊 Admin..." -NoNewline
$regBodyAdmin = @{ email = $adminEmail; password = $password; name = "Admin User"; phone = "0911000003" }
$regAdmin = Test-Endpoint "Register Admin" "$baseUrl/api/users/register" "POST" $null $regBodyAdmin 201

Write-Host "  註冊 Organizer..." -NoNewline
$regBodyOrg = @{ email = $organizerEmail; password = $password; name = "Organizer User"; phone = "0911000004" }
$regOrg = Test-Endpoint "Register Organizer" "$baseUrl/api/users/register" "POST" $null $regBodyOrg 201

# ============================================================
# 2️⃣  登入取得 Token
# ============================================================
Write-Host "`n┌─ 2. 登入取得 Token ─────────────────────────────────┐" -ForegroundColor Yellow

$loginBody1 = @{ email = $user1Email; password = $password }
$loginRes1 = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST -Body ($loginBody1 | ConvertTo-Json) -ContentType "application/json"
$token1 = ($loginRes1.Content | ConvertFrom-Json).token
$user1Id = ($loginRes1.Content | ConvertFrom-Json).user.id
Write-Host "  User 1 Token: $($token1.Substring(0,20))..." -ForegroundColor Green

$loginBody2 = @{ email = $user2Email; password = $password }
$loginRes2 = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST -Body ($loginBody2 | ConvertTo-Json) -ContentType "application/json"
$token2 = ($loginRes2.Content | ConvertFrom-Json).token
$user2Id = ($loginRes2.Content | ConvertFrom-Json).user.id
Write-Host "  User 2 Token: $($token2.Substring(0,20))..." -ForegroundColor Green

# ============================================================
# 3️⃣  ABAC 測試：使用者只能存取自己的資料
# ============================================================
Write-Host "`n┌─ 3. ABAC 測試：使用者資料存取控制 ──────────────────┐" -ForegroundColor Yellow

Write-Host "`n  3.1 使用者存取自己的 Profile (應該成功):"
Test-Endpoint "User 1 - Get Own Profile" "$baseUrl/api/users/profile" "GET" $token1 $null 200

Write-Host "`n  3.2 使用者更新自己的 Profile (應該成功):"
$updateBody = @{ name = "User 1 Updated"; phone = "0922000001" }
Test-Endpoint "User 1 - Update Own Profile" "$baseUrl/api/users/profile" "PUT" $token1 $updateBody 200

Write-Host "`n  3.3 使用者修改自己的密碼 (應該成功):"
$pwdBody = @{ currentPassword = $password; newPassword = "NewPass456!" }
Test-Endpoint "User 1 - Change Password" "$baseUrl/api/users/change-password" "POST" $token1 $pwdBody 200

# ============================================================
# 4️⃣  RBAC 測試：一般使用者無法存取管理員功能
# ============================================================
Write-Host "`n┌─ 4. RBAC 測試：一般使用者權限限制 ──────────────────┐" -ForegroundColor Yellow

Write-Host "`n  4.1 一般使用者嘗試查看所有使用者 (應該失敗 403):"
Test-Endpoint "User 1 - Get All Users" "$baseUrl/api/users/all" "GET" $token1 $null 403

# ============================================================
# 5️⃣  手動提升權限測試說明
# ============================================================
Write-Host "`n┌─ 5. 手動提升權限 ──────────────────────────────────┐" -ForegroundColor Yellow
Write-Host "`n  ⚠️  需要手動執行 SQL 來測試不同角色權限:" -ForegroundColor Yellow
Write-Host "`n  方法 1: 使用 psql 指令" -ForegroundColor Cyan
Write-Host "  psql -U postgres -d tixmaster -c `"UPDATE users SET role = 'admin' WHERE email = '$adminEmail';`"" -ForegroundColor White
Write-Host "  psql -U postgres -d tixmaster -c `"UPDATE users SET role = 'organizer' WHERE email = '$organizerEmail';`"" -ForegroundColor White

Write-Host "`n  方法 2: 使用 pgAdmin 或其他 PostgreSQL 工具" -ForegroundColor Cyan
Write-Host "  執行以下 SQL:" -ForegroundColor White
Write-Host "  UPDATE users SET role = 'admin' WHERE email = '$adminEmail';" -ForegroundColor White
Write-Host "  UPDATE users SET role = 'organizer' WHERE email = '$organizerEmail';" -ForegroundColor White

Write-Host "`n  執行完畢後，按任意鍵繼續測試..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# ============================================================
# 6️⃣  Admin 權限測試
# ============================================================
Write-Host "`n┌─ 6. Admin 權限測試 ────────────────────────────────┐" -ForegroundColor Yellow

# 重新登入 Admin
$loginBodyAdmin = @{ email = $adminEmail; password = $password }
try {
    $loginResAdmin = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST -Body ($loginBodyAdmin | ConvertTo-Json) -ContentType "application/json"
    $tokenAdmin = ($loginResAdmin.Content | ConvertFrom-Json).token
    $adminRole = ($loginResAdmin.Content | ConvertFrom-Json).user.role
    Write-Host "  Admin Token 取得成功, Role: $adminRole" -ForegroundColor Green

    Write-Host "`n  6.1 Admin 查看所有使用者 (應該成功):"
    Test-Endpoint "Admin - Get All Users" "$baseUrl/api/users/all" "GET" $tokenAdmin $null 200

    Write-Host "`n  6.2 Admin 查看分析數據 (應該成功):"
    Test-Endpoint "Admin - Get Analytics" "$baseUrl/api/analytics/overview" "GET" $tokenAdmin $null 200

    Write-Host "`n  6.3 Admin 管理 Feature Flags (應該成功):"
    Test-Endpoint "Admin - Get Feature Flags" "$baseUrl/api/feature-flags" "GET" $tokenAdmin $null 200
}
catch {
    Write-Host "  ⚠️  Admin 登入失敗 - 可能尚未提升權限" -ForegroundColor Red
}

# ============================================================
# 7️⃣  Organizer 權限測試
# ============================================================
Write-Host "`n┌─ 7. Organizer 權限測試 ────────────────────────────┐" -ForegroundColor Yellow

# 重新登入 Organizer
$loginBodyOrg = @{ email = $organizerEmail; password = $password }
try {
    $loginResOrg = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST -Body ($loginBodyOrg | ConvertTo-Json) -ContentType "application/json"
    $tokenOrg = ($loginResOrg.Content | ConvertFrom-Json).token
    $orgRole = ($loginResOrg.Content | ConvertFrom-Json).user.role
    Write-Host "  Organizer Token 取得成功, Role: $orgRole" -ForegroundColor Green

    Write-Host "`n  7.1 Organizer 建立活動 (應該成功):"
    $eventBody = @{
        name = "Test Event"
        description = "Test Description"
        venue = "Test Venue"
        date = "2025-12-31T20:00:00Z"
        total_tickets = 100
        available_tickets = 100
        price = 1000
    }
    Test-Endpoint "Organizer - Create Event" "$baseUrl/api/events" "POST" $tokenOrg $eventBody 201

    Write-Host "`n  7.2 Organizer 查看分析數據 (應該成功):"
    Test-Endpoint "Organizer - Get Analytics" "$baseUrl/api/analytics/overview" "GET" $tokenOrg $null 200

    Write-Host "`n  7.3 Organizer 嘗試查看所有使用者 (應該失敗 403):"
    Test-Endpoint "Organizer - Get All Users" "$baseUrl/api/users/all" "GET" $tokenOrg $null 403
}
catch {
    Write-Host "  ⚠️  Organizer 登入失敗 - 可能尚未提升權限" -ForegroundColor Red
}

# ============================================================
# 8️⃣  測試總結
# ============================================================
Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     測試完成                                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n✅ RBAC (Role-Based) 測試項目:" -ForegroundColor Green
Write-Host "  - User 角色無法存取 Admin 功能 (GET /api/users/all)" -ForegroundColor White
Write-Host "  - Admin 角色可以存取所有功能" -ForegroundColor White
Write-Host "  - Organizer 角色可以建立活動和查看分析" -ForegroundColor White
Write-Host "  - Organizer 角色無法存取使用者管理功能" -ForegroundColor White

Write-Host "`n✅ ABAC (Attribute-Based) 測試項目:" -ForegroundColor Green
Write-Host "  - 使用者可以查看自己的 Profile" -ForegroundColor White
Write-Host "  - 使用者可以更新自己的 Profile" -ForegroundColor White
Write-Host "  - 使用者可以修改自己的密碼" -ForegroundColor White

Write-Host "`n📧 測試帳號資訊:" -ForegroundColor Cyan
Write-Host "  User 1: $user1Email / $password" -ForegroundColor White
Write-Host "  User 2: $user2Email / $password" -ForegroundColor White
Write-Host "  Admin:  $adminEmail / $password" -ForegroundColor White
Write-Host "  Organizer: $organizerEmail / $password" -ForegroundColor White
