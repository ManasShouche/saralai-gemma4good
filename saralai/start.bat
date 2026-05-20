@echo off
title SaralAI — Starting up...
echo.
echo  ===================================
echo   SaralAI - Welfare Access Agent
echo  ===================================
echo.

REM ── 1. Check Ollama ──────────────────────────────────────────────────────────
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama not found. Install from https://ollama.com then run:
    echo         ollama pull gemma4:e4b
    pause
    exit /b 1
)

REM ── 2. Backend setup ─────────────────────────────────────────────────────────
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating Python virtual environment...
    python -m venv .venv
)

echo [2/4] Installing backend dependencies...
.venv\Scripts\pip install -q -r requirements.txt

if not exist "schemes.db" (
    echo [3/4] Seeding scheme database...
    .venv\Scripts\python db\seed.py
) else (
    echo [3/4] Database already seeded.
)

echo [4/4] Starting backend on http://localhost:8000 ...
start "SaralAI Backend" /d "%~dp0backend" cmd /k ".venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

REM ── 3. Frontend setup ────────────────────────────────────────────────────────
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [5/5] Installing frontend dependencies (first run only)...
    npm install --legacy-peer-deps
)

echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo.
echo  On your phone: http://YOUR_IP:3000
echo  (find your IP with: ipconfig)
echo.

start "SaralAI Frontend" /d "%~dp0frontend" cmd /k "npm run dev"

REM Poll until port 3000 is ready before opening browser
echo  Waiting for frontend to start...
:wait_loop
timeout /t 2 /nobreak >nul
powershell -Command "try { (New-Object Net.Sockets.TcpClient).Connect('localhost',3000); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop
start http://localhost:3000

echo  Both services started. Close this window when done.
pause
