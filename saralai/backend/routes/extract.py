"""
Document extraction route — POST /api/extract-doc

Accepts a document image and returns extracted fields via SSE stream.
"""

import asyncio
import io
import json
import time

from fastapi import APIRouter, File, Form, UploadFile
from PIL import Image, ImageFilter
from sse_starlette.sse import EventSourceResponse

from ollama_client import extract_fields


def crop_to_card(img: Image.Image) -> Image.Image:
    """
    Crop the image to just the document/card region.

    Strategy: find contiguous rows/columns where most pixels are bright
    (the white card against a dark phone background). Uses a two-pass
    approach to tighten the crop.
    """
    w, h = img.size
    gray = img.convert("L")
    pixels = gray.load()

    # Pass 1: find rows where >40% of pixels are bright (card area)
    threshold = 150
    min_ratio = 0.4

    row_bright = []
    for y in range(h):
        bright = sum(1 for x in range(w) if pixels[x, y] > threshold)
        row_bright.append(bright / w)

    # Find the longest contiguous run of bright rows
    best_top, best_bottom, best_len = 0, h, 0
    run_start = None
    for y, ratio in enumerate(row_bright):
        if ratio >= min_ratio:
            if run_start is None:
                run_start = y
        else:
            if run_start is not None:
                run_len = y - run_start
                if run_len > best_len:
                    best_top, best_bottom, best_len = run_start, y, run_len
                run_start = None
    # Handle run that extends to bottom
    if run_start is not None:
        run_len = h - run_start
        if run_len > best_len:
            best_top, best_bottom = run_start, h

    # Pass 2: within the found rows, find column bounds
    col_bright = []
    for x in range(w):
        bright = sum(
            1 for y in range(best_top, best_bottom)
            if pixels[x, y] > threshold
        )
        denom = best_bottom - best_top
        col_bright.append(bright / denom if denom > 0 else 0)

    left, right = 0, w
    for x, ratio in enumerate(col_bright):
        if ratio >= min_ratio:
            left = x
            break
    for x in range(w - 1, -1, -1):
        if col_bright[x] >= min_ratio:
            right = x + 1
            break

    # Validate the crop is reasonable (at least 15% of image)
    card_w = right - left
    card_h = best_bottom - best_top
    if card_h > h * 0.15 and card_w > w * 0.15:
        pad = 5
        crop_box = (
            max(0, left - pad),
            max(0, best_top - pad),
            min(w, right + pad),
            min(h, best_bottom + pad),
        )
        return img.crop(crop_box)

    # Fallback: center crop to 80%
    mx, my = int(w * 0.1), int(h * 0.1)
    return img.crop((mx, my, w - mx, h - my))


def prepare_image(image_bytes: bytes) -> bytes:
    """
    Prepare an image for model extraction:
    1. Crop to card region (removes phone UI)
    2. Resize to max 640px wide (smaller = faster inference)
    3. Re-encode as JPEG at 85% quality
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Crop to card region
    img = crop_to_card(img)

    # Resize to max 640px wide
    max_w = 640
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize(
            (max_w, int(img.height * ratio)),
            Image.Resampling.LANCZOS,
        )

    # Re-encode
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()

router = APIRouter()


@router.post("/extract-doc")
async def extract_document(
    image: UploadFile = File(...),
    doc_type: str = Form("aadhaar"),
):
    """
    Extract structured fields from a document image.

    Accepts: multipart form with image (JPEG/PNG) and doc_type.
    Returns: SSE stream of extracted fields.
    """
    raw_bytes = await image.read()

    # Validate image isn't black/empty
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        grayscale = img.convert("L")
        pixels = list(grayscale.getdata())
        mean_brightness = sum(pixels) / len(pixels) if pixels else 0
        if mean_brightness < 10:
            async def empty_image_error():
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "Image appears to be blank or too dark. "
                                   "Make sure the camera can see the document clearly."
                    }),
                }
            return EventSourceResponse(empty_image_error())
    except Exception:
        pass

    # Crop to card region + resize + re-encode (removes phone UI, reduces model load)
    try:
        image_bytes = prepare_image(raw_bytes)
    except Exception:
        image_bytes = raw_bytes  # If prep fails, send original

    async def event_generator():
        start_time = time.time()
        try:
            # Run blocking Ollama call in a thread so it doesn't block
            # other requests (e.g. retake while first is still processing)
            loop = asyncio.get_event_loop()
            fields = await loop.run_in_executor(
                None, extract_fields, image_bytes, doc_type
            )

            if "error" in fields:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": fields["error"]}),
                }
                return

            # Emit raw OCR text for judge/verification display
            raw_text = fields.pop("_raw_text", None)
            if raw_text:
                yield {
                    "event": "raw_text",
                    "data": json.dumps({"text": raw_text}),
                }

            # Stream each field as a separate SSE event.
            # The model returns a flat dict of field→value. Gemma 4 does not
            # produce per-field confidence scores in its JSON output, so we use
            # a fixed default of 0.9. If a future prompt revision causes the
            # model to return {"field": {"value": ..., "confidence": ...}} dicts,
            # the isinstance check below will pick that up automatically.
            field_count = 0
            for key, value in fields.items():
                if value is None:
                    continue

                # Support models that return {value, confidence} dicts per field.
                if isinstance(value, dict) and "value" in value:
                    confidence = float(value.get("confidence", 0.9))
                    value = value["value"]
                else:
                    confidence = 0.9

                yield {
                    "event": "field",
                    "data": json.dumps({
                        "key": key,
                        "value": value,
                        "confidence": confidence,
                    }),
                }
                field_count += 1

            elapsed = int((time.time() - start_time) * 1000)
            yield {
                "event": "done",
                "data": json.dumps({
                    "total_fields": field_count,
                    "elapsed_ms": elapsed,
                }),
            }

        except Exception as e:
            msg = str(e)
            if "more system memory" in msg or "out of memory" in msg.lower():
                msg = "Not enough RAM to run Gemma 4. Close other apps to free up memory and try again."
            elif "model" in msg.lower() and ("not found" in msg.lower() or "does not exist" in msg.lower()):
                msg = f"Ollama model not found. Run: ollama pull gemma4:e4b"
            elif "connection" in msg.lower() or "refused" in msg.lower():
                msg = "Cannot reach Ollama. Make sure it is running (ollama serve)."
            yield {
                "event": "error",
                "data": json.dumps({"message": msg}),
            }

    return EventSourceResponse(event_generator())
