"""
llama.cpp direct backend for edge-optimized inference.

Provides the same interface as ollama_client.py but uses llama-cpp-python
directly for fine-grained control over memory, quantization, and inference
on resource-constrained hardware (8GB RAM, mobile devices, Raspberry Pi).

Activated via: SARALAI_BACKEND=llamacpp

Why llama-cpp-python instead of Ollama?
---------------------------------------
Ollama is excellent for ease of use but abstracts away the parameters that
matter for edge optimization. With llama-cpp-python we can:

  1. Set exact n_ctx to match available RAM (not Ollama's 128K default)
  2. Control n_gpu_layers for hybrid CPU/GPU splits on limited VRAM
  3. Enable flash_attn, use_mmap, use_mlock for zero-copy memory mapping
  4. Tune n_batch for throughput vs. latency tradeoffs on weak hardware
  5. Log actual tokens/sec and peak memory for the hackathon writeup
  6. Run without the Ollama daemon — one fewer process on a Pi

This module is entirely optional. If llama-cpp-python is not installed,
the system falls back to the Ollama backend transparently.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import logging
from typing import Callable, Optional, Any

logger = logging.getLogger("saralai.llamacpp")

# ---------------------------------------------------------------------------
# Guard import — the package is optional
# ---------------------------------------------------------------------------
try:
    from llama_cpp import Llama, ChatCompletionRequestMessage
    LLAMACPP_AVAILABLE = True
except ImportError:
    LLAMACPP_AVAILABLE = False
    Llama = None  # type: ignore[assignment, misc]

# ---------------------------------------------------------------------------
# Import helpers — memory_config is safe to import at module level.
# ollama_client imports are deferred to function bodies to avoid a circular
# import (ollama_client conditionally imports from this module).
# ---------------------------------------------------------------------------
from memory_config import get_system_ram_gb, get_cpu_count, SYSTEM_RAM_GB, CPU_COUNT

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LLAMACPP_MODEL_PATH = os.getenv("LLAMACPP_MODEL_PATH", "")

# Privacy: regex to find and mask Aadhaar numbers (same as ollama_client)
AADHAAR_PATTERN = re.compile(r"\b(\d{4})\s*(\d{4})\s*(\d{4})\b")


# ---------------------------------------------------------------------------
# Adaptive model parameters based on system resources
# ---------------------------------------------------------------------------

def _get_model_params() -> dict:
    """
    Return llama-cpp-python constructor kwargs tuned to detected hardware.

    The three tiers correspond to:
      - LOW  (<=8GB):  Raspberry Pi 5, old laptops, budget phones via Termux.
                       CPU-only, minimal context, aggressive batching.
      - MED  (<=16GB): M2 Air, mid-range laptops with integrated GPU.
                       Auto GPU offload, moderate context window.
      - HIGH (>16GB):  M2 Pro/Max, desktop with discrete GPU.
                       Full GPU offload, large context for multi-turn agent.
    """
    ram = SYSTEM_RAM_GB
    cpus = CPU_COUNT

    if ram <= 8:
        # LOW tier: every MB counts
        return {
            "n_ctx": 1024,          # Minimal context — saves ~1.5GB vs 4096
            "n_gpu_layers": 0,      # CPU-only — no GPU memory spike
            "n_batch": 128,         # Small batches — lower peak memory during prompt eval
            "n_threads": min(cpus, 4),  # Cap threads to avoid contention on weak CPUs
            "use_mmap": True,       # Memory-map the GGUF — OS manages paging, no malloc
            "use_mlock": False,     # Don't pin in RAM — let OS swap if needed
            "flash_attn": True,     # O(n) memory attention instead of O(n^2)
            "verbose": False,       # Suppress llama.cpp's verbose stdout
        }
    elif ram <= 16:
        # MEDIUM tier: can afford GPU offload and moderate context
        return {
            "n_ctx": 2048,          # Comfortable for doc extraction + short agent loops
            "n_gpu_layers": -1,     # Auto: offload all layers that fit in VRAM
            "n_batch": 256,         # Balanced throughput/latency
            "n_threads": min(cpus, 8),
            "use_mmap": True,
            "use_mlock": False,
            "flash_attn": True,
            "verbose": False,
        }
    else:
        # HIGH tier: full power
        return {
            "n_ctx": 4096,          # Large context for multi-scheme agent reasoning
            "n_gpu_layers": -1,     # Full GPU offload
            "n_batch": 512,         # Maximum throughput
            "n_threads": min(cpus, 12),
            "use_mmap": True,
            "use_mlock": True,      # Pin in RAM — we have plenty, avoid page faults
            "flash_attn": True,
            "verbose": False,
        }


# ---------------------------------------------------------------------------
# Singleton model instance — loaded once, reused across requests
# ---------------------------------------------------------------------------

_model: Optional[Any] = None  # typed as Any to avoid issues when Llama is None


def _get_model() -> Any:
    """
    Lazily load and cache the Llama model.

    The model is loaded once on first call and reused for all subsequent
    requests. This avoids the 3-8 second cold-start on each inference call.
    """
    global _model

    if _model is not None:
        return _model

    if not LLAMACPP_AVAILABLE:
        raise RuntimeError(
            "llama-cpp-python is not installed. "
            "Install with: pip install llama-cpp-python>=0.3.0"
        )

    model_path = LLAMACPP_MODEL_PATH
    if not model_path:
        raise RuntimeError(
            "LLAMACPP_MODEL_PATH environment variable not set. "
            "Set it to the path of your Gemma 4 GGUF file, e.g.:\n"
            "  export LLAMACPP_MODEL_PATH=~/models/gemma-4-e4b-it-Q4_K_M.gguf"
        )

    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"Download a Gemma 4 GGUF from HuggingFace and set LLAMACPP_MODEL_PATH."
        )

    params = _get_model_params()
    tier = "LOW" if SYSTEM_RAM_GB <= 8 else "MEDIUM" if SYSTEM_RAM_GB <= 16 else "HIGH"

    logger.info(
        f"Loading model: {os.path.basename(model_path)} "
        f"[{tier} tier, {SYSTEM_RAM_GB:.0f}GB RAM, {CPU_COUNT} CPUs]"
    )
    logger.info(f"  n_ctx={params['n_ctx']}, n_gpu_layers={params['n_gpu_layers']}, "
                f"n_batch={params['n_batch']}, flash_attn={params['flash_attn']}")

    print(f"[SaralAI:llamacpp] Loading model: {os.path.basename(model_path)}")
    print(f"[SaralAI:llamacpp] Tier: {tier} | n_ctx={params['n_ctx']} | "
          f"n_gpu_layers={params['n_gpu_layers']} | n_batch={params['n_batch']}")

    load_start = time.perf_counter()

    _model = Llama(
        model_path=model_path,
        **params,
    )

    load_elapsed = time.perf_counter() - load_start
    print(f"[SaralAI:llamacpp] Model loaded in {load_elapsed:.1f}s")

    return _model


# ---------------------------------------------------------------------------
# Performance metrics helper
# ---------------------------------------------------------------------------

class _PerfMetrics:
    """Track and log inference performance metrics."""

    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = time.perf_counter()
        self.first_token_time: Optional[float] = None
        self.token_count = 0

    def mark_first_token(self):
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()

    def add_tokens(self, n: int = 1):
        self.token_count += n

    def log(self):
        elapsed = time.perf_counter() - self.start_time
        ttft = (
            (self.first_token_time - self.start_time)
            if self.first_token_time else None
        )
        tps = self.token_count / elapsed if elapsed > 0 else 0

        metrics_line = (
            f"[SaralAI:llamacpp] {self.operation}: "
            f"{self.token_count} tokens in {elapsed:.1f}s "
            f"({tps:.1f} tok/s)"
        )
        if ttft is not None:
            metrics_line += f" | TTFT={ttft:.2f}s"

        print(metrics_line)
        logger.info(metrics_line)

        return {
            "elapsed_sec": round(elapsed, 2),
            "tokens": self.token_count,
            "tokens_per_sec": round(tps, 1),
            "time_to_first_token_sec": round(ttft, 3) if ttft else None,
        }


# ---------------------------------------------------------------------------
# extract_fields_llamacpp — Document field extraction
# ---------------------------------------------------------------------------

def extract_fields_llamacpp(image_bytes: bytes, doc_type: str) -> dict:
    """
    Extract structured fields from a document image using Gemma 4 vision
    via llama-cpp-python.

    This is a drop-in replacement for ollama_client.extract_fields().
    For multimodal inference, we encode the image as base64 and pass it
    as an image_url content part (supported by llama-cpp-python's
    multimodal chat handler for vision-capable GGUFs).

    Args:
        image_bytes: Raw image bytes (JPEG/PNG)
        doc_type: One of 'aadhaar', 'ration_card', 'disability_cert', 'income_cert'

    Returns:
        Dictionary of extracted fields with values
    """
    # Deferred imports to avoid circular dependency with ollama_client
    from ollama_client import load_prompt, mask_aadhaar_in_dict, mask_aadhaar

    model = _get_model()
    metrics = _PerfMetrics(f"extract_fields({doc_type})")

    # Load the appropriate prompt
    prompt_map = {
        "aadhaar": "extract_aadhaar",
        "ration_card": "extract_ration_card",
        "disability_cert": "extract_aadhaar",
        "income_cert": "extract_aadhaar",
    }
    prompt_template = prompt_map.get(doc_type, "extract_aadhaar")
    prompt = load_prompt(prompt_template)

    # Encode image for multimodal input
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine MIME type from magic bytes
    mime = "image/jpeg"
    if image_bytes[:4] == b"\x89PNG":
        mime = "image/png"

    # Build message with image_url content part for multimodal models.
    # llama-cpp-python supports this format for vision-capable GGUFs
    # (e.g. Gemma 4 E4B multimodal quantized).
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{image_b64}",
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    # Use low temperature for deterministic extraction
    response = model.create_chat_completion(
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    raw_text = response["choices"][0]["message"]["content"] or ""

    metrics.add_tokens(response.get("usage", {}).get("completion_tokens", 0))
    metrics.log()

    # Parse JSON response
    try:
        fields = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown fences or partial output
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            try:
                fields = json.loads(json_match.group())
            except json.JSONDecodeError:
                fields = {"error": "Failed to parse extraction response"}
        else:
            fields = {"error": "Failed to parse extraction response"}

    # Privacy: always mask Aadhaar numbers
    fields = mask_aadhaar_in_dict(fields)
    fields["_raw_text"] = mask_aadhaar(raw_text)

    return fields


# ---------------------------------------------------------------------------
# run_agentic_loop_llamacpp — Multi-turn tool-calling agent loop
# ---------------------------------------------------------------------------

def run_agentic_loop_llamacpp(
    messages: list,
    profile: dict,
    language: str,
    stream_callback: Callable,
    tools: list,
    tool_registry: dict,
    timeout: int = 60,
) -> None:
    """
    Multi-turn agentic loop using llama-cpp-python with tool calling.

    Drop-in replacement for ollama_client.run_agentic_loop().
    Uses create_chat_completion with streaming and tool schemas.

    The loop:
      1. Send messages + tools to model
      2. Stream thinking tokens to the UI via stream_callback
      3. Collect tool calls from the response
      4. Execute tools, append results, loop back to step 1
      5. Stop when model produces no tool calls (done reasoning)

    Args:
        messages: Conversation history (OpenAI chat format)
        profile: User profile dict
        language: User's language ('hi', 'kn', 'en')
        stream_callback: Callback for streaming events
        tools: List of tool schemas (OpenAI function-calling format)
        tool_registry: Dict mapping function names to callables
        timeout: Hard timeout in seconds (default 60)
    """
    model = _get_model()
    metrics = _PerfMetrics("agentic_loop")

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
            metrics.log()
            break

        # Stream the response — llama-cpp-python returns a generator
        response_stream = model.create_chat_completion(
            messages=messages,
            tools=tools,
            temperature=0.3,
            max_tokens=2048,
            stream=True,
        )

        tool_calls_acc: dict[str, dict] = {}
        assistant_content = ""

        for chunk in response_stream:
            # Check timeout during streaming
            if time.time() - start_time > timeout:
                break

            delta = chunk["choices"][0].get("delta", {})

            # Stream content tokens (thinking output)
            if delta.get("content"):
                metrics.mark_first_token()
                metrics.add_tokens(1)
                token_text = delta["content"]
                assistant_content += token_text
                stream_callback("thinking", {"text": token_text})

            # Accumulate tool calls from streamed deltas.
            # llama-cpp-python streams tool_calls as incremental deltas
            # with an index field to identify which call is being built.
            if delta.get("tool_calls"):
                for tc_delta in delta["tool_calls"]:
                    idx = tc_delta.get("index", 0)
                    idx_key = str(idx)

                    if idx_key not in tool_calls_acc:
                        tool_calls_acc[idx_key] = {
                            "id": tc_delta.get("id", f"call_{idx}"),
                            "function": {
                                "name": "",
                                "arguments": "",
                            },
                        }

                    fn_delta = tc_delta.get("function", {})
                    if fn_delta.get("name"):
                        tool_calls_acc[idx_key]["function"]["name"] += fn_delta["name"]
                    if fn_delta.get("arguments"):
                        tool_calls_acc[idx_key]["function"]["arguments"] += fn_delta["arguments"]

        # Flatten accumulated tool calls
        tool_calls = list(tool_calls_acc.values())

        # Append assistant message to history
        if assistant_content or tool_calls:
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
            }
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

        if not tool_calls:
            # Model is done reasoning — no more tool calls
            perf = metrics.log()
            stream_callback("done", {
                "schemes_matched": schemes_found,
                "schemes_evaluated": schemes_evaluated,
                "elapsed_ms": int((time.time() - start_time) * 1000),
                "timed_out": False,
                "perf": perf,
            })
            break

        # Execute each tool call
        for call in tool_calls:
            fn_name = call["function"]["name"]
            fn_args_raw = call["function"]["arguments"]

            # Parse arguments
            if isinstance(fn_args_raw, str):
                try:
                    fn_args = json.loads(fn_args_raw)
                except json.JSONDecodeError:
                    fn_args = {}
            else:
                fn_args = fn_args_raw or {}

            # Emit visible tool-call event for UI
            display = fn_name.replace("_", " ")
            arg_hint = ""
            if "scheme_id" in fn_args:
                arg_hint = f" -> {fn_args['scheme_id']}"
            elif "district" in fn_args:
                arg_hint = f" -> {fn_args['district']}"
            stream_callback("thinking", {"text": f"\n> tool: {display}{arg_hint}\n"})

            call_id = call.get("id", f"call_{fn_name}")

            # Execute the tool
            if fn_name in tool_registry:
                fn = tool_registry[fn_name]
                result = fn(**fn_args)
                schemes_evaluated += 1

                # Surface scheme results to UI immediately
                if fn_name == "get_scheme_details":
                    stream_callback("scheme", result)
                    schemes_found += 1

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            else:
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps({"error": f"Unknown tool: {fn_name}"}),
                })

        # Loop continues — model decides what to do next


# ---------------------------------------------------------------------------
# Module-level availability check
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Check if the llama.cpp backend can be used."""
    if not LLAMACPP_AVAILABLE:
        return False
    if not LLAMACPP_MODEL_PATH:
        return False
    if not os.path.isfile(LLAMACPP_MODEL_PATH):
        return False
    return True


def get_backend_info() -> dict:
    """Return diagnostic info about the llama.cpp backend configuration."""
    params = _get_model_params()
    tier = "LOW" if SYSTEM_RAM_GB <= 8 else "MEDIUM" if SYSTEM_RAM_GB <= 16 else "HIGH"
    return {
        "available": LLAMACPP_AVAILABLE,
        "model_path": LLAMACPP_MODEL_PATH or "(not set)",
        "model_exists": bool(LLAMACPP_MODEL_PATH and os.path.isfile(LLAMACPP_MODEL_PATH)),
        "system_ram_gb": round(SYSTEM_RAM_GB, 1),
        "cpu_count": CPU_COUNT,
        "tier": tier,
        "params": params,
    }
