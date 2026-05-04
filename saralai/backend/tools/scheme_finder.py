"""
Scheme finder tool — evaluates eligibility predicates against a user profile.

Queries the SQLite database, iterates all schemes, and returns those whose
eligibility predicates match (fully or partially) the given profile.
"""

import json
import os
import sqlite3
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schemes.db")


def evaluate_predicate(predicate: dict, profile: dict) -> Optional[bool]:
    """
    Evaluate a single eligibility predicate against a user profile.

    Returns:
        True if predicate is satisfied
        False if predicate is not satisfied
        None if the required field is missing from profile (unknown)
    """
    field = predicate.get("field")
    op = predicate.get("op")
    value = predicate.get("value")

    # Check if the field exists in the profile (skip for compound ops)
    if op not in ("any_of", "all_of"):
        if field not in profile:
            if op == "exists":
                return False
            return None  # Unknown — field not provided
        profile_value = profile[field]
    else:
        profile_value = None

    if op == "exists":
        return profile_value is not None

    if op == "==":
        return profile_value == value

    if op == "!=":
        return profile_value != value

    if op == ">":
        return profile_value > value

    if op == "<":
        return profile_value < value

    if op == ">=":
        return profile_value >= value

    if op == "<=":
        return profile_value <= value

    if op == "between":
        if isinstance(value, list) and len(value) == 2:
            return value[0] <= profile_value <= value[1]
        return False

    if op == "in":
        if isinstance(value, list):
            return profile_value in value
        return False

    if op == "not_in":
        if isinstance(value, list):
            return profile_value not in value
        return True

    if op == "any_of":
        # OR over sub-predicates
        if isinstance(value, list):
            results = [evaluate_predicate(sub, profile) for sub in value]
            # True if any sub-predicate is True
            if any(r is True for r in results):
                return True
            # None if all are None or False
            if all(r is None for r in results):
                return None
            return False
        return False

    if op == "all_of":
        # AND over sub-predicates
        if isinstance(value, list):
            results = [evaluate_predicate(sub, profile) for sub in value]
            # False if any sub-predicate is False
            if any(r is False for r in results):
                return False
            # None if any is None (and none are False)
            if any(r is None for r in results):
                return None
            return True
        return False

    # Unknown operator
    return None


def evaluate_scheme(predicates: list, profile: dict) -> dict:
    """
    Evaluate all predicates for a scheme against a profile.

    Returns dict with:
        - match: 'full', 'partial', or 'none'
        - confidence_score: float 0.0–1.0 indicating match confidence
        - matched: list of matched predicate fields
        - unmatched: list of unmatched predicate fields
        - unknown: list of fields not in profile
    """
    matched = []
    unmatched = []
    unknown = []

    for pred in predicates:
        result = evaluate_predicate(pred, profile)
        field = pred.get("field", "unknown")
        if result is True:
            matched.append(field)
        elif result is False:
            unmatched.append(field)
        else:
            unknown.append(field)

    if not unmatched and not unknown:
        match_type = "full"
    elif not unmatched:
        match_type = "partial"  # All known predicates match, but some unknown
    elif len(matched) > 0 and len(unmatched) <= 1:
        match_type = "partial"  # Most predicates match
    else:
        match_type = "none"

    # Compute confidence score: matched fields count fully, unknown count as
    # half (benefit of doubt), unmatched count against.
    total = len(matched) + len(unmatched) + len(unknown)
    if total > 0:
        confidence_score = round(
            (len(matched) + 0.5 * len(unknown)) / total, 2
        )
    else:
        confidence_score = 0.0

    return {
        "match": match_type,
        "confidence_score": confidence_score,
        "matched": matched,
        "unmatched": unmatched,
        "unknown": unknown,
    }


def find_schemes_by_profile(
    state: str,
    age: int,
    gender: str,
    marital_status: str = None,
    ration_category: str = None,
    occupation: str = None,
    disability: bool = None,
    children_count: int = None,
    education_level: str = None,
    categories_filter: list = None,
    **kwargs,
) -> list:
    """
    Query the scheme database for schemes matching a user profile.

    Returns a list of scheme summaries (id, title, category, match quality).
    """
    # Build profile dict from arguments
    profile = {
        "state": state,
        "age": age,
        "gender": gender,
    }
    if marital_status is not None:
        profile["marital_status"] = marital_status
    if ration_category is not None:
        profile["ration_category"] = ration_category
    if occupation is not None:
        profile["occupation"] = occupation
    if disability is not None:
        profile["disability"] = disability
    if children_count is not None:
        profile["children_count"] = children_count
    if education_level is not None:
        profile["education_level"] = education_level

    # Query database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Filter by category if specified
    if categories_filter:
        placeholders = ",".join("?" for _ in categories_filter)
        query = f"""
            SELECT id, title_en, title_hi, title_kn, category, scope, state, eligibility
            FROM schemes
            WHERE category IN ({placeholders})
            AND (scope = 'national' OR state = ? OR state IS NULL)
        """
        cursor.execute(query, [*categories_filter, state])
    else:
        cursor.execute(
            """SELECT id, title_en, title_hi, title_kn, category, scope, state, eligibility
            FROM schemes
            WHERE scope = 'national' OR state = ? OR state IS NULL""",
            (state,),
        )

    results = []
    for row in cursor.fetchall():
        try:
            predicates = json.loads(row["eligibility"])
        except json.JSONDecodeError:
            continue

        eval_result = evaluate_scheme(predicates, profile)

        if eval_result["match"] in ("full", "partial"):
            results.append({
                "id": row["id"],
                "title_en": row["title_en"],
                "title_hi": row["title_hi"],
                "title_kn": row["title_kn"],
                "category": row["category"],
                "scope": row["scope"],
                "match_quality": eval_result["match"],
                "confidence_score": eval_result["confidence_score"],
                "matched_fields": eval_result["matched"],
                "unmatched_fields": eval_result["unmatched"],
                "unknown_fields": eval_result["unknown"],
            })

    conn.close()

    # Sort: full matches first, then by confidence descending
    results.sort(key=lambda x: (
        0 if x["match_quality"] == "full" else 1,
        -x["confidence_score"],
    ))

    return results
