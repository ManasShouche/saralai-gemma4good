"""
Audio transcription route — POST /api/transcribe

Accepts audio recording and returns transcription with language detection.
"""

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ollama_client import transcribe_audio

router = APIRouter()
    

@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str = Form("auto"),
):
    """
    Transcribe spoken audio to text.

    Accepts: multipart form with audio (WebM/WAV/MP3) and language hint.
    Returns: JSON with transcript, language_detected, confidence, duration_sec.
    """
    audio_bytes = await audio.read()

    try:
        result = transcribe_audio(audio_bytes, language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
