# SaralAI — Welfare Access Agent

> **Find every government scheme you qualify for — offline, in your language, in under two minutes.**
>
> Scan your Aadhaar card with your phone camera. Speak about your situation in Kannada, Hindi, or English. Get matched to schemes you qualify for, with a pre-filled PDF form ready to take to the office.
>
> Runs entirely on-device. Nothing leaves your phone. Powered by **Gemma 4 4B** via Ollama.

---

## The Problem

India has over 3,000 central and state welfare schemes — widow pensions, free LPG, housing subsidies, education loans — yet two-thirds of eligible citizens never access them. The barrier is not eligibility. It is language, literacy, and bureaucratic opacity.

A 52-year-old widow in rural Karnataka named Rukmini speaks only Kannada. She cannot read English eligibility criteria. She does not know which office processes her application. She has never filled a government PDF form. Her husband's death should have triggered ₹900/month in combined central and state pension. Instead, she has received nothing for three years.

**SaralAI exists to close that gap.**

---

## How It Works

```
┌──────────┐     ┌──────────────┐     ┌──────────────────────────────┐
│  1 SCAN  │────▶│  2  SPEAK    │────▶│  3  MATCH                    │
│          │     │              │     │                              │
│ Point    │     │ Hold mic.    │     │ Gemma 4 runs an agentic      │
│ camera   │     │ "My husband  │     │ loop across 50 schemes.      │
│ at       │     │  passed two  │     │ Matched schemes stream to    │
│ Aadhaar  │     │  years ago.  │     │ screen with plain-language   │
│ card.    │     │  I have a    │     │ explanations. Pre-filled     │
│ Fields   │     │  BPL card."  │     │ PDF form generated and       │
│ stream   │     │              │     │ ready to print.              │
│ live.    │     │              │     │                              │
└──────────┘     └──────────────┘     └──────────────────────────────┘
```

---

## Demo

