@echo off
echo Starting FAQ Document Compilation Interface...
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Virtual environment found. Activating...
    echo.
) else (
    echo ERROR: Virtual environment not found at .venv
    echo Please create it first: python -m venv .venv
    pause
    exit /b 1
)

echo Starting API server in background...
start "FAQ API Server" cmd /k ".venv\Scripts\activate.bat && python interface_api.py"

echo Waiting for API to start...
timeout /t 5 /nobreak >nul

echo Starting Streamlit GUI...
echo.
echo ============================================
echo   API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   GUI: http://localhost:8501
echo ============================================
echo.
echo Close both windows to stop the services
echo.

call .venv\Scripts\activate.bat
streamlit run interface_gui.py
