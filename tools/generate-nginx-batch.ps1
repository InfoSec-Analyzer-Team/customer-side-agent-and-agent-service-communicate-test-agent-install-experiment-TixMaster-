param(
  [string]$BatchId = "nginx01_batch_sqli_001",
  [string]$Label = "abnormal",
  [string]$AttackType = "sqli",
  [int]$Count = 500
)

$BaseUrl = "http://localhost:8080"
$LogDir = ".\nginx\logs"
$OutDir = ".\nginx\collected"

$ipPools = @{
  sqli = @("203.0.113.10", "203.0.113.11", "203.0.113.12", "203.0.113.13")
  xss = @("198.51.100.20", "198.51.100.21", "198.51.100.22", "198.51.100.23")
  traversal = @("192.0.2.30", "192.0.2.31", "192.0.2.32", "192.0.2.33")
  scanner = @("10.10.20.40", "10.10.20.41", "10.10.20.42", "10.10.20.43")
  benign = @("172.16.30.50", "172.16.30.51", "172.16.30.52", "172.16.30.53")
}

$userAgents = @{
  sqli = @("sqlmap/1.8", "Mozilla/5.0 Chrome", "curl/8.0")
  xss = @("Mozilla/5.0 Chrome", "Mozilla/5.0 Firefox", "curl/8.0")
  traversal = @("nikto", "Mozilla/5.0 Edge", "curl/8.0")
  scanner = @("Nikto/2.5.0", "dirsearch/0.4.3", "curl/8.0")
  benign = @("Mozilla/5.0 Chrome", "Mozilla/5.0 Firefox", "Mozilla/5.0 Edge")
}

$paths = @{
  sqli = @(
    "/api/events?id=1%27%20OR%20%271%27%3D%271",
    "/api/events?id=1%20UNION%20SELECT%201,2,3",
    "/login.html?email=admin%40test.com%27--",
    "/api/users/login?user=admin%27%20OR%201%3D1--"
  )
  xss = @(
    "/search?q=%3Cscript%3Ealert(1)%3C/script%3E",
    "/event-detail.html?name=%3Cimg%20src=x%20onerror=alert(1)%3E",
    "/login.html?next=%3Csvg%20onload=alert(1)%3E"
  )
  traversal = @(
    "/../../etc/passwd",
    "/..%2F..%2F..%2Fetc%2Fpasswd",
    "/static/../../backend/.env",
    "/download?file=..%2F..%2Fwindows%2Fwin.ini"
  )
  scanner = @(
    "/admin",
    "/.env",
    "/wp-admin",
    "/phpmyadmin",
    "/server-status",
    "/backup.zip"
  )
  benign = @(
    "/",
    "/index.html",
    "/login.html",
    "/register.html",
    "/event-detail.html?id=1",
    "/checkout.html?eventId=1&ticketId=1&quantity=1",
    "/api/events"
  )
}

if (!(Test-Path $OutDir)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$accessLog = "$LogDir\access.log"
if (!(Test-Path $accessLog)) {
  New-Item -ItemType File -Path $accessLog | Out-Null
}
$startLine = (Get-Content $accessLog -ErrorAction SilentlyContinue).Count

$ips = $ipPools[$AttackType]
$uas = $userAgents[$AttackType]
$selectedPaths = $paths[$AttackType]

for ($i = 0; $i -lt $Count; $i++) {
  $ip = Get-Random $ips
  $ua = Get-Random $uas
  $path = Get-Random $selectedPaths

  try {
    Invoke-WebRequest -UseBasicParsing `
      -Uri "$BaseUrl$path" `
      -Headers @{ "X-Forwarded-For" = $ip; "User-Agent" = $ua } `
      -TimeoutSec 5 `
      -ErrorAction SilentlyContinue | Out-Null
  } catch {
  }
}

$logFile = "$OutDir\$BatchId.log"
$metaFile = "$OutDir\$BatchId.meta.txt"

Get-Content $accessLog |
  Select-Object -Skip $startLine |
  Set-Content $logFile

@"
batch_id: $BatchId
label: $Label
traffic_type: $AttackType
count_requested: $Count
nginx: nginx01
target: $BaseUrl
ip_pool: $($ips -join ',')
user_agent_pool: $($uas -join ',')
log_file: $BatchId.log
timezone_note: nginx timestamp is UTC; local time is Asia/Taipei UTC+8
"@ | Set-Content $metaFile

Write-Host "Done: $logFile"
Write-Host "Meta: $metaFile"