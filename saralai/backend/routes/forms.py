"""
Form generation route — POST /api/generate-form

Generates a pre-filled PDF application form and returns it as a download.
"""

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tools.form_generator import generate_application_form

router = APIRouter()


class GenerateFormRequest(BaseModel):
    """Request body for form generation."""
    scheme_id: str
    user_data: dict


@router.post("/generate-form")
async def generate_form(request: GenerateFormRequest):
    """
    Generate a pre-filled application form PDF.

    Returns the PDF file as a binary download.
    """
    result = generate_application_form(
        scheme_id=request.scheme_id,
        user_data=request.user_data,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    file_path = result["file_path"]
    filename = result["filename"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="PDF file not found after generation")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
