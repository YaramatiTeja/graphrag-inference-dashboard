# GraphRAG Hackathon Dashboard - PowerShell Launcher (Windows)
# Right-click and select "Run with PowerShell"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GraphRAG Hackathon Dashboard Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "  Install from: https://www.python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "[1/3] Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to upgrade pip" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "[2/3] Installing dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Try manually: python -m pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Check .env file
Write-Host ""
Write-Host "[3/3] Checking configuration..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "⚠ WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Create .env with your GEMINI_API_KEY:" -ForegroundColor Yellow
    Write-Host "  GEMINI_API_KEY=your_api_key_here" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Get your API key at: https://aistudio.google.com/app/apikeys" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "✓ Configuration found" -ForegroundColor Green
}

# Launch dashboard
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Launching Streamlit Dashboard..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Green
Write-Host ""

python -m streamlit run dashboard/streamlit_dashboard.py

Read-Host "Press Enter to exit"
