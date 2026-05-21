"""
System resource detection and Ollama memory optimization.

Detects available RAM and returns optimal Ollama options to prevent
out-of-memory hangs on low-RAM devices (e.g. 8GB M2 Air).
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
IS_LOW_RAM = SYSTEM_RAM_GB <= 10


def get_ollama_options(base_options: dict | None = None) -> dict:
    """
    Return Ollama options dict merged with memory-optimal defaults.

    On low-RAM devices (<=10GB):
      - num_ctx=2048 (down from 128K default — saves 2-4GB)
      - num_gpu=0 (CPU-only to avoid GPU memory spike)
      - num_thread=CPU_COUNT

    On medium-RAM (<=16GB):
      - num_ctx=4096

    On high-RAM (>16GB):
      - num_ctx=8192 (comfortable headroom)
    """
    opts = {}

    if SYSTEM_RAM_GB <= 10:
        opts = {
            "num_ctx": 2048,
            "num_gpu": 0,
            "num_thread": min(CPU_COUNT, 8),
        }
    elif SYSTEM_RAM_GB <= 16:
        opts = {"num_ctx": 4096}
    else:
        opts = {"num_ctx": 8192}

    # Merge caller's options on top (caller wins for explicit overrides)
    if base_options:
        opts.update(base_options)

    return opts


def get_preferred_model(configured: str, available: list[str]) -> str:
    """
    On low-RAM devices, prefer e2b over e4b if available.
    The codebase still references gemma4:e4b for submission,
    but this silently falls back on constrained hardware.
    """
    if not IS_LOW_RAM:
        return configured

    # Try e2b variant if the configured model is e4b
    if "e4b" in configured:
        e2b_tag = configured.replace("e4b", "e2b")
        if e2b_tag in available:
            print(f"[SaralAI] Low RAM ({SYSTEM_RAM_GB:.0f}GB) — using {e2b_tag} instead of {configured}")
            return e2b_tag

    return configured


def log_config():
    """Print detected system config at startup."""
    tier = "LOW" if SYSTEM_RAM_GB <= 10 else "MEDIUM" if SYSTEM_RAM_GB <= 16 else "HIGH"
    print(f"[SaralAI] System: {SYSTEM_RAM_GB:.1f}GB RAM, {CPU_COUNT} CPUs → {tier} memory tier")
    if IS_LOW_RAM:
        print(f"[SaralAI] Memory optimization active: num_ctx=2048, CPU-only inference")
        print(f"[SaralAI] Tip: pull gemma4:e2b for best performance on this device")
