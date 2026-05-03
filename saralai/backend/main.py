"""
SaralAI Backend — FastAPI orchestrator for multimodal welfare scheme matching.

Serves as the bridge between the Next.js frontend and the Gemma 4 model
running on Ollama. Handles document extraction, audio transcription,
scheme matching, and PDF form generation.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.debug import router as debug_router
from routes.extract import router as extract_router
from routes.transcribe import router as transcribe_router
from routes.schemes import router as schemes_router
from routes.forms import router as forms_router
from routes.tts import router as tts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # Startup: verify Ollama connectivity
    print("[SaralAI] Backend starting up...")
    print(f"[SaralAI] Ollama host: {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")
    print(f"[SaralAI] Model: {os.getenv('OLLAMA_MODEL', 'gemma4:e4b')}")
    yield
    # Shutdown
    print("[SaralAI] Backend shutting down...")


app = FastAPI(
    title="SaralAI API",
    description="Multimodal welfare scheme matching agent powered by Gemma 4",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend on any LAN IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # cannot combine credentials=True with origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(debug_router, prefix="/api")
app.include_router(extract_router, prefix="/api")
app.include_router(transcribe_router, prefix="/api")
app.include_router(schemes_router, prefix="/api")
app.include_router(forms_router, prefix="/api")
app.include_router(tts_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "service": "saralai-backend",
        "model": os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
    }
