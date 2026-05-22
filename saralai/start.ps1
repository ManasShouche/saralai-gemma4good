#!/usr/bin/env pwsh
# SaralAI — one-command startup script (PowerShell / cross-platform)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host ""
Write-Host "  ===================================" -ForegroundColor Cyan
Write-Host "   SaralAI - Welfare Access Agent" -ForegroundColor Cyan
Write-Host "  ===================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check Ollama ─────────────────────────────────────────────────────────────
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Ollama not found. Install from https://ollama.com" -ForegroundColor Red
    Write-Host "        Then run: ollama pull gemma4:e4b"
    exit 1
}

# ── 2. Python venv ──────────────────────────────────────────────────────────────
Set-Location $backend

$venvPy = if ($IsWindows -or $env:OS -match "Windows") {
    Join-Path $backend ".venv\Scripts\python.exe"
} else {
    Join-Path $backend ".venv/bin/python"
}

$pip = if ($IsWindows -or $env:OS -match "Windows") {
    Join-Path $backend ".venv\Scripts\pip.exe"
} else {
    Join-Path $backend ".venv/bin/pip"
}

$uvicorn = if ($IsWindows -or $env:OS -match "Windows") {
    Join-Path $backend ".venv\Scripts\uvicorn.exe"
} else {
    Join-Path $backend ".venv/bin/uvicorn"
}

if (-not (Test-Path $venvPy)) {
    Write-Host "[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "[2/4] Installing backend dependencies..." -ForegroundColor Yellow
& $pip install -q -r requirements.txt

$dbPath = Join-Path $backend "schemes.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "[3/4] Seeding scheme database..." -ForegroundColor Yellow
    & $venvPy (Join-Path $backend "db\seed.py")
} else {
    Write-Host "[3/4] Database already seeded." -ForegroundColor Green
}

# ── Ollama memory optimization ─────────────────────────────────────────────────
$env:OLLAMA_MODEL = "gemma4:e4b"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"
$env:OLLAMA_KEEP_ALIVE = "-1"

$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory / 1GB)
if ($ramGB -gt 0 -and $ramGB -le 10) {
    Write-Host ""
    Write-Host "  ⚠  Low RAM detected (${ramGB}GB)." -ForegroundColor Yellow
    Write-Host "     The backend will auto-select a smaller model if available."
    Write-Host "     For best results: ollama pull gemma4:e2b"
    Write-Host ""
}

# ── llama.cpp backend detection ──────────────────────────────────────────────
if ($env:SARALAI_BACKEND -eq "llamacpp") {
    Write-Host "  Using llama.cpp direct backend for edge optimization" -ForegroundColor Cyan
    $llama_check = & $venvPy -c "import llama_cpp" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Installing llama-cpp-python..." -ForegroundColor Yellow
        & $pip install -q llama-cpp-python
    }
    if (-not $env:LLAMACPP_MODEL_PATH) {
        Write-Host ""
        Write-Host "  ⚠  LLAMACPP_MODEL_PATH not set." -ForegroundColor Yellow
        Write-Host "     Set it to your Gemma 4 GGUF file path, e.g.:"
        Write-Host "     `$env:LLAMACPP_MODEL_PATH = 'C:\models\gemma-4-e4b-it-Q4_K_M.gguf'"
        Write-Host ""
    }
}

Write-Host "[4/4] Starting backend on http://localhost:8000 ..." -ForegroundColor Yellow
$backendJob = Start-Process -FilePath $uvicorn -ArgumentList "main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $backend -PassThru -WindowStyle Normal

# ── 3. Frontend ─────────────────────────────────────────────────────────────────
Set-Location $frontend

$nodeModules = Join-Path $frontend "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "[5/5] Installing frontend dependencies (first run only)..." -ForegroundColor Yellow
    npm install --legacy-peer-deps
}

Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "  On your phone: http://$(hostname):3000" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 2
$frontendJob = Start-Process -FilePath "npm" -ArgumentList "run dev -- -H 0.0.0.0" -WorkingDirectory $frontend -PassThru -WindowStyle Normal

Start-Sleep -Seconds 4
Start-Process "http://localhost:3000"

Write-Host "  Both services running. Press Ctrl+C to stop." -ForegroundColor Green
Write-Host ""

# Keep script alive
try {
    Wait-Process -Id $frontendJob.Id
} catch {
    Write-Host "Services stopped."
}
