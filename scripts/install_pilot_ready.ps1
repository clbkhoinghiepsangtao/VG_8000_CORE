param(
  [string]$InstallPath = "C:\VinhGiangMiniApp",
  [int]$Port = 8000
)

$ErrorActionPreference="Stop"
Write-Host "=== Vinh Giang Mini App V1.0 - Pilot Ready Installer ==="

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Khong tim thay Python. Hay cai Python 3.11+ va tick Add Python to PATH."
}

$Source = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ($Source -ne $InstallPath) {
  if (Test-Path $InstallPath) {
    Write-Host "Install folder already exists: $InstallPath"
  } else {
    New-Item -ItemType Directory -Path $InstallPath | Out-Null
    Copy-Item "$Source\*" $InstallPath -Recurse -Force
  }
}
Set-Location $InstallPath

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements_release.txt

# Initialize DB and pilot users
$env:PYTHONPATH=$InstallPath
& ".\.venv\Scripts\python.exe" ".\scripts\seed_pilot_users.py"

# Windows Firewall
$ruleName="VinhGiangMiniApp-$Port"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow | Out-Null
}

# Startup scheduled task
$taskName="VinhGiangMiniApp"
$python="$InstallPath\.venv\Scripts\python.exe"
$arguments="-m uvicorn app.main:app --host 0.0.0.0 --port $Port"
$action=New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $InstallPath
$trigger=New-ScheduledTaskTrigger -AtStartup
$principal=New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null

# Backup every 6 hours
$backupTask="VinhGiangMiniApp-Backup"
$backupAction=New-ScheduledTaskAction -Execute $python -Argument "`"$InstallPath\pilot_daily_backup.py`" `"$InstallPath`"" -WorkingDirectory $InstallPath
$backupTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
Register-ScheduledTask -TaskName $backupTask -Action $backupAction -Trigger $backupTrigger -Principal $principal -Force | Out-Null

Write-Host ""
Write-Host "Installation completed."
Write-Host "Run smoke test:"
Write-Host "  $InstallPath\.venv\Scripts\python.exe $InstallPath\scripts\pilot_smoke_test.py"
Write-Host "Start task:"
Write-Host "  Start-ScheduledTask -TaskName VinhGiangMiniApp"
Write-Host "Then open http://localhost:$Port"
