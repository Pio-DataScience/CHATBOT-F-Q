# Fix Firewall Rules
# Run this AS ADMINISTRATOR to properly configure firewall

Write-Host "`nFixing Firewall Rules for FAQ System..." -ForegroundColor Green

# Remove old rules if they exist
Write-Host "`nRemoving old rules..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "FAQ API Port 8000" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "FAQ GUI Port 8501" -ErrorAction SilentlyContinue

# Create new rules with ALL profiles (Domain, Private, Public)
Write-Host "Creating new rules for ALL network profiles..." -ForegroundColor Yellow

New-NetFirewallRule `
    -DisplayName "FAQ API Port 8000" `
    -Description "Allow inbound access to FAQ API on port 8000" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Domain,Private,Public `
    -Enabled True

Write-Host "  Created: FAQ API Port 8000" -ForegroundColor Green

New-NetFirewallRule `
    -DisplayName "FAQ GUI Port 8501" `
    -Description "Allow inbound access to FAQ GUI on port 8501" `
    -Direction Inbound `
    -LocalPort 8501 `
    -Protocol TCP `
    -Action Allow `
    -Profile Domain,Private,Public `
    -Enabled True

Write-Host "  Created: FAQ GUI Port 8501" -ForegroundColor Green

# Verify
Write-Host "`nVerifying firewall rules..." -ForegroundColor Yellow
$rules = Get-NetFirewallRule -DisplayName "FAQ*"

foreach ($rule in $rules) {
    $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule
    Write-Host "`n  Rule: $($rule.DisplayName)" -ForegroundColor Cyan
    Write-Host "    Port: $($portFilter.LocalPort)" -ForegroundColor White
    Write-Host "    Protocol: $($portFilter.Protocol)" -ForegroundColor White
    Write-Host "    Direction: $($rule.Direction)" -ForegroundColor White
    Write-Host "    Profile: $($rule.Profile)" -ForegroundColor White
    Write-Host "    Enabled: $($rule.Enabled)" -ForegroundColor White
    Write-Host "    Action: $($rule.Action)" -ForegroundColor White
}

Write-Host "`n" + "=" * 60
Write-Host "Firewall rules created successfully!" -ForegroundColor Green
Write-Host "Clients should now be able to connect from other machines." -ForegroundColor Green
Write-Host "=" * 60 + "`n"
