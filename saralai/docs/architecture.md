# SaralAI — System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER DEVICE (PWA)                            │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────────┐  │
│  │ Camera   │   │  Mic     │   │ Results  │   │ Scheme Detail  │  │
│  │ (Scan)   │   │ (Speak)  │   │ Page     │   │ + Ready Page   │  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └───────┬────────┘  │
│       │              │              │                  │            │
│       └──────────────┴──────────────┴──────────────────┘            │
│                              │                                      │
│                     lib/api.ts (fetch + SSE)                       │
└──────────────────────────────┼──────────────────────────────────────┘
                               │  HTTP / SSE (localhost:8000)
┌──────────────────────────────┼──────────────────────────────────────┐
│                    FASTAPI BACKEND                                  │
│                              │                                      │
│  ┌───────────────────────────┼─────────────────────────────────┐   │
│  │                    Route Layer                               │   │
│  │  POST /api/extract-doc   POST /api/transcribe               │   │
│  │  POST /api/find-schemes  GET  /api/scheme/{id}              │   │
│  │  POST /api/generate-form POST /api/tts                      │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     │                                               │
│  ┌──────────────────▼──────────────────────────────────────────┐   │
│  │               ollama_client.py                               │   │
│  │                                                              │   │
│  │  extract_fields()    ──► Gemma 4 Vision (multimodal prompt) │   │
│  │  transcribe_audio()  ──► Gemma 4 Text (ASR + NLU)          │   │
│  │  run_agentic_loop()  ──► Gemma 4 + Tool Calling Loop        │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     │                                               │
│  ┌──────────────────▼──────────────────────────────────────────┐   │
│  │                  Tool Registry                               │   │
│  │                                                              │   │
│  │  find_matching_schemes ──► SQLite (50 schemes)              │   │
│  │  get_scheme_details    ──► SQLite                           │   │
│  │  find_nearest_office   ──► Template interpolation          │   │
│  │  generate_application  ──► ReportLab PDF                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                     OLLAMA (local)                                  │
│                                                                     │
│              gemma-4-e4b  (4B params, vision + text)               │
│              Runs entirely on CPU/GPU — no cloud, no API key        │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow — Full User Journey

```
Camera JPEG
    │
    ▼
POST /api/extract-doc
    │
    ├─► Gemma 4 Vision → JSON fields (name, dob, gender, district, uid)
    │                    streamed via SSE → FieldChip components
    │
    ▼
sessionStorage["saralai_profile"]

Mic WebM
    │
    ▼
POST /api/transcribe
    │
    ├─► Gemma 4 ASR → transcript + welfare_signals
    │
    ▼
sessionStorage["saralai_narrative"]

profile + narrative
    │
    ▼
POST /api/find-schemes  (SSE)
    │
    ├─► Agentic loop (up to 10 turns):
    │     turn 1: find_matching_schemes(profile + narrative)
    │     turn 2: get_scheme_details(scheme_id) × N
    │     turn 3: find_nearest_office(scheme_id, district)
    │     turn 4: generate_application(scheme_id, profile)
    │
    ├─► SSE "thinking" events → ReasoningStream component
    ├─► SSE "scheme" events   → SchemeCard components
    └─► SSE "done" event      → results phase transition

scheme_id + profile
    │
    ▼
POST /api/generate-form
    │
    └─► ReportLab → pre-filled PDF → download → /ready page
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Local inference (Ollama) | No internet required, no data leaves device |
| SSE streaming | Progressive UI — user sees results as they arrive, not after 10s wait |
| SQLite over vector DB | 50 schemes fit in memory; predicate evaluation is deterministic |
| Custom tool loop | No LangChain dependency; full control over turn budget and error handling |
| Gemma 4 E4B only | Single model handles vision, multilingual text, and structured output |
| Next.js PWA | Installable, offline-capable, camera/mic access on all platforms |
