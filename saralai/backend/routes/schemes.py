"""
Scheme matching routes:
  - POST /api/find-schemes — agentic loop with SSE streaming
  - GET /api/scheme/{scheme_id} — single scheme details
"""

import asyncio
import json
import time
from datetime import date, datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ollama_client import load_prompt, run_agentic_loop
from tools import TOOLS, TOOL_REGISTRY
from tools.scheme_details import get_scheme_details

router = APIRouter()


class UserProfile(BaseModel):
    """User profile extracted from documents."""
    name: str = None
    dob: str = None
    gender: str = None
    district: str = None
    state: str = None
    ration_category: str = None
    marital_status: str = None
    occupation: str = None
    disability: bool = None
    disability_type: str = None
    disability_percentage: int = None
    children_count: int = None
    education_level: str = None
    has_lpg_connection: bool = None
    children_in_education: bool = None


class FindSchemesRequest(BaseModel):
    """Request body for scheme matching."""
    profile: UserProfile
    narrative: str = ""
    language: str = "en"


def _compute_age(dob_str: str) -> int:
    """Compute age from a date-of-birth string (YYYY-MM-DD)."""
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except (ValueError, TypeError):
        return 0


@router.post("/find-schemes")
async def find_schemes(request: FindSchemesRequest):
    """
    Match user profile against scheme database using agentic reasoning.

    Returns SSE stream with:
    - event: thinking — reasoning tokens from the model
    - event: scheme — confirmed scheme match
    - event: done — completion summary
    """
    profile_dict = request.profile.model_dump(exclude_none=True)

    # Compute age from DOB if not explicitly provided
    if "dob" in profile_dict and "age" not in profile_dict:
        profile_dict["age"] = _compute_age(profile_dict["dob"])

    # Build the system prompt with language substitution
    lang_names = {"hi": "Hindi", "kn": "Kannada", "en": "English"}
    system_prompt = load_prompt("find_schemes_system").replace(
        "{user_language}", lang_names.get(request.language, "English")
    )

    # Build initial messages
    user_message = (
        f"Here is the user's profile extracted from their documents:\n"
        f"{json.dumps(profile_dict, ensure_ascii=False, indent=2)}\n\n"
        f"Here is what the user said about their situation:\n"
        f"\"{request.narrative}\"\n\n"
        f"Please find all government schemes this person may qualify for. "
        f"Respond in {lang_names.get(request.language, 'English')}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def stream_callback(event_type: str, data):
            # Called from worker thread — schedule onto event loop thread-safely
            loop.call_soon_threadsafe(queue.put_nowait, (event_type, data))

        async def run_in_thread():
            try:
                await asyncio.to_thread(
                    run_agentic_loop,
                    messages=messages,
                    profile=profile_dict,
                    language=request.language,
                    stream_callback=stream_callback,
                    tools=TOOLS,
                    tool_registry=TOOL_REGISTRY,
                    timeout=60,
                )
            except Exception as e:
                loop.call_soon_threadsafe(
                    queue.put_nowait, ("error", {"message": str(e)})
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        asyncio.create_task(run_in_thread())

        while True:
            item = await queue.get()
            if item is None:
                break
            event_type, data = item
            yield {
                "event": event_type,
                "data": json.dumps(data, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


@router.get("/scheme/{scheme_id}")
async def scheme_detail(scheme_id: str):
    """Get full details for a single scheme."""
    result = get_scheme_details(scheme_id)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])
    return result
