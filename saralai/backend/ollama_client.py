"""
Ollama client wrapper for Gemma 4 interactions.

Provides two primary interfaces:
1. extract_fields() — Single-shot image→JSON extraction for documents
2. run_agentic_loop() — Multi-turn tool-calling loop for scheme matching

All model interactions go through this module to centralize
configuration, error handling, and privacy masking.

Backend selection:
  Set SARALAI_BACKEND=llamacpp to use llama-cpp-python directly for
  edge-optimized inference (fine-grained memory control, no Ollama daemon).
  Default is "ollama".
"""

import json
import os
import re
import time
from typing import Callable, Optional

import ollama
from faster_whisper import WhisperModel

from memory_config import get_ollama_options, get_preferred_model, log_config, IS_LOW_RAM

# ---------------------------------------------------------------------------
# Backend selection: Ollama (default) or llama-cpp-python (edge optimization)
# ---------------------------------------------------------------------------
BACKEND = os.getenv("SARALAI_BACKEND", "ollama")  # "ollama" or "llamacpp"

if BACKEND == "llamacpp":
    try:
        from llama_backend import (
            extract_fields_llamacpp,
            run_agentic_loop_llamacpp,
            is_available as _llamacpp_is_available,
        )
        _USE_LLAMACPP = _llamacpp_is_available()
        if _USE_LLAMACPP:
            print("[SaralAI] Using llama.cpp direct backend for edge optimization")
        else:
            print("[SaralAI] llama.cpp backend requested but model not configured, "
                  "falling back to Ollama")
    except ImportError:
        _USE_LLAMACPP = False
        print("[SaralAI] llama-cpp-python not installed, falling back to Ollama")
else:
    _USE_LLAMACPP = False

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Log system config at startup
log_config()


def _resolve_model() -> str:
    """Return the model to use, with RAM-aware fallback for low-memory devices."""
    configured = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
    try:
        available = [m.model for m in ollama.list().models]
        # On low-RAM devices, prefer e2b if available
        preferred = get_preferred_model(configured, available)
        if preferred in available:
            return preferred
        # Configured tag not found — try the canonical tag
        fallback = "gemma4:e4b"
        if fallback in available:
            print(f"[SaralAI] OLLAMA_MODEL={configured!r} not found; using {fallback!r}")
            return fallback
        # Return whatever is configured and let Ollama surface a clear error
        return configured
    except Exception:
        return configured

MODEL = _resolve_model()
print(f"[SaralAI] Using model: {MODEL}")

# Privacy: regex to find and mask Aadhaar numbers
AADHAAR_PATTERN = re.compile(r"\b(\d{4})\s*(\d{4})\s*(\d{4})\b")


def mask_aadhaar(text: str) -> str:
    """Mask Aadhaar numbers to show only last 4 digits."""
    def _replace(match):
        return f"XXXX XXXX {match.group(3)}"
    return AADHAAR_PATTERN.sub(_replace, text)


def mask_aadhaar_in_dict(data: dict) -> dict:
    """Recursively mask Aadhaar numbers in a dictionary."""
    masked = {}
    for key, value in data.items():
        if isinstance(value, str):
            if key == "aadhaar_number" or "aadhaar" in key.lower():
                masked[key] = mask_aadhaar(value)
            else:
                masked[key] = value
        elif isinstance(value, dict):
            masked[key] = mask_aadhaar_in_dict(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_aadhaar_in_dict(item) if isinstance(item, dict)
                else mask_aadhaar(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            masked[key] = value
    return masked


def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", f"{prompt_name}.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def extract_fields(image_bytes: bytes, doc_type: str) -> dict:
    """
    Extract structured fields from a document image using Gemma 4 vision.

    Args:
        image_bytes: Raw image bytes (JPEG/PNG)
        doc_type: One of 'aadhaar', 'ration_card', 'disability_cert', 'income_cert'

    Returns:
        Dictionary of extracted fields with values
    """
    if _USE_LLAMACPP:
        return extract_fields_llamacpp(image_bytes, doc_type)

    import base64
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Load the appropriate prompt template
    prompt_map = {
        "aadhaar": "extract_aadhaar",
        "ration_card": "extract_ration_card",
        "disability_cert": "extract_aadhaar",  # Reuse with modifications
        "income_cert": "extract_aadhaar",       # Reuse with modifications
    }
    prompt_template = prompt_map.get(doc_type, "extract_aadhaar")
    prompt = load_prompt(prompt_template)

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt, "images": [image_b64]}
        ],
        format="json",
        options=get_ollama_options({"temperature": 0.1}),
    )

    # Parse the JSON response (ollama>=0.4 returns objects, not dicts)
    raw_text = response.message.content
    try:
        fields = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown fences
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            fields = json.loads(json_match.group())
        else:
            fields = {"error": "Failed to parse extraction response"}

    # Privacy: always mask Aadhaar numbers
    fields = mask_aadhaar_in_dict(fields)

    # Attach raw model output for UI verification display (masked)
    fields["_raw_text"] = mask_aadhaar(raw_text)

    return fields


# Lazy-loaded Whisper model — initialized on first transcription call.
# Using "small" for a good balance of accuracy and speed on CPU.
_whisper_model: Optional[WhisperModel] = None


