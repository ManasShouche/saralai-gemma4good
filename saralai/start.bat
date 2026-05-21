@echo off
title SaralAI — Starting up...
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

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
cd /d "%BACKEND_DIR%"

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

REM ── Ollama memory optimization ──────────────────────────────────────────────
set OLLAMA_MODEL=gemma4:e4b
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_FLASH_ATTENTION=1

REM ── Detect RAM and warn if low ────────────────────────────────────────────
for /f "skip=1" %%A in ('wmic computersystem get TotalPhysicalMemory 2^>nul') do (
    set /a "RAM_GB=%%A / 1073741824" 2>nul
    goto :ram_done
)
:ram_done
if defined RAM_GB (
    if %RAM_GB% LEQ 10 (
        echo.
        echo   WARNING: Low RAM detected ^(%RAM_GB%GB^).
        echo   The backend will auto-select a smaller model if available.
        echo   For best results: ollama pull gemma4:e2b
        echo.
    )
)

REM ── llama.cpp backend detection ───────────────────────────────────────────
if "%SARALAI_BACKEND%"=="llamacpp" (
    echo   Using llama.cpp direct backend for edge optimization
    .venv\Scripts\python -c "import llama_cpp" 2>nul
    if errorlevel 1 (
        echo   Installing llama-cpp-python...
        .venv\Scripts\pip install -q llama-cpp-python
    )
    if not defined LLAMACPP_MODEL_PATH (
        echo   WARNING: LLAMACPP_MODEL_PATH not set.
        echo   Set it to your Gemma 4 GGUF file path, e.g.:
        echo   set LLAMACPP_MODEL_PATH=C:\models\gemma-4-e4b-it-Q4_K_M.gguf
    )
)

echo [4/4] Starting backend on http://localhost:8000 ...
start "SaralAI Backend" cmd /k "cd /d "%BACKEND_DIR%" && set OLLAMA_MODEL=gemma4:e4b && set OLLAMA_NUM_PARALLEL=1 && set OLLAMA_MAX_LOADED_MODELS=1 && set OLLAMA_FLASH_ATTENTION=1 && .venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

REM ── 3. Frontend setup ────────────────────────────────────────────────────────
cd /d "%FRONTEND_DIR%"

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

echo  Clearing Next.js build cache...
if exist "%FRONTEND_DIR%\.next" rmdir /s /q "%FRONTEND_DIR%\.next"

start "SaralAI Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

REM Poll until port 3000 is ready before opening browser
echo  Waiting for frontend to start...
:wait_loop
timeout /t 2 /nobreak >nul
powershell -Command "try { (New-Object Net.Sockets.TcpClient).Connect('localhost',3000); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop
start http://localhost:3000

echo  Both services started. Close this window when done.
pause
