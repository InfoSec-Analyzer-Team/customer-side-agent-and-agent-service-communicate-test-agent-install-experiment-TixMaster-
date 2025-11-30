@echo off
REM ====================================================
REM TixMaster Monitoring System Startup Script (Windows)
REM ====================================================

echo.
echo ========================================
echo   TixMaster Monitoring System Startup
echo ========================================
echo.

REM Check if Docker is running
echo [1/3] Checking Docker status...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running! Please start Docker Desktop first
    echo.
    pause
    exit /b 1
)
echo ✅ Docker is running

echo.
echo [2/3] Starting Prometheus and Grafana...
docker-compose -f docker-compose.monitoring.yml up -d
if %errorlevel% neq 0 (
    echo ❌ Monitoring system failed to start
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for services to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   ✅ Monitoring System Started!
echo ========================================
echo.
echo 📊 Prometheus: http://localhost:9091
echo 📈 Grafana:    http://localhost:3001
echo    Credentials: admin / admin
echo.
echo 💡 Tip: Make sure Backend is running at http://localhost:3000
echo.
echo Press any key to continue...
pause >nul