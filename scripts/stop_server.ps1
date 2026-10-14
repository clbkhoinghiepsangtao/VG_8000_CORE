$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn app\.main:app' -and $_.CommandLine -match '--port 8000' }
if (-not $procs) { Write-Host 'Khong tim thay Mini App dang chay.'; exit 0 }
foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force; Write-Host "Da dung PID $($p.ProcessId)" }
