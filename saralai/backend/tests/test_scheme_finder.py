"""
Tests for find_schemes_by_profile() using an isolated in-memory SQLite DB.

No Ollama or live DB required. A temp DB is seeded inline via fixtures.

Run with:
    cd backend
    pytest tests/test_scheme_finder.py -v
"""

import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.scheme_finder import find_schemes_by_profile, evaluate_scheme


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schemes (
    id              TEXT PRIMARY KEY,
    title_en        TEXT NOT NULL,
    title_hi        TEXT,
    title_kn        TEXT,
    ministry        TEXT,
    scope           TEXT,
    state           TEXT,
    category        TEXT NOT NULL,
    eligibility     TEXT NOT NULL,
    benefit_en      TEXT NOT NULL,
    benefit_hi      TEXT,
    benefit_kn      TEXT,
    documents       TEXT NOT NULL,
    application_url TEXT,
    office_template TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

TEST_SCHEMES = [
    # Widow
    {
        "id": "igw_pension", "title_en": "Indira Gandhi National Widow Pension",
        "scope": "national", "state": None, "category": "widow",
        "eligibility": json.dumps([
            {"field": "marital_status", "op": "==", "value": "widow"},
            {"field": "age", "op": "between", "value": [40, 79]},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "₹300/month.", "documents": json.dumps(["aadhaar", "ration_card"]),
    },
    {
        "id": "ka_widow_pension", "title_en": "Karnataka Widow Pension",
        "scope": "state", "state": "Karnataka", "category": "widow",
        "eligibility": json.dumps([
            {"field": "marital_status", "op": "==", "value": "widow"},
            {"field": "state", "op": "==", "value": "Karnataka"},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "₹600/month.", "documents": json.dumps(["aadhaar", "ration_card"]),
    },
    # Senior citizen
    {
        "id": "ignoaps", "title_en": "Indira Gandhi National Old Age Pension",
        "scope": "national", "state": None, "category": "senior_citizen",
        "eligibility": json.dumps([
            {"field": "age", "op": ">=", "value": 60},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "₹200-500/month.", "documents": json.dumps(["aadhaar", "ration_card"]),
    },
    {
        "id": "ka_senior_pension", "title_en": "Karnataka Senior Citizen Pension",
        "scope": "state", "state": "Karnataka", "category": "senior_citizen",
        "eligibility": json.dumps([
            {"field": "age", "op": ">=", "value": 65},
            {"field": "state", "op": "==", "value": "Karnataka"},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "₹600/month.", "documents": json.dumps(["aadhaar", "ration_card"]),
    },
    {
        "id": "annapurna", "title_en": "Annapurna Yojana",
        "scope": "national", "state": None, "category": "senior_citizen",
        "eligibility": json.dumps([
            {"field": "age", "op": ">=", "value": 65},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "10 kg free food grain/month.", "documents": json.dumps(["aadhaar"]),
    },
    # Disability
    {
        "id": "ig_disability_pension", "title_en": "Indira Gandhi National Disability Pension",
        "scope": "national", "state": None, "category": "disability",
        "eligibility": json.dumps([
            {"field": "disability", "op": "==", "value": True},
            {"field": "disability_percentage", "op": ">=", "value": 40},
            {"field": "age", "op": "between", "value": [18, 79]},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]),
        "benefit_en": "₹300/month.", "documents": json.dumps(["aadhaar", "disability_certificate"]),
    },
    {
        "id": "ka_disability_pension", "title_en": "Karnataka Disability Pension",
        "scope": "state", "state": "Karnataka", "category": "disability",
        "eligibility": json.dumps([
            {"field": "disability", "op": "==", "value": True},
            {"field": "disability_percentage", "op": ">=", "value": 40},
            {"field": "state", "op": "==", "value": "Karnataka"},
        ]),
        "benefit_en": "₹600/month.", "documents": json.dumps(["aadhaar", "disability_certificate"]),
    },
    # LPG (has_lpg_connection field absent from most profiles → partial)
    {
        "id": "pmuy", "title_en": "Pradhan Mantri Ujjwala Yojana",
        "scope": "national", "state": None, "category": "women_child",
        "eligibility": json.dumps([
            {"field": "gender", "op": "==", "value": "F"},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            {"field": "has_lpg_connection", "op": "==", "value": False},
        ]),
        "benefit_en": "Free LPG connection.", "documents": json.dumps(["aadhaar", "ration_card"]),
    },
]


@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    db_path = str(tmp_path_factory.mktemp("sfdb") / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    for s in TEST_SCHEMES:
        conn.execute(
            "INSERT OR REPLACE INTO schemes "
            "(id, title_en, scope, state, category, eligibility, benefit_en, documents) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (s["id"], s["title_en"], s["scope"], s.get("state"),
             s["category"], s["eligibility"], s["benefit_en"], s["documents"]),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def patch_db(test_db_path, monkeypatch):
    import tools.scheme_finder as sf
    monkeypatch.setattr(sf, "DB_PATH", test_db_path)


# ---------------------------------------------------------------------------
# Rukmini (widow, 52, AAY, Karnataka)
# ---------------------------------------------------------------------------

class TestRukmini:

    def _results(self, **extra):
        return find_schemes_by_profile(
            state="Karnataka", age=52, gender="F",
            marital_status="widow", ration_category="AAY", **extra
        )

    def test_igw_pension_matched(self):
        ids = {r["id"] for r in self._results()}
        assert "igw_pension" in ids

    def test_ka_widow_pension_matched(self):
        ids = {r["id"] for r in self._results()}
        assert "ka_widow_pension" in ids

    def test_igw_pension_is_full_match(self):
        igw = next(r for r in self._results() if r["id"] == "igw_pension")
        assert igw["match_quality"] == "full"

    def test_ka_widow_pension_is_full_match(self):
        kaw = next(r for r in self._results() if r["id"] == "ka_widow_pension")
        assert kaw["match_quality"] == "full"

    def test_disability_schemes_excluded(self):
        ids = {r["id"] for r in self._results()}
        assert "ig_disability_pension" not in ids
        assert "ka_disability_pension" not in ids

    def test_senior_schemes_excluded_at_52(self):
        ids = {r["id"] for r in self._results()}
        assert "ignoaps" not in ids
        assert "ka_senior_pension" not in ids

    def test_pmuy_is_partial_missing_lpg_field(self):
        results = self._results()
        pmuy = next((r for r in results if r["id"] == "pmuy"), None)
        assert pmuy is not None, "pmuy should be a partial match (missing has_lpg_connection)"
        assert pmuy["match_quality"] == "partial"
        assert "has_lpg_connection" in pmuy["unknown_fields"]

    def test_apl_excludes_igw_pension(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=52, gender="F",
            marital_status="widow", ration_category="APL",
        )
        ids = {r["id"] for r in results}
        assert "igw_pension" not in ids


# ---------------------------------------------------------------------------
# Suresh (disability 60%, BPL, Karnataka, age 45)
# ---------------------------------------------------------------------------

class TestSuresh:

    def test_disability_predicate_full_match(self):
        """Directly test predicate evaluation for Suresh's profile."""
        predicates = [
            {"field": "disability", "op": "==", "value": True},
            {"field": "disability_percentage", "op": ">=", "value": 40},
            {"field": "age", "op": "between", "value": [18, 79]},
            {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
        ]
        profile = {
            "state": "Karnataka", "age": 45, "gender": "M",
            "ration_category": "BPL", "disability": True, "disability_percentage": 60,
        }
        result = evaluate_scheme(predicates, profile)
        assert result["match"] == "full"

    def test_widow_schemes_excluded(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=45, gender="M",
            marital_status="married", ration_category="BPL", disability=True,
        )
        ids = {r["id"] for r in results}
        assert "igw_pension" not in ids
        assert "ka_widow_pension" not in ids

    def test_no_disability_flag_excludes_disability_schemes(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=45, gender="M",
            marital_status="married", ration_category="BPL",
            # disability not passed
        )
        ids = {r["id"] for r in results}
        assert "ig_disability_pension" not in ids
        assert "ka_disability_pension" not in ids


# ---------------------------------------------------------------------------
# Lakshmi (69, married, BPL, Karnataka)
# ---------------------------------------------------------------------------

class TestLakshmi:

    def _results(self, age=69, **extra):
        return find_schemes_by_profile(
            state="Karnataka", age=age, gender="F",
            marital_status="married", ration_category="BPL", **extra
        )

    def test_ignoaps_matched(self):
        assert any(r["id"] == "ignoaps" for r in self._results())

    def test_ka_senior_pension_matched(self):
        assert any(r["id"] == "ka_senior_pension" for r in self._results())

    def test_annapurna_matched(self):
        assert any(r["id"] == "annapurna" for r in self._results())

    def test_widow_schemes_excluded(self):
        ids = {r["id"] for r in self._results()}
        assert "igw_pension" not in ids
        assert "ka_widow_pension" not in ids

    def test_age_59_misses_ignoaps(self):
        ids = {r["id"] for r in self._results(age=59)}
        assert "ignoaps" not in ids

    def test_age_60_hits_ignoaps(self):
        ids = {r["id"] for r in self._results(age=60)}
        assert "ignoaps" in ids

    def test_age_64_misses_ka_senior_pension(self):
        ids = {r["id"] for r in self._results(age=64)}
        assert "ka_senior_pension" not in ids

    def test_age_65_hits_ka_senior_pension(self):
        ids = {r["id"] for r in self._results(age=65)}
        assert "ka_senior_pension" in ids


# ---------------------------------------------------------------------------
# Partial match: missing field
# ---------------------------------------------------------------------------

class TestPartialMatch:

    def test_igw_partial_when_ration_category_missing(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=52, gender="F", marital_status="widow",
            # ration_category omitted
        )
        igw = next((r for r in results if r["id"] == "igw_pension"), None)
        assert igw is not None, "igw_pension should appear as partial match"
        assert igw["match_quality"] == "partial"
        assert "ration_category" in igw["unknown_fields"]

    def test_partial_has_no_unmatched_fields(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=52, gender="F", marital_status="widow",
        )
        igw = next(r for r in results if r["id"] == "igw_pension")
        assert igw["unmatched_fields"] == []


# ---------------------------------------------------------------------------
# Result ordering
# ---------------------------------------------------------------------------

class TestOrdering:

    def test_full_matches_before_partials(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=52, gender="F",
            marital_status="widow", ration_category="AAY",
        )
        seen_partial = False
        for r in results:
            if r["match_quality"] == "partial":
                seen_partial = True
            if seen_partial and r["match_quality"] == "full":
                pytest.fail("Full match appeared after partial match")


# ---------------------------------------------------------------------------
# State scoping
# ---------------------------------------------------------------------------

class TestStateScoping:

    def test_karnataka_scheme_excluded_for_other_state(self):
        results = find_schemes_by_profile(
            state="Maharashtra", age=52, gender="F",
            marital_status="widow", ration_category="AAY",
        )
        ids = {r["id"] for r in results}
        assert "ka_widow_pension" not in ids

    def test_national_scheme_included_for_any_state(self):
        results = find_schemes_by_profile(
            state="Maharashtra", age=52, gender="F",
            marital_status="widow", ration_category="AAY",
        )
        ids = {r["id"] for r in results}
        assert "igw_pension" in ids


# ---------------------------------------------------------------------------
# Category filter
# ---------------------------------------------------------------------------

class TestCategoryFilter:

    def test_widow_filter_excludes_disability(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=52, gender="F",
            marital_status="widow", ration_category="AAY",
            categories_filter=["widow"],
        )
        for r in results:
            assert r["category"] == "widow"

    def test_multiple_categories(self):
        results = find_schemes_by_profile(
            state="Karnataka", age=69, gender="F",
            marital_status="married", ration_category="BPL",
            categories_filter=["senior_citizen", "widow"],
        )
        for r in results:
            assert r["category"] in ("senior_citizen", "widow")
