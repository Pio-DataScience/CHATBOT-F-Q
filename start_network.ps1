# Start Network-Accessible FAQ Interface
# Run this script to make the system accessible from other machines

Write-Host "`nStarting FAQ Interface for Network Access..." -ForegroundColor Green
Write-Host "=" * 60

# Check for virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Get server IP address (excluding virtual adapters like Docker/WSL)
try {
    # Try to get real LAN IP (192.168.x.x or 10.x.x.x) - exclude 172.17.x.x (Docker/WSL)
    $serverIP = (Get-NetIPAddress -AddressFamily IPv4 | 
        Where-Object {
            ($_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*") -and 
            $_.IPAddress -ne "127.0.0.1"
        } | 
        Select-Object -First 1).IPAddress
    
    if (-not $serverIP) {
        Write-Host "WARNING: Could not find LAN IP (192.168.x.x or 10.x.x.x)" -ForegroundColor Yellow
        Write-Host "Please manually find your LAN IP with: ipconfig" -ForegroundColor Yellow
        $serverIP = Read-Host "Enter your LAN IP address"
    }
    
    Write-Host "`nServer LAN IP Address: $serverIP" -ForegroundColor Green
} catch {
    Write-Host "Could not auto-detect IP. Using localhost..." -ForegroundColor Yellow
    $serverIP = "localhost"
}

# Display access information
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Network Access URLs:" -ForegroundColor White
Write-Host "  ===================" -ForegroundColor White
Write-Host "  API:      http://${serverIP}:8000" -ForegroundColor Green
Write-Host "  API Docs: http://${serverIP}:8000/docs" -ForegroundColor Green
Write-Host "  GUI:      http://${serverIP}:8501" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nShare the GUI URL with your team!" -ForegroundColor Yellow
Write-Host "They can access it from: http://${serverIP}:8501`n" -ForegroundColor Yellow

# Set API URL for GUI
$env:API_BASE_URL = "http://${serverIP}:8000"
Write-Host "API_BASE_URL set to: $env:API_BASE_URL" -ForegroundColor Cyan

# Check firewall (informational only - requires admin)
Write-Host "`nFirewall Configuration:" -ForegroundColor Yellow
Write-Host "Make sure you have created firewall rules for ports 8000 and 8501" -ForegroundColor Cyan
Write-Host "If you haven't already, run as Administrator:" -ForegroundColor Gray
Write-Host "  New-NetFirewallRule -DisplayName 'FAQ API Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow" -ForegroundColor DarkGray
Write-Host "  New-NetFirewallRule -DisplayName 'FAQ GUI Port 8501' -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow" -ForegroundColor DarkGray

Write-Host "`n" + "=" * 60

# Start API in background
Write-Host "`nStarting API server in background..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; Write-Host 'API Server Running' -ForegroundColor Green; python interface_api.py"

# Wait for API to start
Write-Host "Waiting for API to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test API connection
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "API is running successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not verify API status" -ForegroundColor Yellow
}

# Start Streamlit GUI with network access
Write-Host "`nStarting Streamlit GUI..." -ForegroundColor Yellow
Write-Host "This window will show Streamlit logs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the GUI`n" -ForegroundColor Yellow
Write-Host "Note: Browser may open to 0.0.0.0 - ignore it and use the URL above!`n" -ForegroundColor Yellow

# Disable Streamlit's auto-browser and use correct address
streamlit run interface_gui.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

# Open browser with correct IP after a delay
Start-Sleep -Seconds 3
Start-Process "http://${serverIP}:8501"