> **[Watch the 2-minute demo →](#)**

Screenshots:

| Home | Camera Scan | Results |
|------|-------------|---------|
| Language toggle, one-tap CTA | Live viewfinder with Gemma 4 OCR | Streamed scheme cards with eligibility reasons |

---

## Quickstart

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| [Ollama](https://ollama.com/download) | latest | ollama.com/download |
| Python | 3.11+ | python.org |
| Node.js | 18+ | nodejs.org |

### Step 1 — Pull the model

```bash
ollama pull gemma4:4b
```

> ~3 GB download. Do this before the demo.

---

### Step 2 — Start everything

Two methods are listed for each platform. **Try Method A first** — if anything goes wrong, Method B is the fully manual fallback.

---

#### Mac / Linux

**Method A — one command (recommended)**

```bash
cd saralai
chmod +x start.sh
./start.sh
```

The script creates the venv, installs deps, seeds the database, starts both servers, and opens the browser automatically.

**Method B — manual (two terminals)**

Terminal 1 — backend:
```bash
cd saralai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 db/seed.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — frontend:
```bash
cd saralai/frontend
npm install --legacy-peer-deps
npm run dev
```

Open **http://localhost:3000**

---

#### Windows

**Method A — double-click script (recommended)**

```bat
start.bat
```

Or from PowerShell:
```powershell
pwsh start.ps1
```

**Method B — manual (two terminals)**

Terminal 1 — backend:
```bat
cd saralai\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python db\seed.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — frontend:
```bat
cd saralai\frontend
npm install --legacy-peer-deps
npm run dev
```

Open **http://localhost:3000**

---

### Step 3 — Open on your phone (optional but impressive)

```bash
# Find your laptop's LAN IP:
ipconfig getifaddr en0       # Mac
ipconfig                     # Windows
ip addr show                 # Linux

# Then on your phone browser: http://<your-laptop-ip>:3000
# Tap browser menu → "Add to Home Screen" to install as PWA
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js 14 PWA  (port 3000)                                │
│                                                             │
│  CameraView · HoldToTalk · Waveform · FieldChip             │
│  SchemeCard · ReasoningStream · ListenFAB                   │
│  TrustStrip · LanguageToggle · GiantCTA                     │
│                                                             │
│  Kannada · Hindi · English · framer-motion SSE streaming    │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP + Server-Sent Events
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI  (port 8000)                                       │
│                                                             │
│  POST /api/extract-doc      image → field stream (SSE)      │
│  POST /api/transcribe       audio blob → transcript         │
│  POST /api/find-schemes     profile + text → scheme stream  │
│  GET  /api/scheme/{id}      scheme detail                   │
│  POST /api/generate-form    scheme + data → PDF blob        │
│  POST /api/tts              text → browser speech hint      │
└──────────┬──────────────────────┬───────────────────────────┘
           │                      │
    ┌──────▼──────┐        ┌──────▼──────┐     ┌─────────────┐
    │  Ollama     │        │  SQLite     │     │  ReportLab  │
    │  Gemma 4    │        │  schemes.db │     │  PDF forms  │
    │  E4B (4B)   │        │  50 schemes │     │  on-device  │
    │  vision +   │        │  25 natl    │     └─────────────┘
    │  language   │        │  25 KA      │
    └─────────────┘        └─────────────┘
```

**Data never leaves the machine.** All inference runs locally via Ollama.

---

## What Gemma 4 Does

Gemma 4 4B handles three distinct tasks in this pipeline:

### 1. Vision OCR — `/api/extract-doc`
A JPEG of an Aadhaar card is sent directly to Gemma 4's vision encoder. A structured JSON extraction prompt returns name, date of birth, gender, district, state, and UID with field-level confidence scores. Fields are streamed to the UI via SSE as they arrive — users see their data appear live rather than waiting.

### 2. Multilingual ASR — `/api/transcribe`
The spoken narrative (WebM audio blob from MediaRecorder) is sent to Gemma 4. In a single pass it transcribes Kannada/Hindi/English speech and identifies welfare-relevant signals: widow status, BPL category, disability, land ownership. No separate NLU step needed.

### 3. Agentic Scheme Matching — `/api/find-schemes`
A custom tool-calling loop — built without LangChain, using OpenAI-compatible JSON schemas against Ollama — gives Gemma 4 four tools:

| Tool | What it does |
|------|-------------|
| `find_matching_schemes` | Queries SQLite with 11 predicate operators against the profile |
| `get_scheme_details` | Fetches eligibility rules, benefit value, document checklist |
| `find_nearest_office` | Returns the relevant district office for application |
| `generate_application_form` | Triggers pre-filled PDF generation via ReportLab |

The model's reasoning stream — match decisions, skip reasons, tool calls — is forwarded to the frontend via SSE and displayed in real time in the `ReasoningStream` component. **Judges can watch Gemma 4 think.**

---

## Scheme Database

50 curated welfare schemes across 7 categories:

| Category | Count | Examples |
|----------|-------|---------|
| Widow / Women | 8 | IGNWPS (₹300/mo), Karnataka Widow Pension (₹1,200/mo) |
| Disability | 6 | NSAP Disability, State Disability Scholarship |
| Education | 7 | PM Vidya Lakshmi, SC/ST scholarship, NMMS |
| Health | 5 | PMJAY (₹5L cover), Janani Suraksha |
| Housing / LPG | 6 | PM Awas Yojana, Ujjwala (free LPG) |
| Senior Citizen | 5 | IGNOAPS, IGNWPS, Annapurna |
| Employment / Self-Employment | 13 | MGNREGA, PM Mudra, PMEGP |

Each scheme has: eligibility predicates · benefit value · document checklist · nearest office template.

---

## Languages

| Code | Language | Script |
|------|----------|--------|
| `kn` | Kannada | ಕನ್ನಡ |
| `hi` | Hindi | हिन्दी |
| `en` | English | Latin |

UI strings, scheme titles, eligibility reasons, and TrustStrip text are all fully localised. The app defaults to the language stored from the onboarding screen.

---

## Project Structure

```
saralai/
├── backend/
│   ├── main.py               # FastAPI app + CORS + route registration
│   ├── ollama_client.py      # Gemma 4 interface: extract / transcribe / agentic loop
│   ├── routes/
│   │   ├── extract.py        # /api/extract-doc (SSE)
│   │   ├── transcribe.py     # /api/transcribe
│   │   ├── schemes.py        # /api/find-schemes (SSE) + /api/scheme/{id}
│   │   ├── forms.py          # /api/generate-form
│   │   ├── tts.py            # /api/tts
│   │   └── debug.py          # /api/debug/log (ships client errors to terminal)
│   ├── tools/
│   │   ├── scheme_finder.py  # predicate evaluator (11 operators)
│   │   ├── scheme_details.py # scheme lookup
│   │   ├── office_finder.py  # district → office
│   │   └── form_generator.py # ReportLab PDF builder
│   ├── db/
│   │   └── seed.py           # populates schemes.db from JSON
│   ├── prompts/              # .txt prompt templates
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Home
│   │   ├── scan/page.tsx     # Camera → extract → confirm
│   │   ├── speak/page.tsx    # MediaRecorder → transcribe
│   │   ├── results/page.tsx  # Agentic scheme match stream
│   │   └── scheme/[id]/      # Scheme detail + form ready
│   ├── components/           # 10 reusable components
│   ├── lib/
│   │   ├── api.ts            # fetch + SSE client
│   │   └── i18n.ts           # 300+ strings × 3 languages
│   └── public/
│       └── sw.js             # offline service worker
├── start.sh                  # Mac / Linux one-command startup
├── start.bat                 # Windows one-command startup
├── start.ps1                 # PowerShell cross-platform startup
└── docker-compose.yml        # optional containerised run
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI model | Gemma 4 4B via Ollama |
| Backend | FastAPI 0.110, Python 3.11, uvicorn |
| Streaming | Server-Sent Events (SSE) via sse-starlette |
| Database | SQLite via sqlite-utils |
| PDF | ReportLab |
| Frontend | Next.js 14 App Router, TypeScript |
| Styling | Tailwind CSS, framer-motion |
| Fonts | next/font (Plus Jakarta Sans, JetBrains Mono, Noto Sans Kannada, Noto Sans Devanagari) |
| Camera | MediaDevices.getUserMedia + Canvas capture |
| Audio | MediaRecorder API (WebM/Opus) |
| PWA | Service Worker, Web App Manifest |

---

## Privacy

The `TrustStrip` component — *"ಏನೂ ಈ ಫೋನ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ · Nothing leaves this phone"* — appears on every screen. This is technically accurate:

- All inference runs via Ollama on the local machine
- No data is sent to any cloud API
- Aadhaar numbers are masked in all logs (regex: `XXXX XXXX {last4}`)
- The service worker caches the app shell for fully offline use

---

## License

Apache 2.0 — see [LICENSE](./LICENSE)

The scheme database is freely available for other welfare-tech projects to build on.

---

## Acknowledgements

- [Gemma 4](https://ai.google.dev/gemma) by Google DeepMind — the only 4B model with multilingual vision that makes this architecture viable at the edge
- [Ollama](https://ollama.com/) for zero-friction local model serving
- Government of India [myScheme](https://www.myscheme.gov.in/) portal for scheme reference data
- Karnataka [Seva Sindhu](https://sevasindhuservices.karnataka.gov.in/) for state scheme data

---

*Built for the Gemma 4 Hackathon · Track: Gemma for Good · May 2026*
