
"""
Form generator tool — creates pre-filled PDF application forms.

Uses ReportLab to generate PDFs with user data overlaid at specified
coordinates. Missing fields are left as blank lines for hand-filling.
"""

import io
import json
import os
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "forms", "templates")
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "forms", "generated")


def load_template(scheme_id: str) -> Optional[dict]:
    """Load a form template JSON for the given scheme."""
    template_path = os.path.join(TEMPLATES_DIR, f"{scheme_id}.json")
    if not os.path.exists(template_path):
        return None
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_application_form(scheme_id: str, user_data: dict) -> dict:
    """
    Generate a pre-filled PDF application form.

    Args:
        scheme_id: The scheme to generate a form for
        user_data: Dict of user fields to pre-fill

    Returns:
        Dict with file_path to the generated PDF, or generates a
        simple form if no template exists
    """
    os.makedirs(GENERATED_DIR, exist_ok=True)

    template = load_template(scheme_id)
    import re
    raw_name = user_data.get("name", "applicant")
    user_name = re.sub(r"[^a-z0-9_-]", "", raw_name.replace(" ", "_").lower()) or "applicant"
    filename = f"{scheme_id}_{user_name}.pdf"
    output_path = os.path.join(GENERATED_DIR, filename)

    if template:
        _generate_from_template(template, user_data, output_path)
    else:
        _generate_simple_form(scheme_id, user_data, output_path)

    return {
        "file_path": output_path,
        "filename": filename,
        "scheme_id": scheme_id,
        "fields_filled": list(user_data.keys()),
    }


def _generate_from_template(template: dict, user_data: dict, output_path: str):
    """Generate PDF using field coordinates from a template."""
    c = pdf_canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30 * mm, height - 30 * mm, template.get("title", "Application Form"))

    # Fill fields at specified coordinates
    c.setFont("Helvetica", 11)
    for field_spec in template.get("fields", []):
        key = field_spec["key"]
        x = field_spec.get("x", 30 * mm)
        y = field_spec.get("y", height - 50 * mm)
        size = field_spec.get("size", 11)

        c.setFont("Helvetica", size)
        value = user_data.get(key, "")
        if value:
            c.drawString(x, y, str(value))
        else:
            # Draw underline for missing fields
            c.line(x, y - 2, x + 150, y - 2)

    c.save()


def _generate_simple_form(scheme_id: str, user_data: dict, output_path: str):
    """Generate a simple pre-filled form when no template exists."""
    c = pdf_canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30 * mm, height - 25 * mm, "Government Scheme Application Form")

    c.setFont("Helvetica", 12)
    c.drawString(30 * mm, height - 35 * mm, f"Scheme: {scheme_id}")
    c.drawString(30 * mm, height - 42 * mm, "=" * 60)

    # Applicant details section
    y_pos = height - 55 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y_pos, "Applicant Details")
    y_pos -= 10 * mm

    # Standard fields
    field_labels = [
        ("name", "Full Name"),
        ("dob", "Date of Birth"),
        ("gender", "Gender"),
        ("aadhaar_number", "Aadhaar Number"),
        ("address", "Address"),
        ("district", "District"),
        ("state", "State"),
        ("ration_category", "Ration Card Category"),
        ("marital_status", "Marital Status"),
        ("occupation", "Occupation"),
        ("bank_account", "Bank Account Number"),
        ("ifsc_code", "IFSC Code"),
    ]

    c.setFont("Helvetica", 11)
    for key, label in field_labels:
        value = user_data.get(key, "")
        c.drawString(30 * mm, y_pos, f"{label}: ")
        if value:
            c.drawString(80 * mm, y_pos, str(value))
        else:
            c.line(80 * mm, y_pos - 2, 180 * mm, y_pos - 2)
        y_pos -= 8 * mm

        # Page break if needed
        if y_pos < 30 * mm:
            c.showPage()
            y_pos = height - 25 * mm
            c.setFont("Helvetica", 11)

    # Signature section
    y_pos -= 15 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y_pos, "Declaration:")
    y_pos -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(
        30 * mm, y_pos,
        "I hereby declare that the information provided above is true to the best of my knowledge.",
    )
    y_pos -= 20 * mm
    c.drawString(30 * mm, y_pos, "Signature: ___________________")
    c.drawString(110 * mm, y_pos, f"Date: ___________________")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(30 * mm, 15 * mm, "Generated by SaralAI — Pre-filled for your convenience.")

    c.save()
