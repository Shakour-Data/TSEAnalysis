# TSEAnalysis Deployment Script for Windows
# This script automates: Venv creation, dependency installation, and server startup.

function Write-Header($msg) {
    Write-Host "`n==== $msg ====" -ForegroundColor Cyan
}

Write-Header "Checking System Requirements"

# 1. Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "CRITICAL: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from python.org"
    exit
}

$pythonVersion = python --version
Write-Host "Found $pythonVersion"

# 2. Virtual Environment Setup
if (!(Test-Path "venv")) {
    Write-Header "Creating Virtual Environment"
    python -m venv venv
    Write-Host "Venv created successfully."
} else {
    Write-Host "Virtual environment already exists."
}

# 3. Activate and Install
Write-Header "Installing/Updating Dependencies"
& .\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing from requirements.txt..."
    pip install -r requirements.txt
} else {
    Write-Host "WARNING: requirements.txt not found. Installing core packages manually."
    pip install flask flask-caching pandas numpy requests matplotlib ta tls-client curl_cffi jdatetime
}

# 4. Database Setup
Write-Header "Verifying Database"
if (!(Test-Path "tse_data.db")) {
    Write-Host "Database file will be initialized on first run of app.py"
} else {
    Write-Host "Existing database found."
}

# 5. Network Check
Write-Header "Network Connectivity Check"
# Testing brsapi.ir accessibility
try {
    $res = Invoke-WebRequest -Uri "https://brsapi.ir" -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Success: BrsApi.ir is reachable." -ForegroundColor Green
} catch {
    Write-Host "WARNING: BrsApi.ir might be blocked in this environment." -ForegroundColor Yellow
    Write-Host "Consider using a Proxy inside app.py if needed."
}

Write-Header "Deployment Complete"
Write-Host "To start the server, run: python app.py" -ForegroundColor Green
Write-Host "The dashboard will be available at: http://127.0.0.1:5000"

$choice = Read-Host "`nDo you want to start the server now? (Y/N)"
if ($choice -eq "Y" -or $choice -eq "y") {
    python app.py
}
