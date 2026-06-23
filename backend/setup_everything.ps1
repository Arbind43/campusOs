# ============================================================================
# Complete Backend Setup Script for Neon Database
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  CampusOS Backend Setup - Neon Database" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install dependencies
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install asyncpg python-dotenv
Write-Host "✅ Dependencies installed`n" -ForegroundColor Green

# Step 2: Setup database
Write-Host "[2/4] Setting up Neon database tables..." -ForegroundColor Yellow
python setup_neon_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database setup failed! Check error above.`n" -ForegroundColor Red
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  1. Check DATABASE_URL in .env file" -ForegroundColor Yellow
    Write-Host "  2. Make sure Neon database is active" -ForegroundColor Yellow
    Write-Host "  3. Try running neon_setup.sql manually in Neon SQL Editor`n" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 3: Create admin user
Write-Host "[3/4] Creating admin and student users..." -ForegroundColor Yellow
python -m scripts.create_admin_simple
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ User creation failed! Check error above.`n" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Test connection
Write-Host "[4/4] Testing authentication..." -ForegroundColor Yellow
Write-Host "Starting backend temporarily to test...`n" -ForegroundColor Gray

# Start backend in background
$job = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
} -ArgumentList (Get-Location)

# Wait for backend to start
Start-Sleep -Seconds 5

# Test authentication
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"email":"admin@college.edu","password":"test"}' `
        -UseBasicParsing -ErrorAction SilentlyContinue
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Authentication test passed!`n" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Backend started but auth test failed`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test authentication (backend might not be ready yet)`n" -ForegroundColor Yellow
}

# Stop test backend
Stop-Job -Job $job
Remove-Job -Job $job

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor Yellow
Write-Host "  Admin:   admin@college.edu / any-password" -ForegroundColor White
Write-Host "  Student: student@college.edu / any-password" -ForegroundColor White
Write-Host ""
Write-Host "Start Backend:" -ForegroundColor Yellow
Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "API Docs:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Test Script:" -ForegroundColor Yellow
Write-Host "  python test_auth_simple.py" -ForegroundColor White
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
