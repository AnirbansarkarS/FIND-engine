# PowerShell startup script for FIND-engine
$ProjectDir = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting FIND-engine (Local Private Infrastructure)   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$EnvFile = Join-Path $ProjectDir "backend\.env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "Creating backend\.env file..." -ForegroundColor Yellow
    Set-Content -Path $EnvFile -Value "EXA_API_KEY=f3185198-f358-4c9d-b3f0-ead87cdb7286`nADMIN_USERNAME=admin`nADMIN_PASSWORD=admin123"
}

Write-Host "Launching Backend API Server (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir\backend'; python main.py"

Write-Host "Launching Frontend Dev Server (Vite / React)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " FIND-engine is launching!" -ForegroundColor Green
Write-Host " - React UI:    http://localhost:5173" -ForegroundColor Yellow
Write-Host " - Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host " - Demo Login:  admin / admin123" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
