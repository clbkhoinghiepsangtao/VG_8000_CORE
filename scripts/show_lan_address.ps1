$ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.PrefixOrigin -ne 'WellKnown' }
Write-Host 'Dia chi truy cap de may khac trong LAN mo Mini App:'
foreach ($ip in $ips) { Write-Host ("  http://{0}:8000" -f $ip.IPAddress) }
