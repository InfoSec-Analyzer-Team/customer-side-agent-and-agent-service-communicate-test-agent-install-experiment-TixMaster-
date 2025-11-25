# PowerShell script to create admin account in PostgreSQL
# Usage: .\create_admin.ps1

$dbName = "tixmaster"
$dbUser = "postgres"
$sqlFile = "create_admin.sql"

Write-Host "=== Creating Admin Account ===" -ForegroundColor Cyan
Write-Host "Database: $dbName" -ForegroundColor Yellow
Write-Host "Email: admin@tixmaster.com" -ForegroundColor Yellow
Write-Host "Password: admin123" -ForegroundColor Yellow
Write-Host ""

# Execute SQL file
Write-Host "Executing SQL..." -ForegroundColor Green
psql -U $dbUser -d $dbName -f $sqlFile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Admin Account Created Successfully ===" -ForegroundColor Green
    Write-Host "You can now login at:" -ForegroundColor Cyan
    Write-Host "  URL: http://localhost:3000/admin-login.html" -ForegroundColor White
    Write-Host "  Email: admin@tixmaster.com" -ForegroundColor White
    Write-Host "  Password: admin123" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== Error Creating Admin Account ===" -ForegroundColor Red
    Write-Host "Please check the error message above" -ForegroundColor Yellow
}
