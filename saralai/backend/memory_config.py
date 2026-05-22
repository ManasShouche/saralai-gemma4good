"""
System resource detection and Ollama memory optimization.

Detects available RAM and returns optimal Ollama options to prevent
out-of-memory hangs on constrained devices.

Key insight for Apple Silicon: unified memory means num_gpu=-1 (full Metal)
uses the SAME memory as num_gpu=0 (CPU-only) but is ~10x faster. Never
force CPU-only on Apple Silicon — it wastes time without saving memory.
"""

import os
import platform


def get_system_ram_gb() -> float:
    """Return total system RAM in GB."""
    try:
        if platform.system() == "Darwin":
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            return int(result.stdout.strip()) / (1024 ** 3)
        else:
            # Linux / generic — read from /proc/meminfo or os.sysconf
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return (pages * page_size) / (1024 ** 3)
    except Exception:
        return 16.0  # Assume 16GB if detection fails


def get_cpu_count() -> int:
    """Return usable CPU core count."""
    try:
        return os.cpu_count() or 4
    except Exception:
        return 4


# Cached at import time
SYSTEM_RAM_GB = get_system_ram_gb()
CPU_COUNT = get_cpu_count()
IS_APPLE_SILICON = platform.system() == "Darwin" and platform.machine() == "arm64"
IS_LOW_RAM = SYSTEM_RAM_GB <= 10


def get_ollama_options(base_options: dict | None = None) -> dict:
    """
    Return Ollama options dict merged with memory-optimal defaults.

    3-tier system:
      LOW  (≤10GB): e2b forced, 1024 ctx, CPU-only (unless Apple Silicon)
      MEDIUM (≤16GB): e4b with tight settings, 2048 ctx, full Metal on Apple Silicon
      HIGH (>16GB): e4b comfortable, 8192 ctx

    On Apple Silicon: always use full Metal (num_gpu=-1) because unified
    memory means GPU offload costs nothing extra but is ~10x faster.
    """
    opts = {}

    if SYSTEM_RAM_GB <= 10:
        opts = {
            "num_ctx": 1024,
            "num_gpu": -1 if IS_APPLE_SILICON else 0,
            "num_batch": 64,
            "num_thread": min(CPU_COUNT, 8),
        }
    elif SYSTEM_RAM_GB <= 16:
        opts = {
            "num_ctx": 2048,
            "num_gpu": -1 if IS_APPLE_SILICON else 0,
            "num_batch": 128,
        }
    else:
        opts = {"num_ctx": 8192}

    # Merge caller's options on top (caller wins for explicit overrides)
    if base_options:
        opts.update(base_options)

    return opts


def get_preferred_model(configured: str, available: list[str]) -> str:
    """
    Select the best model for available RAM.

    ≤10GB: always e2b (e4b at 9.6GB won't fit)
    ≤16GB: try e4b first (fits at ~10.5GB with tight options), keep it
    >16GB: e4b with comfortable headroom
    """
    if SYSTEM_RAM_GB <= 10 and "e4b" in configured:
        e2b_tag = configured.replace("e4b", "e2b")
        if e2b_tag in available:
            print(f"[SaralAI] {SYSTEM_RAM_GB:.0f}GB RAM — switching to {e2b_tag} (e4b won't fit)")
            return e2b_tag

    # On 16GB, e4b fits with tight settings — don't downgrade
    return configured


def log_config():
    """Print detected system config at startup."""
    tier = "LOW" if SYSTEM_RAM_GB <= 10 else "MEDIUM" if SYSTEM_RAM_GB <= 16 else "HIGH"
    gpu_mode = "Metal (unified memory)" if IS_APPLE_SILICON else "CPU-only" if SYSTEM_RAM_GB <= 16 else "GPU"
    print(f"[SaralAI] System: {SYSTEM_RAM_GB:.1f}GB RAM, {CPU_COUNT} CPUs → {tier} tier")
    if IS_APPLE_SILICON:
        print(f"[SaralAI] Apple Silicon detected — using full Metal GPU (unified memory)")
    opts = get_ollama_options()
    print(f"[SaralAI] Ollama options: {opts}")
