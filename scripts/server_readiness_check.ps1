param([int]$Port=8000)
Write-Host "=== SERVER READINESS CHECK ==="
$results=@()

function Add-Check($name,$pass,$detail){
  $script:results += [pscustomobject]@{Check=$name;Status=($(if($pass){"PASS"}else{"FAIL"}));Detail=$detail}
}

$os=Get-CimInstance Win32_OperatingSystem
Add-Check "Windows 64-bit" ($os.OSArchitecture -match "64") $os.Caption

$ram=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)
Add-Check "RAM >= 8 GB" ($ram -ge 8) "$ram GB"

$disk=Get-PSDrive C
$free=[math]::Round($disk.Free/1GB,1)
Add-Check "C: free >= 20 GB" ($free -ge 20) "$free GB"

$py=(Get-Command python -ErrorAction SilentlyContinue)
Add-Check "Python available" ($null -ne $py) ($(if($py){$py.Source}else{"Not found"}))

$ip=(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notmatch "^127\." -and $_.PrefixOrigin -ne "WellKnown"} | Select-Object -First 1 -ExpandProperty IPAddress)
Add-Check "LAN IPv4 found" ($null -ne $ip) $ip

$tcp=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
Add-Check "Port $Port listening" ($null -ne $tcp) ($(if($tcp){"Listening"}else{"Not listening"}))

try {
  $health=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 5
  Add-Check "HTTP health" ($health.status -eq 'ok') $health.status
} catch {
  Add-Check "HTTP health" $false $_.Exception.Message
}

$results | Format-Table -AutoSize
if($results.Status -contains "FAIL"){exit 1}else{exit 0}
