param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("start","finish")]
  [string]$Action,

  [Parameter(Mandatory=$true)]
  [string]$BatchId,

  [string]$Label = "abnormal",
  [string]$TrafficType = "tool_generated",
  [string]$Tool = "",
  [string]$Notes = ""
)

$LogPath = ".\nginx\logs\access.log"
$OutDir = ".\nginx\collected"
$StateDir = ".\nginx\collected\.state"

if (!(Test-Path $OutDir)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}
if (!(Test-Path $StateDir)) {
  New-Item -ItemType Directory -Path $StateDir | Out-Null
}
if (!(Test-Path $LogPath)) {
  New-Item -ItemType File -Path $LogPath | Out-Null
}

$stateFile = "$StateDir\$BatchId.startline.txt"

if ($Action -eq "start") {
  $startLine = (Get-Content $LogPath -ErrorAction SilentlyContinue).Count
  Set-Content $stateFile $startLine
  Write-Host "Started batch $BatchId at line $startLine"
  exit 0
}

if (!(Test-Path $stateFile)) {
  throw "Missing state file. Run start first for batch $BatchId"
}

$startLine = [int](Get-Content $stateFile)
$logFile = "$OutDir\$BatchId.log"
$metaFile = "$OutDir\$BatchId.meta.txt"

Get-Content $LogPath |
  Select-Object -Skip $startLine |
  Set-Content $logFile

$lineCount = (Get-Content $logFile -ErrorAction SilentlyContinue).Count

@"
batch_id: $BatchId
label: $Label
traffic_type: $TrafficType
tool: $Tool
count_collected: $lineCount
nginx: nginx01
target: http://localhost:8080
log_file: $BatchId.log
notes: $Notes
timezone_note: nginx timestamp is UTC; local time is Asia/Taipei UTC+8
"@ | Set-Content $metaFile

Write-Host "Done: $logFile ($lineCount lines)"
Write-Host "Meta: $metaFile"
