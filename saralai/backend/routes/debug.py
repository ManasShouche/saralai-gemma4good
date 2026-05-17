"""
Debug logging endpoint — dev only.

Receives client-side errors (React hydration errors, unhandled rejections,
console.error calls) and prints them to the backend terminal so they're
visible alongside server logs.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/debug/log")
async def log_client_error(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {"raw": await request.body()}

    level = body.get("level", "error").upper()
    source = body.get("source", "client")
    message = body.get("message", "")
    stack = body.get("stack", "")
    url = body.get("url", "")
    ts = datetime.now().strftime("%H:%M:%S")

    print(f"\n[{ts}] [{source.upper()}] [{level}] {url}")
    print(f"  {message}")
    if stack:
        for line in stack.splitlines()[:8]:
            print(f"    {line}")
    print()

    return {"ok": True}
