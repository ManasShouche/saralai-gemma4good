"""
Text-to-speech route — POST /api/tts

Accepts text and returns synthesized speech audio.
Falls back to browser-native TTS hint when no external TTS engine is available.
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


router = APIRouter()


class TTSRequest(BaseModel):
    """Request body for text-to-speech."""
    text: str
    language: str = "en"
    voice: str = "female"


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech audio.

    Since Gemma 4 does not natively produce audio output, this endpoint
    returns the text payload with a hint for the frontend to use the
    browser's Web Speech API (SpeechSynthesisUtterance).

    Future enhancement: integrate with a real TTS service (Google TTS,
    Azure Cognitive Services, or a local piper-tts instance).

    Returns:
        JSON with text, language code, and synthesis instructions.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    lang_map = {"hi": "hi-IN", "kn": "kn-IN", "en": "en-IN"}
    bcp47 = lang_map.get(request.language, "en-IN")

    return JSONResponse(content={
        "text": request.text.strip(),
        "language": request.language,
        "bcp47": bcp47,
        "voice": request.voice,
        "engine": "browser",
        "hint": "Use SpeechSynthesisUtterance with the bcp47 lang code",
    })
