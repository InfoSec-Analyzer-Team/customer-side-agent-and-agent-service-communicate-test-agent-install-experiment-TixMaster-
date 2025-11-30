@echo off
REM TixMaster 快速診斷腳本 (Windows 版本)
REM 使用方式: quick_check.bat

echo ========================================
echo   TixMaster 系統健康檢查
echo ========================================
echo.
echo 檢查時間: %date% %time%
echo.

REM ============================================
REM 1. 服務狀態檢查
REM ============================================
echo [1/8] 檢查 Backend 服務狀態...
curl -s http://localhost:3000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Backend 服務: 運行中
) else (
    echo    [ERR] Backend 服務: 無法連接
)
echo.

REM ============================================
REM 2. 錯誤率檢查
REM ============================================
echo [2/8] 檢查 5xx 錯誤率...
curl -s "http://localhost:9091/api/v1/query?query=100*sum(rate(http_errors_total{status_code=~\"5..\"}[5m]))/sum(rate(http_requests_total[5m]))" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Prometheus 連接成功
) else (
    echo    [WARN] Prometheus 無法連接
)
echo.

REM ============================================
REM 3. 記憶體使用檢查
REM ============================================
echo [3/8] 檢查記憶體使用...
curl -s http://localhost:3000/metrics | findstr process_resident_memory_bytes >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Metrics 端點可用
) else (
    echo    [WARN] Metrics 端點無法連接
)
echo.

REM ============================================
REM 4. 資料庫連線檢查
REM ============================================
echo [4/8] 檢查資料庫狀態...
docker exec -it tixmaster-postgres psql -U postgres -c "SELECT 1;" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] 資料庫: 已連接
) else (
    echo    [ERR] 資料庫: 無法連接
)
echo.

REM ============================================
REM 5. Docker 容器狀態
REM ============================================
echo [5/8] 檢查 Docker 容器...
docker ps --filter "name=tixmaster" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Docker 容器運行中
    docker ps --filter "name=tixmaster" --format "   {{.Names}}: {{.Status}}"
) else (
    echo    [WARN] Docker 未運行或無容器
)
echo.

REM ============================================
REM 6. Prometheus 狀態
REM ============================================
echo [6/8] 檢查 Prometheus...
curl -s http://localhost:9091/-/healthy >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Prometheus: http://localhost:9091
) else (
    echo    [ERR] Prometheus: 無法連接
)
echo.

REM ============================================
REM 7. Grafana 狀態
REM ============================================
echo [7/8] 檢查 Grafana...
curl -s http://localhost:3001/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] Grafana: http://localhost:3001
) else (
    echo    [ERR] Grafana: 無法連接
)
echo.

REM ============================================
REM 8. 快速測試
REM ============================================
echo [8/8] 執行快速 API 測試...
echo    測試 /health 端點...
curl -s http://localhost:3000/health
echo.
echo.

REM ============================================
REM 總結
REM ============================================
echo ========================================
echo   檢查完成
echo ========================================
echo.
echo 提示:
echo    [OK]   = 正常
echo    [WARN] = 警告
echo    [ERR]  = 異常
echo.
echo 詳細故障排除請參考: markdown_file\RUNBOOK.md
echo.
pause
