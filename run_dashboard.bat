@echo off
REM GraphRAG Hackathon Dashboard - Windows Launcher
REM This script installs dependencies and runs the Streamlit dashboard

echo.
echo ========================================
echo GraphRAG Hackathon Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)

echo [1/3] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 goto :error

echo [2/3] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 goto :error

echo [3/3] Checking for .env file...
if not exist .env (
    echo.
    echo WARNING: .env file not found!
    echo Create a .env file with your GEMINI_API_KEY:
    echo   GEMINI_API_KEY=your_api_key_here
    echo.
    echo Get your API key at: https://aistudio.google.com/app/apikeys
    echo.
    pause
)

echo.
echo ========================================
echo Launching Streamlit Dashboard...
echo ========================================
echo.

python -m streamlit run dashboard/streamlit_dashboard.py
goto :end

:error
echo.
echo ERROR: Installation failed
echo Please try manually: python -m pip install -r requirements.txt
pause
exit /b 1

:end
pause
