# 快速 RBAC/ABAC 測試 - 不需修改資料庫
$baseUrl = "http://localhost:3000"

function Test-API {
    param($name, $url, $method, $token, $body, $expectedStatus)

    Write-Host "`n  $name" -NoNewline

    $headers = @{}
    if ($token) { $headers["Authorization"] = "Bearer $token" }

    try {
        $params = @{
            Uri         = $url
            Method      = $method
            Headers     = $headers
            ContentType = "application/json"
        }
        if ($body) { $params.Body = ($body | ConvertTo-Json) }

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
        Write-Host " ✓" -ForegroundColor Green -NoNewline
        Write-Host " ($status)" -ForegroundColor Gray
    }
    else {
        Write-Host " ✗" -ForegroundColor Red -NoNewline
        Write-Host " (預期: $expectedStatus, 實際: $status)" -ForegroundColor Yellow
    }

    if ($content) {
        Write-Host "     $($content | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
    }

    return @{ Status = $status; Content = $content }
}

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RBAC/ABAC 快速測試" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# 1. 註冊新使用者
Write-Host "`n【1】註冊兩個測試使用者" -ForegroundColor Yellow
$rand = Get-Random
$email1 = "user$rand@test.com"
$email2 = "user$($rand+1)@test.com"
$pwd = "Pass123!"

$reg1 = Test-API "註冊 User 1" "$baseUrl/api/users/register" "POST" $null @{
    email = $email1
    password = $pwd
    name = "User One"
    phone = "0911111111"
} 201

$reg2 = Test-API "註冊 User 2" "$baseUrl/api/users/register" "POST" $null @{
    email = $email2
    password = $pwd
    name = "User Two"
    phone = "0922222222"
} 201

# 2. 登入
Write-Host "`n【2】登入取得 Token" -ForegroundColor Yellow
$login1 = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST `
    -Body (@{ email = $email1; password = $pwd } | ConvertTo-Json) `
    -ContentType "application/json"
$token1 = ($login1.Content | ConvertFrom-Json).token
Write-Host "  User 1 Token: $($token1.Substring(0,30))..." -ForegroundColor Green

$login2 = Invoke-WebRequest -Uri "$baseUrl/api/users/login" -Method POST `
    -Body (@{ email = $email2; password = $pwd } | ConvertTo-Json) `
    -ContentType "application/json"
$token2 = ($login2.Content | ConvertFrom-Json).token
Write-Host "  User 2 Token: $($token2.Substring(0,30))..." -ForegroundColor Green

# 3. ABAC 測試
Write-Host "`n【3】ABAC 測試：使用者只能存取自己的資料" -ForegroundColor Yellow

Test-API "User 1 查看自己的 Profile (✓ 應成功)" `
    "$baseUrl/api/users/profile" "GET" $token1 $null 200

Test-API "User 1 更新自己的 Profile (✓ 應成功)" `
    "$baseUrl/api/users/profile" "PUT" $token1 @{
        name = "User One Updated"
        phone = "0933333333"
    } 200

Test-API "User 1 修改自己的密碼 (✓ 應成功)" `
    "$baseUrl/api/users/change-password" "POST" $token1 @{
        currentPassword = $pwd
        newPassword = "NewPass456!"
    } 200

# 4. RBAC 測試
Write-Host "`n【4】RBAC 測試：一般使用者無管理員權限" -ForegroundColor Yellow

Test-API "User 1 嘗試查看所有使用者 (✗ 應失敗 403)" `
    "$baseUrl/api/users/all" "GET" $token1 $null 403

Test-API "User 2 嘗試查看所有使用者 (✗ 應失敗 403)" `
    "$baseUrl/api/users/all" "GET" $token2 $null 403

# 5. 測試其他受保護的端點
Write-Host "`n【5】測試其他權限控制" -ForegroundColor Yellow

Test-API "未登入嘗試查看 Profile (✗ 應失敗 401)" `
    "$baseUrl/api/users/profile" "GET" $null $null 401

Test-API "錯誤 Token 嘗試查看 Profile (✗ 應失敗 401)" `
    "$baseUrl/api/users/profile" "GET" "invalid-token" $null 401

# 總結
Write-Host "`n═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  測試完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n✅ 已測試的 RBAC 控制:" -ForegroundColor Green
Write-Host "  • 一般使用者無法存取管理員功能 (403 Forbidden)"
Write-Host "  • 未認證使用者無法存取受保護資源 (401 Unauthorized)"

Write-Host "`n✅ 已測試的 ABAC 控制:" -ForegroundColor Green
Write-Host "  • 使用者可以查看自己的 Profile"
Write-Host "  • 使用者可以更新自己的 Profile"
Write-Host "  • 使用者可以修改自己的密碼"

Write-Host "`n📧 測試帳號:" -ForegroundColor Cyan
Write-Host "  User 1: $email1 / NewPass456!"
Write-Host "  User 2: $email2 / $pwd"

Write-Host "`n💡 提示：" -ForegroundColor Yellow
Write-Host "  如要測試 Admin/Organizer 權限，需要在資料庫中手動提升角色："
Write-Host "  UPDATE users SET role = 'admin' WHERE email = '$email1';"
