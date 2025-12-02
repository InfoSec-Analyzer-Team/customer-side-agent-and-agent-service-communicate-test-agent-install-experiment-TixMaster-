# Requires: Windows PowerShell 5.1+
# Quick fault-injection smoke suite for local verification
# Usage examples:
#   pwsh -File backend/scripts/run_fault_suite.ps1
#   powershell -ExecutionPolicy Bypass -File backend/scripts/run_fault_suite.ps1

param(
  [int]$Port = 3999,
#   [string]$Host = '127.0.0.1',
  [int]$PauseMs = 300
)

$Base = "http://127.0.0.1:3999"

function Invoke-Check($name, $url) {
  Write-Host "[RUN] $name -> $url" -ForegroundColor Cyan
  try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    Write-Host ("[OK ] {0} {1}" -f $resp.StatusCode, $name) -ForegroundColor Green
  } catch {
    $status = $_.Exception.Response.StatusCode.value__
    if (-not $status) { $status = -1 }
    Write-Host ("[ERR] {0} {1}" -f $status, $name) -ForegroundColor Red
  }
  Start-Sleep -Milliseconds $PauseMs
}

Write-Host "Fault suite against $Base" -ForegroundColor Yellow

# Health
Invoke-Check 'health' "$Base/health"

# Latency
Invoke-Check 'latency' "$Base/api/fault/latency?delayMs=200"

# Delay jitter
Invoke-Check 'delay-jitter' "$Base/api/fault/delay-jitter?meanMs=300&jitterMs=150"

# Random (30% error)
Invoke-Check 'random' "$Base/api/fault/random?errorRate=0.3"

# Rate limit (hit 3 times, limit=2)
Invoke-Check 'rate-limit#1' "$Base/api/fault/rate-limit?limit=2&periodSec=10"
Invoke-Check 'rate-limit#2' "$Base/api/fault/rate-limit?limit=2&periodSec=10"
Invoke-Check 'rate-limit#3' "$Base/api/fault/rate-limit?limit=2&periodSec=10"

# HTTP dependency simulated 500
Invoke-Check 'http-dep' "$Base/api/fault/http-dependency?status=500&delayMs=50"

# DNS failure (likely 503)
Invoke-Check 'dns-failure' "$Base/api/fault/dns-failure?hostname=invalid.local"

# CPU spike
Invoke-Check 'cpu-spike' "$Base/api/fault/cpu-spike?durationMs=500"

# Memory pressure
Invoke-Check 'memory-pressure' "$Base/api/fault/memory-pressure?mb=50&durationMs=1000"

# Disk I/O 5MB
Invoke-Check 'disk-io' "$Base/api/fault/disk-io?sizeMb=5"

# Log spam (returns immediately)
Invoke-Check 'log-spam' "$Base/api/fault/log-spam?lines=50&intervalMs=2&level=info"

Write-Host "Done. Review logs and responses for expected behavior." -ForegroundColor Yellow
