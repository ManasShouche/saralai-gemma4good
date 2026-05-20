"""
Document extraction route — POST /api/extract-doc

Accepts a document image and returns extracted fields via SSE stream.
"""

import json
import time

from fastapi import APIRouter, File, Form, UploadFile
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
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())
