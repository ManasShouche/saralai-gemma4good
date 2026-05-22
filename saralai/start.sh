#!/usr/bin/env bash
# SaralAI — one-command startup (Mac / Linux)

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo ""
echo "  ==================================="
echo "   SaralAI — Welfare Access Agent"
echo "  ==================================="
echo ""

# ── 1. Check prerequisites ───────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "[ERROR] Ollama not found."
  echo "        Install from https://ollama.com/download, then run:"
  echo "        ollama pull gemma4:e4b"
  exit 1
fi

if ! command -v node &>/dev/null; then
  echo "[ERROR] Node.js not found. Install from https://nodejs.org (v18+)"
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "[ERROR] Python 3 not found. Install from https://python.org (v3.11+)"
  exit 1
fi

# ── 2. Backend ────────────────────────────────────────────────────────────────
cd "$BACKEND"

if [ ! -f ".venv/bin/python" ]; then
  echo "[1/4] Creating Python virtual environment..."
  python3 -m venv .venv
fi

echo "[2/4] Installing backend dependencies..."
.venv/bin/pip install -q -r requirements.txt

if [ ! -f "db/schemes.db" ]; then
  echo "[3/4] Seeding scheme database..."
  .venv/bin/python db/seed.py
else
  echo "[3/4] Database already seeded."
fi

# ── Ollama memory optimization ───────────────────────────────────────────────
export OLLAMA_MODEL=gemma4:e4b
export OLLAMA_NUM_PARALLEL=1        # Single request slot — saves context memory
export OLLAMA_MAX_LOADED_MODELS=1   # Only one model in RAM at a time
export OLLAMA_FLASH_ATTENTION=1     # Required for KV cache quantization
export OLLAMA_KV_CACHE_TYPE=q8_0    # Halve KV cache memory (~100MB saved)
export OLLAMA_KEEP_ALIVE=-1         # Keep model loaded permanently (no 20s reload)

# Detect system RAM and warn if low
RAM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
RAM_GB=$((RAM_BYTES / 1073741824))
if [ "$RAM_GB" -le 10 ] 2>/dev/null; then
  echo ""
  echo "  ⚠  Low RAM detected (${RAM_GB}GB)."
  echo "     The backend will auto-select a smaller model if available."
  echo "     For best results: ollama pull gemma4:e2b"
  echo ""
fi

# If llama.cpp backend is requested (edge optimization mode)
if [ "$SARALAI_BACKEND" = "llamacpp" ]; then
  echo "  Using llama.cpp direct backend for edge optimization"
  if ! .venv/bin/python3 -c "import llama_cpp" 2>/dev/null; then
    echo "  Installing llama-cpp-python..."
    .venv/bin/pip install -q llama-cpp-python
  fi
  if [ -z "$LLAMACPP_MODEL_PATH" ]; then
    echo "  ⚠  LLAMACPP_MODEL_PATH not set."
    echo "     Set it to your Gemma 4 GGUF file path, e.g.:"
    echo "     export LLAMACPP_MODEL_PATH=~/models/gemma-4-e4b-it-Q4_K_M.gguf"
  fi
fi

echo "[4/4] Starting backend on http://localhost:8000 ..."
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 2

# Pre-warm: load model into Metal GPU memory before user interacts
echo "  Pre-warming Gemma model (this avoids a 20s delay on first request)..."
curl -s http://localhost:11434/api/generate \
  -d '{"model":"'"$OLLAMA_MODEL"'","prompt":"hello","stream":false,"options":{"num_predict":1,"num_ctx":2048}}' \
  > /dev/null 2>&1 &

# ── 3. Frontend ───────────────────────────────────────────────────────────────
cd "$FRONTEND"

if [ ! -d "node_modules" ]; then
  echo "[5/5] Installing frontend dependencies (first run only)..."
  npm install --legacy-peer-deps
fi

# Detect LAN IP for phone access
if command -v ipconfig &>/dev/null; then
  LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "YOUR_IP")
else
  LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "YOUR_IP")
fi

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  On your phone: http://$LAN_IP:3000"
echo "  (tap browser menu → Add to Home Screen for PWA)"
echo ""

echo "  Clearing Next.js build cache..."
rm -rf "$FRONTEND/.next"

npm run dev &
FRONTEND_PID=$!

# Wait for port 3000, then open browser
echo "  Waiting for frontend to start..."
until curl -s http://localhost:3000 > /dev/null 2>&1; do sleep 1; done

if command -v open &>/dev/null; then
  open http://localhost:3000          # macOS
elif command -v xdg-open &>/dev/null; then
  xdg-open http://localhost:3000      # Linux
fi

echo "  Both services running. Press Ctrl+C to stop."
echo ""

# Trap Ctrl+C, terminal close, and script exit — kill both processes cleanly
cleanup() { kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; }
trap cleanup INT TERM EXIT
wait
