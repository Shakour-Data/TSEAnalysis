# TSE Analysis Native Python Deployment Script
# Run this script to deploy the application natively

Write-Host "🚀 Starting TSE Analysis Native Deployment..." -ForegroundColor Green

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check if application can start
Write-Host "🔍 Testing application startup..." -ForegroundColor Yellow
$testProcess = Start-Process python -ArgumentList "app.py" -NoNewWindow -PassThru
Start-Sleep -Seconds 5

if (!$testProcess.HasExited) {
    Stop-Process -Id $testProcess.Id -Force
    Write-Host "✅ Application started successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Application failed to start" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "🌐 To start the application, run: python app.py" -ForegroundColor Cyan
Write-Host "📊 API will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🔧 Management Panel: http://localhost:5000/management" -ForegroundColor Cyan

Write-Host "`n📋 Useful commands:" -ForegroundColor Cyan
Write-Host "  • Start: python app.py" -ForegroundColor White
Write-Host "  • Stop: Ctrl+C in the terminal" -ForegroundColor White
Write-Host "  • Test: python -m pytest tests/" -ForegroundColor White