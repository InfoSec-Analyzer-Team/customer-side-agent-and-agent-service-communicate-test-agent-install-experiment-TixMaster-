# 讀取 .env 檔案並載入變數
$envPath = "$PSScriptRoot\alertmanager\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $parts = $line.Split("=", 2)
            if ($parts.Length -eq 2) {
                $name = $parts[0].Trim()
                $value = $parts[1].Trim()
                Set-Variable -Name $name -Value $value -Scope Script
            }
        }
    }
} else {
    Write-Host "找不到 .env 檔案，請確認 $envPath 存在。" -ForegroundColor Red
    exit 1
}

# 檢查必要變數
if (-not $Script:SMTP_EMAIL -or -not $Script:SMTP_PASSWORD) {
    Write-Host "錯誤: .env 檔案中缺少 SMTP_EMAIL 或 SMTP_PASSWORD 設定。" -ForegroundColor Red
    exit 1
}

# 讀取樣板
$templatePath = "$PSScriptRoot\alertmanager\config.template.yml"
$configPath = "$PSScriptRoot\alertmanager\config.yml"

if (-not (Test-Path $templatePath)) {
    Write-Host "找不到樣板檔案 $templatePath" -ForegroundColor Red
    exit 1
}

$content = Get-Content $templatePath -Raw

# 取代變數
$content = $content.Replace('${SMTP_EMAIL}', $Script:SMTP_EMAIL)
$content = $content.Replace('${SMTP_PASSWORD}', $Script:SMTP_PASSWORD)

# 寫入設定檔
$content | Set-Content $configPath -Encoding UTF8
Write-Host "Successfully generated from the sample $configPath" -ForegroundColor Green
Write-Host "Email: $Script:SMTP_EMAIL" -ForegroundColor Cyan
Write-Host "Password: $Script:SMTP_PASSWORD" -ForegroundColor Cyan