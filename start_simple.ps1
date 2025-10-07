# Simple Start Script for FAQ Interface
# Run this from your activated virtual environment

Write-Host "`nStarting FAQ Document Compilation Interface..." -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Cyan

# Start API in background
Write-Host "Starting API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python interface_api.py"

# Wait a bit for API to start
Write-Host "Waiting for API to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Streamlit GUI
Write-Host "`nStarting Streamlit GUI..." -ForegroundColor Yellow
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  API: http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  GUI: http://localhost:8501" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the GUI (API will remain in separate window)`n" -ForegroundColor Yellow

streamlit run interface_gui.py
