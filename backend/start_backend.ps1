# Simple script to start the backend
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting CampusOS Backend" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  No virtual environment found. Using global Python." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting uvicorn server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
$port = $env:PORT
if ([string]::IsNullOrWhiteSpace($port)) {
    $port = "8000"
}

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $port
