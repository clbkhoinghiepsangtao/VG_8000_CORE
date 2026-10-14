$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { throw 'Chua co .venv. Hay chay install_pilot.ps1 truoc.' }
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Out = Join-Path $LogDir 'server-out.log'
$Err = Join-Path $LogDir 'server-error.log'
Start-Process -FilePath $Python -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000' -WorkingDirectory $Root -RedirectStandardOutput $Out -RedirectStandardError $Err -WindowStyle Hidden
Write-Host 'Mini App Vinh Giang da khoi dong tren cong 8000.'