def get_whisper_model() -> WhisperModel:
    """Return a cached WhisperModel, creating it on first call.
    Uses 'tiny' on low-RAM devices to save ~400MB."""
    global _whisper_model
    if _whisper_model is None:
        size = "tiny" if IS_LOW_RAM else "small"
        print(f"[SaralAI] Loading Whisper model: {size}")
        _whisper_model = WhisperModel(size, device="cpu", compute_type="int8")
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, language: str = "auto") -> dict:
    """
    Transcribe audio using faster-whisper (local, offline, supports Hindi/Kannada).

    Gemma 4 does not accept audio via its images field; this function uses
    faster-whisper instead, which is already in requirements.txt and runs fully
    on-device without any network calls.

    Args:
        audio_bytes: Raw audio bytes (WebM/WAV/MP3)
        language: BCP-47 language code hint ('hi', 'kn', 'en') or 'auto' for
                  automatic detection.

    Returns:
        Dict with transcript, language_detected, confidence, duration_sec
    """
    import tempfile

    model = get_whisper_model()
    # Pass None to faster-whisper when the caller wants auto-detection.
    lang = None if language == "auto" else language

    # faster-whisper requires a file path, not raw bytes.
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        segments, info = model.transcribe(tmp_path, language=lang, beam_size=5)
        transcript = " ".join(seg.text for seg in segments).strip()
        return {
            "transcript": transcript,
            "language_detected": info.language,
            "confidence": round(float(info.language_probability), 2),
            "duration_sec": round(info.duration, 1),
        }
    finally:
        os.unlink(tmp_path)


def run_agentic_loop(
    messages: list,
    profile: dict,
    language: str,
    stream_callback: Callable,
    tools: list,
    tool_registry: dict,
    timeout: int = 60,
) -> None:
    """
    Multi-turn agentic loop: model proposes tool calls, we execute, feed results back.

    The stream_callback receives each thinking-token chunk and each scheme result.
    Format: stream_callback(event_type: str, data: any)
      - stream_callback("thinking", {"text": "..."})
      - stream_callback("scheme", {scheme_data})
      - stream_callback("done", {summary})

    Args:
        messages: Conversation history
        profile: User profile dict
        language: User's language ('hi', 'kn', 'en')
        stream_callback: Callback for streaming events to the client
        tools: List of tool schemas (OpenAI format)
        tool_registry: Dict mapping function names to callables
        timeout: Hard timeout in seconds (default 60)
    """
    if _USE_LLAMACPP:
        return run_agentic_loop_llamacpp(
            messages, profile, language, stream_callback,
            tools, tool_registry, timeout,
        )

    start_time = time.time()
    schemes_found = 0
    schemes_evaluated = 0

    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            stream_callback("done", {
                "schemes_matched": schemes_found,
                "schemes_evaluated": schemes_evaluated,
                "elapsed_ms": int(elapsed * 1000),
                "timed_out": True,
            })
            break

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
            stream=True,
            options=get_ollama_options({"temperature": 0.3}),
        )

        tool_calls = []
        assistant_content = ""

        for chunk in response:
            # Check timeout during streaming
            if time.time() - start_time > timeout:
                break

            msg = chunk.message

            # Stream thinking tokens
            if msg.content:
                assistant_content += msg.content
                stream_callback("thinking", {"text": msg.content})

            # Collect tool calls
            if msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

        # Append assistant message to history
        if assistant_content or tool_calls:
            assistant_msg = {"role": "assistant", "content": assistant_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

        if not tool_calls:
            # Model is done reasoning
            stream_callback("done", {
                "schemes_matched": schemes_found,
                "schemes_evaluated": schemes_evaluated,
                "elapsed_ms": int((time.time() - start_time) * 1000),
                "timed_out": False,
            })
            break

        # Execute tool calls
        for call in tool_calls:
            fn_name = call.function.name
            fn_args_raw = call.function.arguments

            # arguments is already a dict in ollama>=0.4; guard for str just in case
            if isinstance(fn_args_raw, str):
                fn_args = json.loads(fn_args_raw)
            else:
                fn_args = fn_args_raw or {}

            # Emit visible tool-call event so UI shows function invocations
            display = fn_name.replace("_", " ")
            arg_hint = ""
            if "scheme_id" in fn_args:
                arg_hint = f" → {fn_args['scheme_id']}"
            elif "district" in fn_args:
                arg_hint = f" → {fn_args['district']}"
            stream_callback("thinking", {"text": f"\n⟳ tool: {display}{arg_hint}\n"})

            call_id = getattr(call, "id", None) or f"call_{fn_name}"

            # Execute the tool
            if fn_name in tool_registry:
                fn = tool_registry[fn_name]
                result = fn(**fn_args)
                schemes_evaluated += 1

                # If it's a scheme result, surface to UI immediately
                if fn_name == "get_scheme_details":
                    stream_callback("scheme", result)
                    schemes_found += 1

                # Add tool result to message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            else:
                # Unknown tool — return error to model
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps({"error": f"Unknown tool: {fn_name}"}),
                })

        # Loop continues; model decides what to do next
