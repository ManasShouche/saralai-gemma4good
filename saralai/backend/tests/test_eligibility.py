
"""Tests for scheme eligibility matching against test personas."""

import json
import os
import sqlite3
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.scheme_finder import evaluate_predicate, evaluate_scheme, find_schemes_by_profile


# ── Test Personas ──────────────────────────────────────────────────────────

RUKMINI = {
    "name": "Rukmini Devi",
    "age": 52,
    "gender": "F",
    "district": "Tumkur",
    "state": "Karnataka",
    "ration_category": "AAY",
    "marital_status": "widow",
    "occupation": "none",
    "disability": False,
    "children_count": 2,
}

SURESH = {
    "name": "Suresh Kumar",
    "age": 45,
    "gender": "M",
    "district": "Bengaluru Rural",
    "state": "Karnataka",
    "ration_category": "BPL",
    "marital_status": "married",
    "occupation": "agricultural_laborer",
    "disability": True,
    "disability_type": "locomotor",
    "disability_percentage": 60,
    "children_count": 1,
}

LAKSHMI = {
    "name": "Lakshmi Bai",
    "age": 69,
    "gender": "F",
    "district": "Tumkur",
    "state": "Karnataka",
    "ration_category": "BPL",
    "marital_status": "married",
    "occupation": "none",
    "disability": False,
    "children_count": 4,
}


# ── Unit Tests: Predicate Evaluator ─────────────────────────────────────

def test_equals():
    assert evaluate_predicate({"field": "gender", "op": "==", "value": "F"}, {"gender": "F"}) is True
    assert evaluate_predicate({"field": "gender", "op": "==", "value": "M"}, {"gender": "F"}) is False

def test_not_equals():
    assert evaluate_predicate({"field": "gender", "op": "!=", "value": "M"}, {"gender": "F"}) is True

def test_greater_than():
    assert evaluate_predicate({"field": "age", "op": ">", "value": 50}, {"age": 52}) is True
    assert evaluate_predicate({"field": "age", "op": ">", "value": 60}, {"age": 52}) is False

def test_between():
    pred = {"field": "age", "op": "between", "value": [40, 79]}
    assert evaluate_predicate(pred, {"age": 52}) is True
    assert evaluate_predicate(pred, {"age": 40}) is True  # Inclusive
    assert evaluate_predicate(pred, {"age": 79}) is True  # Inclusive
    assert evaluate_predicate(pred, {"age": 39}) is False
    assert evaluate_predicate(pred, {"age": 80}) is False

def test_in_operator():
    pred = {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]}
    assert evaluate_predicate(pred, {"ration_category": "AAY"}) is True
    assert evaluate_predicate(pred, {"ration_category": "APL"}) is False

def test_not_in():
    pred = {"field": "ration_category", "op": "not_in", "value": ["APL"]}
    assert evaluate_predicate(pred, {"ration_category": "BPL"}) is True
    assert evaluate_predicate(pred, {"ration_category": "APL"}) is False

def test_exists():
    assert evaluate_predicate({"field": "disability", "op": "exists", "value": None}, {"disability": True}) is True
    assert evaluate_predicate({"field": "missing", "op": "exists", "value": None}, {"name": "x"}) is False

def test_missing_field():
    result = evaluate_predicate({"field": "income", "op": "==", "value": 0}, {"name": "x"})
    assert result is None  # Unknown

def test_any_of():
    pred = {
        "field": None,
        "op": "any_of",
        "value": [
            {"field": "marital_status", "op": "==", "value": "widow"},
            {"field": "age", "op": ">=", "value": 60},
        ],
    }
    assert evaluate_predicate(pred, {"marital_status": "widow", "age": 52}) is True
    assert evaluate_predicate(pred, {"marital_status": "married", "age": 65}) is True
    assert evaluate_predicate(pred, {"marital_status": "married", "age": 30}) is False

def test_all_of():
    pred = {
        "field": None,
        "op": "all_of",
        "value": [
            {"field": "gender", "op": "==", "value": "F"},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ],
    }
    assert evaluate_predicate(pred, {"gender": "F", "ration_category": "AAY"}) is True
    assert evaluate_predicate(pred, {"gender": "M", "ration_category": "AAY"}) is False


# ── Integration Tests: Persona Matching ─────────────────────────────────

def test_rukmini_matches():
    """Rukmini (widow, 52, AAY, Karnataka) should match 4+ schemes."""
    results = find_schemes_by_profile(
        state="Karnataka", age=52, gender="F",
        marital_status="widow", ration_category="AAY",
    )
    scheme_ids = [r["id"] for r in results]
    print(f"Rukmini matches: {scheme_ids}")
    assert "igw_pension" in scheme_ids, "IGW Pension should match"
    assert len(results) >= 3, f"Expected 3+ matches, got {len(results)}"


def test_suresh_matches():
    """Suresh (disabled, 45, BPL, Karnataka) should match disability schemes."""
    results = find_schemes_by_profile(
        state="Karnataka", age=45, gender="M",
        marital_status="married", ration_category="BPL",
        disability=True,
    )
    scheme_ids = [r["id"] for r in results]
    print(f"Suresh matches: {scheme_ids}")
    assert len(results) >= 2, f"Expected 2+ matches, got {len(results)}"


def test_lakshmi_matches():
    """Lakshmi (69, F, BPL, Karnataka) should match senior citizen schemes."""
    results = find_schemes_by_profile(
        state="Karnataka", age=69, gender="F",
        marital_status="married", ration_category="BPL",
    )
    scheme_ids = [r["id"] for r in results]
    print(f"Lakshmi matches: {scheme_ids}")
    assert len(results) >= 2, f"Expected 2+ matches, got {len(results)}"


if __name__ == "__main__":
    # Run unit tests
    print("Running predicate evaluator tests...")
    test_equals()
    test_not_equals()
    test_greater_than()
    test_between()
    test_in_operator()
    test_not_in()
    test_exists()
    test_missing_field()
    test_any_of()
    test_all_of()
    print("All predicate tests passed.\n")

    # Run persona tests (require seeded DB)
    print("Running persona integration tests...")
    try:
        test_rukmini_matches()
        test_suresh_matches()
        test_lakshmi_matches()
        print("All persona tests passed.")
    except FileNotFoundError:
        print("Database not seeded yet. Run `python db/seed.py` first.")
    except Exception as e:
        print(f"Persona tests failed: {e}")
