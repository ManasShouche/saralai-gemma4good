"""Agent 3: Database Integrity Audit — checks scheme DB for data quality issues."""

import sqlite3
import os
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schemes.db")

def test_database_integrity():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    issues = []
    warnings = []

    # 1. Check for schemes with empty/null required fields
    c.execute("SELECT id, title_en FROM schemes WHERE title_en IS NULL OR title_en = ''")
    for r in c.fetchall():
        issues.append(f"MISSING title_en: {r[0]}")

    c.execute("SELECT id, title_en FROM schemes WHERE eligibility IS NULL OR eligibility = ''")
    for r in c.fetchall():
        issues.append(f"MISSING eligibility: {r[0]} ({r[1]})")

    c.execute("SELECT id, title_en FROM schemes WHERE benefit_en IS NULL OR benefit_en = ''")
    for r in c.fetchall():
        issues.append(f"MISSING benefit_en: {r[0]} ({r[1]})")

    c.execute("SELECT id, title_en FROM schemes WHERE documents IS NULL OR documents = ''")
    for r in c.fetchall():
        issues.append(f"MISSING documents: {r[0]} ({r[1]})")

    # 2. Check JSON validity of eligibility and documents fields
    c.execute("SELECT id, eligibility, documents FROM schemes")
    for r in c.fetchall():
        try:
            preds = json.loads(r[1])
            if not isinstance(preds, list):
                issues.append(f"ELIGIBILITY not a list: {r[0]}")
            elif len(preds) == 0:
                warnings.append(f"EMPTY eligibility predicates: {r[0]}")
        except json.JSONDecodeError:
            issues.append(f"INVALID JSON eligibility: {r[0]}")
        try:
            docs = json.loads(r[2])
            if not isinstance(docs, list):
                issues.append(f"DOCUMENTS not a list: {r[0]}")
        except json.JSONDecodeError:
            issues.append(f"INVALID JSON documents: {r[0]}")

    # 3. Check for scope/state consistency
    c.execute("SELECT id, scope, state FROM schemes WHERE scope = 'state' AND (state IS NULL OR state = '')")
    for r in c.fetchall():
        issues.append(f"STATE scope but no state value: {r[0]}")

    c.execute("SELECT id, scope, state FROM schemes WHERE scope = 'national' AND state IS NOT NULL AND state != ''")
    for r in c.fetchall():
        warnings.append(f"NATIONAL scope but has state='{r[2]}': {r[0]}")

    # 4. Check for duplicate IDs
    c.execute("SELECT id, COUNT(*) as cnt FROM schemes GROUP BY id HAVING cnt > 1")
    for r in c.fetchall():
        issues.append(f"DUPLICATE ID: {r[0]} ({r[1]} copies)")

    # 5. Check i18n coverage
    c.execute("SELECT COUNT(*) FROM schemes")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM schemes WHERE title_hi IS NULL OR title_hi = ''")
    hi_missing = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM schemes WHERE title_kn IS NULL OR title_kn = ''")
    kn_missing = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM schemes WHERE benefit_hi IS NULL OR benefit_hi = ''")
    bhi_missing = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM schemes WHERE benefit_kn IS NULL OR benefit_kn = ''")
    bkn_missing = c.fetchone()[0]

    if hi_missing > 0:
        warnings.append(f"Missing Hindi titles: {hi_missing}/{total}")
    if kn_missing > 0:
        warnings.append(f"Missing Kannada titles: {kn_missing}/{total}")
    if bhi_missing > 0:
        warnings.append(f"Missing Hindi benefits: {bhi_missing}/{total}")
    if bkn_missing > 0:
        warnings.append(f"Missing Kannada benefits: {bkn_missing}/{total}")

    # 6. Check eligibility predicate field consistency
    valid_fields = {"age", "gender", "state", "marital_status", "ration_category",
                    "occupation", "disability", "children_count", "education_level",
                    "disability_type", "disability_percentage", "has_lpg_connection",
                    "children_in_education", "income"}
    c.execute("SELECT id, eligibility FROM schemes")
    for r in c.fetchall():
        try:
            preds = json.loads(r[1])
            for pred in preds:
                field = pred.get("field")
                op = pred.get("op")
                if op in ("any_of", "all_of"):
                    # Check sub-predicates
                    for sub in pred.get("value", []):
                        sf = sub.get("field")
                        if sf and sf not in valid_fields:
                            warnings.append(f"Unknown predicate field '{sf}' in {r[0]}")
                elif field and field not in valid_fields:
                    warnings.append(f"Unknown predicate field '{field}' in {r[0]}")
        except json.JSONDecodeError:
            pass

    # 7. Check for missing application_url
    c.execute("SELECT id FROM schemes WHERE application_url IS NULL OR application_url = ''")
    missing_url = c.fetchall()
    if missing_url:
        warnings.append(f"Missing application_url for {len(missing_url)} schemes")

    conn.close()

    # Print results
    print(f"\n{'='*60}")
    print(f"DATABASE INTEGRITY AUDIT REPORT")
    print(f"{'='*60}")
    print(f"Total schemes: {total}")
    print(f"")

    if issues:
        print(f"❌ ERRORS ({len(issues)}):")
        for i in issues:
            print(f"  ❌ {i}")
    else:
        print(f"✅ No critical errors found")

    print(f"")
    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print(f"✅ No warnings")

    print(f"\n{'='*60}")
    
    assert len(issues) == 0, f"Database integrity check failed with {len(issues)} errors"

if __name__ == "__main__":
    test_database_integrity()
