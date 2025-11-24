# TixMaster API 快速測試腳本
# 使用方法: .\quick-test.ps1

$baseUrl = "http://localhost:3000"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   TixMaster API 測試工具" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Health Check
Write-Host "[1/5] 測試伺服器健康狀態..." -ForegroundColor Yellow
try {
    $health = (Invoke-WebRequest "$baseUrl/health").Content | ConvertFrom-Json
    Write-Host "✅ 伺服器運行正常: $($health.message)" -ForegroundColor Green
} catch {
    Write-Host "❌ 伺服器無法連線" -ForegroundColor Red
    exit 1
}

# 2. Feature Flags
Write-Host "`n[2/5] 取得功能開關..." -ForegroundColor Yellow
try {
    $flags = (Invoke-WebRequest "$baseUrl/api/feature-flags").Content | ConvertFrom-Json
    Write-Host "✅ 功能開關數量: $($flags.flags.Count)" -ForegroundColor Green
    foreach ($key in $flags.flags.PSObject.Properties.Name) {
        $flag = $flags.flags.$key
        $status = if ($flag.enabled) { "[ON]" } else { "[OFF]" }
        Write-Host "   - $key : $status" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ 無法取得功能開關" -ForegroundColor Red
}

# 3. Events
Write-Host "`n[3/5] 取得活動列表..." -ForegroundColor Yellow
try {
    $events = (Invoke-WebRequest "$baseUrl/api/events").Content | ConvertFrom-Json
    Write-Host "✅ 活動數量: $($events.events.Count)" -ForegroundColor Green
    if ($events.events.Count -eq 0) {
        Write-Host "   ⚠️  目前沒有活動資料" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 無法取得活動列表" -ForegroundColor Red
}

# 4. 測試 404 錯誤
Write-Host "`n[4/5] 測試錯誤處理（預期會看到錯誤）..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$baseUrl/api/wrong-endpoint"
} catch {
    $errorMsg = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "✅ 404 處理正常: $($errorMsg.error)" -ForegroundColor Green
}

# 5. 測試認證端點（預期會失敗，因為沒有 token）
Write-Host "`n[5/5] 測試認證保護..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$baseUrl/api/users/profile"
} catch {
    $errorMsg = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "✅ 認證保護正常: $($errorMsg.error)" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   ✅ 所有測試完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "🎯 可用的端點：" -ForegroundColor Cyan
Write-Host "   - GET  /health" -ForegroundColor Gray
Write-Host "   - GET  /api/events" -ForegroundColor Gray
Write-Host "   - GET  /api/feature-flags" -ForegroundColor Gray
Write-Host "   - POST /api/users/register" -ForegroundColor Gray
Write-Host "   - POST /api/users/login" -ForegroundColor Gray
Write-Host "`n📖 查看完整文件: API_TESTING_GUIDE.md`n" -ForegroundColor Gray
