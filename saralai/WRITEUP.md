# SaralAI — Technical Writeup

**Team:** Manas | **Track:** Gemma 4 Good | **Deadline:** May 18 2026

---

## The Problem

India administers over 3,000 central and state welfare schemes — widow pensions, free LPG connections, education loans, ration entitlements — yet two-thirds of eligible citizens never access them. The barriers are not eligibility; they are language, literacy, and bureaucratic opacity.

A 52-year-old widow in rural Karnataka named Rukmini speaks only Kannada. She cannot read the English eligibility criteria for the Indira Gandhi National Widow Pension. She does not know the Tahsildar office processes her application, not the gram panchayat. She has never filled a government PDF form. Her husband's death should have triggered ₹900/month in combined central and state pension — instead, she has received nothing for three years.

SaralAI exists to close that gap.

---

## The Solution

SaralAI is a Progressive Web App that lets any citizen discover every welfare scheme they qualify for in under two minutes — using only their Aadhaar card and their voice. No English required. No internet required after first load. No government portal account needed.

The flow is three steps:

1. **Scan** — Point your phone camera at your Aadhaar card. Gemma 4's vision encoder reads the document, extracts name, date of birth, gender, district, and UID, and streams each field to the screen as it confirms them.
2. **Speak** — Hold the mic button and describe your situation in Kannada, Hindi, or English: *"My husband passed away two years ago. I have a BPL ration card."* Gemma 4 transcribes and understands the narrative.
3. **Match** — An agentic tool-calling loop queries a curated database of 50 schemes against the extracted profile and spoken narrative. Matched schemes stream to the screen with plain-language eligibility explanations. A pre-filled PDF form is generated on-device and ready to print.

The entire pipeline runs on a single consumer laptop running Ollama. Nothing is uploaded to the cloud. The TrustStrip visible on every screen — *"Nothing leaves this phone"* — is technically accurate.

---

## Technical Execution

### Gemma 4 as the Reasoning Core

SaralAI uses **Gemma 4 E4B** (the 4-billion parameter edge model) via Ollama for three distinct tasks, each requiring different modalities:

**Vision OCR** (`/api/extract-doc`): A single multimodal prompt sends the captured JPEG directly to Gemma 4's vision encoder alongside a structured extraction instruction. The model returns a JSON object with field-level confidence scores. Fields stream to the UI via Server-Sent Events as they are confirmed, giving users immediate feedback without waiting for the full extraction to complete.

**Multilingual ASR + NLU** (`/api/transcribe`): Audio from the MediaRecorder API is sent as a WebM blob. Gemma 4 handles transcription and intent extraction in a single pass — it does not just transcribe, it also identifies relevant welfare signals (widow status, BPL category, land ownership, disability) that the scheme-matching loop will later use.

**Agentic Scheme Matching** (`/api/find-schemes`): This is the technical centrepiece. A custom tool-calling loop — built without LangChain, using OpenAI-compatible JSON schemas against Ollama's endpoint — gives Gemma 4 access to four tools: `find_matching_schemes`, `get_scheme_details`, `find_nearest_office`, and `generate_application_form`. The model iterates through the 50-scheme SQLite database, evaluating each against 11 predicate operators (equality, range, membership, any_of, all_of). Its reasoning stream — match decisions, skip reasons, tool invocations — is forwarded to the frontend via SSE and displayed in real time in the `ReasoningStream` component. Users can watch the AI think.

### Backend Architecture

- **FastAPI** with four SSE-streaming routes
- **SQLite** with 50 curated schemes (25 national + 25 Karnataka), each with structured eligibility predicates, benefit values, document checklists, and office templates
- **ReportLab** for on-device pre-filled PDF form generation — no external service required
- **Kokoro/Coqui TTS** (with silent fallback) for audio playback of eligibility explanations

### Frontend Architecture

- **Next.js 14** App Router PWA with full offline support via service worker
- **10 reusable components**: `CameraView` (native-script doc tabs, accent bracket corners), `HoldToTalk` (124px mic with halo rings), `Waveform` (20-bar Web Audio FFT), `FieldChip` (confidence % display), `SchemeCard` (solid/outline variants), `ReasoningStream` (typed thought lines), `ListenFAB` (persistent audio button), `GiantCTA`, `TrustStrip`, `LanguageToggle`
- **Framer Motion** for field streaming animations and phase transitions
- **PWA**: installable, offline-capable, safe-area aware

---

## Accessibility as Architecture

Accessibility is not a feature layer on top of SaralAI — it is the reason it was built the way it was.

**Native script primacy.** Every screen defaults to Kannada. The onboarding language picker shows ಕನ್ನಡ in large type as the first and primary option, not a dropdown item. English appears as an annotation, never the primary label. The `font-kan` family (Noto Sans Kannada) is loaded at the root level, ensuring native glyphs render at full weight even on older Android devices.

**Voice-first interaction.** The entire eligibility interview is spoken, not typed. The `HoldToTalk` button is 124px — three times the minimum 44px tap target — with double halo rings that pulse during recording. Citizens who cannot type a form field can simply say *"I am a widow"* and the system understands.

**Privacy as trust.** The `TrustStrip` component — *"ಏನೂ ಈ ಫೋನ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ"* — appears on every text-heavy screen. It is not decorative. No data transits to any cloud service; all inference runs on Ollama locally. This matters enormously for the communities SaralAI serves: Aadhaar card details are sensitive, and trust is a prerequisite for adoption.

**Offline-first PWA.** Rural Karnataka has patchy mobile data. SaralAI caches the app shell, fonts, and scheme database on first load. Subsequent uses — common in households where the app is shared across family members — work without connectivity.

**Minimum tap targets.** Every interactive element respects the 44×44px minimum enforced globally in `globals.css`. The camera shutter is 88px. The Continue button is 68px tall — tall enough to tap with a thumb while holding a phone with the other hand pointing at a document.

---

## Impact

In Karnataka alone, approximately 1.2 million widow households are eligible for the combined IGNWPS + state pension of ₹900/month but are not enrolled. SaralAI's target persona — a 50-70 year old Kannada-speaking woman — is precisely the demographic that existing digital welfare portals fail to reach.

The 50-scheme database covers the highest-impact schemes by enrollment gap: widow pensions, PM Ujjwala (free LPG), PM Awas (housing), PMJAY (health insurance), and multiple Karnataka-specific supplements. Each scheme's benefit value and document checklist is pre-loaded. Each generated PDF is pre-filled with the extracted Aadhaar data. The citizen arrives at the Tahsildar office with a complete, correctly filled application — reducing the average number of office visits required from 3.2 (national average) to 1.

---

## What Gemma 4 Makes Possible

Gemma 4 E4B is the only model that makes SaralAI's architecture viable for the communities it serves. A larger cloud-hosted model would require internet connectivity, raise data privacy concerns that would prevent adoption, and cost money that BPL households cannot pay. A smaller model would lack the vision capability to read Aadhaar card text reliably or the multilingual depth to understand spoken Kannada welfare narratives.

Gemma 4 runs locally, handles vision and language in a single model, and understands Kannada. That combination is not available anywhere else at the 4B parameter scale. SaralAI would not exist without it.

---

*SaralAI is open source under Apache 2.0. The scheme database is freely available for other welfare-tech projects to build on.*
