@echo off
title FIND-engine Private Infrastructure
echo ========================================================
echo   Starting FIND-engine (Local Private Infrastructure)
echo ========================================================
echo.

if not exist "backend\.env" (
    echo Creating backend\.env from template...
    copy "backend\.env.example" "backend\.env"
)

echo Starting Backend API Server (FastAPI)...
start "FIND-engine Backend" cmd /k "cd backend && python main.py"

echo Starting Frontend Dev Server (Vite / React)...
start "FIND-engine Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo  FIND-engine is starting!
echo  - React UI:    http://localhost:5173
echo  - Backend API: http://localhost:8000
echo  - Demo Login:  admin / admin123
echo ========================================================
echo.
pause
