"""
Scheme details tool — retrieves full information about a specific scheme.
"""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schemes.db")


def get_scheme_details(scheme_id: str) -> dict:
    """
    Get full information about a specific scheme.

    Returns all scheme fields including parsed eligibility predicates
    and documents list.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schemes WHERE id = ?", (scheme_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"Scheme '{scheme_id}' not found"}

    # Parse JSON fields
    try:
        eligibility_predicates = json.loads(row["eligibility"])
    except (json.JSONDecodeError, TypeError):
        eligibility_predicates = []

    try:
        documents_required = json.loads(row["documents"])
    except (json.JSONDecodeError, TypeError):
        documents_required = []

    return {
        "id": row["id"],
        "title_en": row["title_en"],
        "title_hi": row["title_hi"],
        "title_kn": row["title_kn"],
        "ministry": row["ministry"],
        "scope": row["scope"],
        "state": row["state"],
        "category": row["category"],
        "eligibility_predicates": eligibility_predicates,
        "benefit_en": row["benefit_en"],
        "benefit_hi": row["benefit_hi"],
        "benefit_kn": row["benefit_kn"],
        "documents_required": documents_required,
        "application_url": row["application_url"],
        "office_template": row["office_template"],
    }
