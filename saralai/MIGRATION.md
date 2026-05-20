# SaralAI Migration & Handoff Document

> **Target AI:** Claude Code  
> **Previous Agent:** Antigravity (Gemini)  
> **Timestamp:** May 15, 2026

Claude, welcome to SaralAI. You are picking up Phase 2 of the development. 

## 1. What Has Been Completed (Phase 0 & Phase 1)

I have successfully initialized the full monolithic project scaffold and wired all the core infrastructure. The project currently runs and passes all core tests.

### Backend Structure
- **FastAPI Core**: Fully functional in `backend/main.py` with routers.
- **Ollama Client**: Multi-turn agent loop, Aadhaar masking, streaming SSE responses (`backend/ollama_client.py`).
- **Tools**: The Predicate Engine (`backend/tools/scheme_finder.py`) supports all 11 evaluation operators (e.g., `any_of`, `between`, `exists`).
- **Database**: SQLite schema (`schemes.db`) successfully populated with 50 curated schemes using the custom seeder (`db/seed.py`).
- **Testing**: Persona-based integration testing (Rukmini, Suresh, Lakshmi) against the database passes flawlessly (`tests/test_eligibility.py`).

### Frontend Structure
- **Next.js & PWA**: PWA manifest and service worker are initialized. `tailwind.config.ts` has the custom saffron UI tokens.
- **API Wiring**: All 5 critical screens are now wired to real API client calls (`lib/api.ts`):
  - `/scan`: Uses real `extractDocument` SSE stream.
  - `/speak`: Records `.webm` audio and hits `transcribeAudio`.
  - `/results`: Fetches profile from `sessionStorage` and triggers `findSchemes` SSE pipeline.
  - `/scheme/[id]`: Renders real DB scheme metadata and allows form generation via `/api/generate-form`.
- **Compilation**: `npm run build` succeeds cleanly with 0 type errors.

## 2. Your Immediate Tasks (Phase 2 & Phase 3)

You must now extract inline code into reusable components, generate required visual assets, and finalize the submission materials.

### Priority 1: Component Extraction
The frontend pages currently have inline UI logic. Please extract these into the `frontend/components/` directory:
1. **`CameraView.tsx`**: Extract from `scan/page.tsx`. Implement edge detection heuristics.
2. **`HoldToTalk.tsx`**: Extract from `speak/page.tsx`.
3. **`Waveform.tsx`**: Extract from `speak/page.tsx` and implement real `requestAnimationFrame` + `AnalyserNode` FFT.
4. **`FieldChip.tsx`**, **`SchemeCard.tsx`**, **`ReasoningStream.tsx`**, **`LanguageToggle.tsx`**.

### Priority 2: PWA Assets & CSS Fixes
1. Generate the missing PWA icons: `icon-192.png`, `icon-512.png`, `icon-maskable-512.png` in `frontend/public/`.
2. Add `postcss.config.js` to ensure Tailwind builds gracefully on all systems.
3. Test the "Add to Home Screen" mechanism.

### Priority 3: Submission Deliverables
1. Perform local End-to-End manual testing of the Rukmini Persona using `ollama pull gemma4:e4b`.
2. Draft the `WRITEUP.md` (1000-1200 words) according to Section 18 of the `CLAUDE.md` specification.
3. Help the team script and prepare for the 2:30 demo video.
4. Add the 2 required redacted Aadhaar images to `data/test_aadhaars/`.

## 3. Context & Gotchas

- **Agent Framework:** We are not using LangChain. We use a custom tool-calling loop passing pure OpenAI-spec JSON schemas to Gemma 4 via Ollama. 
- **Streaming:** The `/api/extract-doc` and `/api/find-schemes` endpoints use Server-Sent Events (SSE). The frontend `lib/sse.ts` provides async generators to handle this perfectly. 
- **Mock Data Removed:** I have completely stripped all `setTimeout` MOCK values from the frontend components. They all rely strictly on `lib/api.ts`.
- **Code Rules:** Adhere strictly to the `CLAUDE.md` specification file. If a problem is vaguely described, defer to the spec.
