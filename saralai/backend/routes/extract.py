"""
Document extraction route — POST /api/extract-doc

Accepts a document image and returns extracted fields via SSE stream.
"""

import io
import json
import time

from fastapi import APIRouter, File, Form, UploadFile
from PIL import Image
from sse_starlette.sse import EventSourceResponse

from ollama_client import extract_fields

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
    image_bytes = await image.read()

    # Validate image isn't black/empty before sending to model
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Check if image is mostly black (mean pixel value < 10)
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
        pass  # If PIL can't open it, let the model try and fail with a better error

    async def event_generator():
        start_time = time.time()
        try:
            fields = extract_fields(image_bytes, doc_type)

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
