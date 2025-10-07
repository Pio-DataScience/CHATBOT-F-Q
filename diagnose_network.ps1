# Network Diagnostics Script
# Run this to diagnose network connectivity issues

Write-Host "`n=== FAQ System Network Diagnostics ===" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. Check server IP
Write-Host "`n1. Server IP Addresses:" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne "127.0.0.1"} | Select-Object IPAddress, InterfaceAlias | Format-Table

# 2. Check if services are listening
Write-Host "`n2. Service Status:" -ForegroundColor Yellow
$port8000 = netstat -an | findstr "8000" | findstr "LISTENING"
$port8501 = netstat -an | findstr "8501" | findstr "LISTENING"

if ($port8000) {
    Write-Host "  API (8000):     RUNNING" -ForegroundColor Green
} else {
    Write-Host "  API (8000):     NOT RUNNING" -ForegroundColor Red
}

if ($port8501) {
    Write-Host "  GUI (8501):     RUNNING" -ForegroundColor Green
} else {
    Write-Host "  GUI (8501):     NOT RUNNING" -ForegroundColor Red
}

# 3. Check firewall rules (requires admin)
Write-Host "`n3. Firewall Rules:" -ForegroundColor Yellow
try {
    $rules = Get-NetFirewallRule -DisplayName "FAQ*" -ErrorAction Stop
    foreach ($rule in $rules) {
        $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule
        $profile = $rule.Profile
        Write-Host "  $($rule.DisplayName)" -ForegroundColor Green
        Write-Host "    Port: $($portFilter.LocalPort)" -ForegroundColor Gray
        Write-Host "    Profile: $profile" -ForegroundColor Gray
        Write-Host "    Enabled: $($rule.Enabled)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Cannot check (requires Administrator)" -ForegroundColor Yellow
}

# 4. Test local connectivity
Write-Host "`n4. Local Connectivity Test:" -ForegroundColor Yellow
try {
    $test = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 3 -UseBasicParsing
    Write-Host "  localhost:8501  OK (Status: $($test.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  localhost:8501  FAILED" -ForegroundColor Red
}

try {
    $test = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "  localhost:8000  OK (Status: $($test.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  localhost:8000  FAILED" -ForegroundColor Red
}

# 5. Test network connectivity
Write-Host "`n5. Network Connectivity Test:" -ForegroundColor Yellow
$serverIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "172.*" -or $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress

if ($serverIP) {
    Write-Host "  Testing from IP: $serverIP" -ForegroundColor Cyan
    
    try {
        $test = Invoke-WebRequest -Uri "http://${serverIP}:8501" -TimeoutSec 3 -UseBasicParsing
        Write-Host "  ${serverIP}:8501  OK (Status: $($test.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  ${serverIP}:8501  FAILED" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 6. Firewall profile status
Write-Host "`n6. Windows Firewall Status:" -ForegroundColor Yellow
Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table

# 7. Recommendations
Write-Host "`n=== Recommendations ===" -ForegroundColor Cyan
Write-Host "If services are RUNNING but network access FAILS:" -ForegroundColor Yellow
Write-Host "1. Run this script as Administrator to see firewall details" -ForegroundColor White
Write-Host "2. Temporarily disable Windows Firewall to test:" -ForegroundColor White
Write-Host "   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False" -ForegroundColor Gray
Write-Host "3. If it works with firewall off, recreate rules with correct profiles:" -ForegroundColor White
Write-Host "   New-NetFirewallRule -DisplayName 'FAQ API' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Domain,Private,Public" -ForegroundColor Gray
Write-Host "   New-NetFirewallRule -DisplayName 'FAQ GUI' -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow -Profile Domain,Private,Public" -ForegroundColor Gray
Write-Host "4. Re-enable firewall:" -ForegroundColor White
Write-Host "   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True" -ForegroundColor Gray

Write-Host "`n" + "=" * 60
Write-Host "Diagnostics Complete`n" -ForegroundColor Cyan
