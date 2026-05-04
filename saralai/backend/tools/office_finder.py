"""
Office finder tool — locates the nearest application office for a scheme.

Uses the office_template field from the scheme database and interpolates
the user's district and state information.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schemes.db")


def find_nearest_office(scheme_id: str, district: str, state: str, block: str = None) -> dict:
    """
    Find the application office for a scheme in the user's district.

    Args:
        scheme_id: The scheme identifier
        district: User's district
        state: User's state
        block: User's block/taluk (optional)

    Returns:
        Dict with office address and contact information
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT office_template, title_en FROM schemes WHERE id = ?",
        (scheme_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"Scheme '{scheme_id}' not found"}

    template = row["office_template"] or "District Office, {district}, {state}"

    # Interpolate the template with user's location
    office_address = template.format(
        district=district,
        state=state,
        block=block or district,  # Default block to district if not provided
    )

    return {
        "scheme_id": scheme_id,
        "scheme_title": row["title_en"],
        "office_address": office_address,
        "district": district,
        "state": state,
        "note": "Please verify office timings before visiting. Carry all required documents.",
    }
