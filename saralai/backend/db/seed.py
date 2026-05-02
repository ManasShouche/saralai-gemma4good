"""
Database seeder for SaralAI scheme database.

Reads scheme data from the CSV seed file and populates the SQLite database.
Run this script once to initialize the database:
    python db/seed.py
"""

import csv
import json
import os
import sqlite3
import sys


# Paths
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "schemes.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
CSV_PATH = os.path.join(DB_DIR, "..", "..", "data", "schemes_seed.csv")


def create_database():
    """Create the database and apply schema."""
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def seed_from_csv(conn: sqlite3.Connection):
    """Read the CSV seed file and insert schemes into the database."""
    if not os.path.exists(CSV_PATH):
        print(f"[seed] CSV file not found at {CSV_PATH}")
        print("[seed] Falling back to built-in seed data...")
        seed_builtin(conn)
        return

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO schemes
                    (id, title_en, title_hi, title_kn, ministry, scope, state,
                     category, eligibility, benefit_en, benefit_hi, benefit_kn,
                     documents, application_url, office_template)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row["id"],
                        row["title_en"],
                        row.get("title_hi"),
                        row.get("title_kn"),
                        row.get("ministry"),
                        row["scope"],
                        row.get("state"),
                        row["category"],
                        row["eligibility"],
                        row["benefit_en"],
                        row.get("benefit_hi"),
                        row.get("benefit_kn"),
                        row["documents"],
                        row.get("application_url"),
                        row.get("office_template"),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"[seed] Error inserting {row.get('id', '?')}: {e}")

    conn.commit()
    print(f"[seed] Inserted {count} schemes from CSV.")


def seed_builtin(conn: sqlite3.Connection):
    """Seed with built-in scheme data when CSV is not available."""
    schemes = [
        {
            "id": "igw_pension",
            "title_en": "Indira Gandhi National Widow Pension Scheme",
            "title_hi": "इंदिरा गांधी राष्ट्रीय विधवा पेंशन योजना",
            "title_kn": "ಇಂದಿರಾ ಗಾಂಧಿ ರಾಷ್ಟ್ರೀಯ ವಿಧವಾ ಪಿಂಚಣಿ ಯೋಜನೆ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "widow",
            "eligibility": json.dumps([
                {"field": "marital_status", "op": "==", "value": "widow"},
                {"field": "age", "op": "between", "value": [40, 79]},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "Monthly pension of ₹300 (often topped up by state).",
            "benefit_hi": "₹300 मासिक पेंशन (राज्य द्वारा अतिरिक्त संभव)।",
            "benefit_kn": "ಮಾಸಿಕ ₹300 ಪಿಂಚಣಿ (ರಾಜ್ಯದಿಂದ ಹೆಚ್ಚುವರಿ ಸಂಭವ).",
            "documents": json.dumps(["aadhaar", "ration_card", "death_certificate", "bank_passbook"]),
            "application_url": "https://nsap.nic.in/",
            "office_template": "Block Development Office, {block}, {district}, {state}",
        },
        {
            "id": "pmuy",
            "title_en": "Pradhan Mantri Ujjwala Yojana",
            "title_hi": "प्रधानमंत्री उज्ज्वला योजना",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಉಜ್ವಲಾ ಯೋಜನೆ",
            "ministry": "Ministry of Petroleum & Natural Gas",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "gender", "op": "==", "value": "F"},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
                {"field": "has_lpg_connection", "op": "==", "value": False},
            ]),
            "benefit_en": "Free LPG connection + first refill + stove.",
            "benefit_hi": "मुफ्त LPG कनेक्शन + पहला रिफिल + चूल्हा।",
            "benefit_kn": "ಉಚಿತ LPG ಸಂಪರ್ಕ + ಮೊದಲ ರಿಫಿಲ್ + ಸ್ಟೌವ್.",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook"]),
            "application_url": "https://pmuy.gov.in/",
            "office_template": "Nearest LPG distributor, {district}",
        },
        {
            "id": "ignoaps",
            "title_en": "Indira Gandhi National Old Age Pension Scheme",
            "title_hi": "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना",
            "title_kn": "ಇಂದಿರಾ ಗಾಂಧಿ ರಾಷ್ಟ್ರೀಯ ವೃದ್ಧಾಪ್ಯ ಪಿಂಚಣಿ ಯೋಜನೆ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 60},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "Monthly pension of ₹200 (60-79 yrs) or ₹500 (80+ yrs).",
            "benefit_hi": "₹200 मासिक पेंशन (60-79 वर्ष) या ₹500 (80+ वर्ष)।",
            "benefit_kn": "ಮಾಸಿಕ ₹200 ಪಿಂಚಣಿ (60-79 ವರ್ಷ) ಅಥವಾ ₹500 (80+ ವರ್ಷ).",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook"]),
            "application_url": "https://nsap.nic.in/",
            "office_template": "Block Development Office, {block}, {district}, {state}",
        },
        {
            "id": "ig_disability_pension",
            "title_en": "Indira Gandhi National Disability Pension Scheme",
            "title_hi": "इंदिरा गांधी राष्ट्रीय विकलांगता पेंशन योजना",
            "title_kn": "ಇಂದಿರಾ ಗಾಂಧಿ ರಾಷ್ಟ್ರೀಯ ಅಂಗವಿಕಲ ಪಿಂಚಣಿ ಯೋಜನೆ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
                {"field": "disability_percentage", "op": ">=", "value": 40},
                {"field": "age", "op": "between", "value": [18, 79]},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "Monthly pension of ₹300.",
            "benefit_hi": "₹300 मासिक पेंशन।",
            "benefit_kn": "ಮಾಸಿಕ ₹300 ಪಿಂಚಣಿ.",
            "documents": json.dumps(["aadhaar", "ration_card", "disability_certificate", "bank_passbook"]),
            "application_url": "https://nsap.nic.in/",
            "office_template": "Block Development Office, {block}, {district}, {state}",
        },
        {
            "id": "pm_kisan",
            "title_en": "PM-KISAN Samman Nidhi",
            "title_hi": "पीएम-किसान सम्मान निधि",
            "title_kn": "ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ",
            "ministry": "Ministry of Agriculture",
            "scope": "national",
            "state": None,
            "category": "agriculture",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["farmer", "agricultural_laborer"]},
            ]),
            "benefit_en": "₹6,000 per year in three installments.",
            "benefit_hi": "तीन किश्तों में प्रति वर्ष ₹6,000।",
            "benefit_kn": "ವರ್ಷಕ್ಕೆ ₹6,000 ಮೂರು ಕಂತುಗಳಲ್ಲಿ.",
            "documents": json.dumps(["aadhaar", "bank_passbook"]),
            "application_url": "https://pmkisan.gov.in/",
            "office_template": "Agriculture Department, {district}, {state}",
        },
        {
            "id": "pm_vidya_lakshmi",
            "title_en": "PM Vidya Lakshmi Education Loan Portal",
            "title_hi": "पीएम विद्या लक्ष्मी शिक्षा ऋण पोर्टल",
            "title_kn": "ಪಿಎಂ ವಿದ್ಯಾ ಲಕ್ಷ್ಮಿ ಶಿಕ್ಷಣ ಸಾಲ ಪೋರ್ಟಲ್",
            "ministry": "Ministry of Education",
            "scope": "national",
            "state": None,
            "category": "education",
            "eligibility": json.dumps([
                {"field": "children_in_education", "op": "==", "value": True},
            ]),
            "benefit_en": "Education loans from multiple banks via single portal.",
            "benefit_hi": "एकल पोर्टल के माध्यम से कई बैंकों से शिक्षा ऋण।",
            "benefit_kn": "ಒಂದೇ ಪೋರ್ಟಲ್ ಮೂಲಕ ಹಲವು ಬ್ಯಾಂಕ್‌ಗಳಿಂದ ಶಿಕ್ಷಣ ಸಾಲ.",
            "documents": json.dumps(["aadhaar", "school_certificate", "bank_passbook"]),
            "application_url": "https://www.vidyalakshmi.co.in/",
            "office_template": "Nearest bank branch, {district}, {state}",
        },
        {
            "id": "pm_fasal_bima",
            "title_en": "Pradhan Mantri Fasal Bima Yojana",
            "title_hi": "प्रधानमंत्री फसल बीमा योजना",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬೀಮಾ ಯೋಜನೆ",
            "ministry": "Ministry of Agriculture",
            "scope": "national",
            "state": None,
            "category": "agriculture",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["farmer"]},
            ]),
            "benefit_en": "Crop insurance covering natural calamities, pests, diseases.",
            "benefit_hi": "प्राकृतिक आपदाओं, कीटों, रोगों से फसल बीमा।",
            "benefit_kn": "ನೈಸರ್ಗಿಕ ವಿಪತ್ತುಗಳು, ಕೀಟಗಳು, ರೋಗಗಳಿಂದ ಬೆಳೆ ವಿಮೆ.",
            "documents": json.dumps(["aadhaar", "bank_passbook"]),
            "application_url": "https://pmfby.gov.in/",
            "office_template": "Agriculture Department, {district}, {state}",
        },
        {
            "id": "ka_widow_pension",
            "title_en": "Karnataka Widow Pension (Sandhya Suraksha)",
            "title_hi": "कर्नाटक विधवा पेंशन (संध्या सुरक्षा)",
            "title_kn": "ಕರ್ನಾಟಕ ವಿಧವಾ ಪಿಂಚಣಿ (ಸಂಧ್ಯಾ ಸುರಕ್ಷಾ)",
            "ministry": "Department of Women and Child Development, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "widow",
            "eligibility": json.dumps([
                {"field": "marital_status", "op": "==", "value": "widow"},
                {"field": "state", "op": "==", "value": "Karnataka"},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "State top-up pension of ₹600/month for widows.",
            "benefit_hi": "विधवाओं के लिए ₹600/माह राज्य पेंशन।",
            "benefit_kn": "ವಿಧವೆಯರಿಗೆ ₹600/ತಿಂಗಳು ರಾಜ್ಯ ಪಿಂಚಣಿ.",
            "documents": json.dumps(["aadhaar", "ration_card", "death_certificate", "bank_passbook"]),
            "application_url": "https://ksp.karnataka.gov.in/",
            "office_template": "Taluk Social Welfare Office, {district}, Karnataka",
        },
        {
            "id": "ka_disability_pension",
            "title_en": "Karnataka Disability Pension",
            "title_hi": "कर्नाटक विकलांगता पेंशन",
            "title_kn": "ಕರ್ನಾಟಕ ಅಂಗವಿಕಲ ಪಿಂಚಣಿ",
            "ministry": "Department of Empowerment of Differently Abled, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
                {"field": "disability_percentage", "op": ">=", "value": 40},
                {"field": "state", "op": "==", "value": "Karnataka"},
            ]),
            "benefit_en": "Monthly pension of ₹600 for persons with disabilities.",
            "benefit_hi": "विकलांग व्यक्तियों के लिए ₹600 मासिक पेंशन।",
            "benefit_kn": "ಅಂಗವಿಕಲ ವ್ಯಕ್ತಿಗಳಿಗೆ ₹600 ಮಾಸಿಕ ಪಿಂಚಣಿ.",
            "documents": json.dumps(["aadhaar", "disability_certificate", "bank_passbook"]),
            "application_url": "https://ksp.karnataka.gov.in/",
            "office_template": "District Disability Welfare Office, {district}, Karnataka",
        },
        {
            "id": "ka_senior_pension",
            "title_en": "Karnataka Senior Citizen Pension",
            "title_hi": "कर्नाटक वरिष्ठ नागरिक पेंशन",
            "title_kn": "ಕರ್ನಾಟಕ ಹಿರಿಯ ನಾಗರಿಕ ಪಿಂಚಣಿ",
            "ministry": "Department of Social Welfare, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 65},
                {"field": "state", "op": "==", "value": "Karnataka"},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "Monthly pension of ₹600 for senior citizens.",
            "benefit_hi": "वरिष्ठ नागरिकों के लिए ₹600 मासिक पेंशन।",
            "benefit_kn": "ಹಿರಿಯ ನಾಗರಿಕರಿಗೆ ₹600 ಮಾಸಿಕ ಪಿಂಚಣಿ.",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook"]),
            "application_url": "https://ksp.karnataka.gov.in/",
            "office_template": "Taluk Social Welfare Office, {district}, Karnataka",
        },
        {
            "id": "annapurna",
            "title_en": "Annapurna Yojana",
            "title_hi": "अन्नपूर्णा योजना",
            "title_kn": "ಅನ್ನಪೂರ್ಣ ಯೋಜನೆ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 65},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "10 kg of free food grain per month for destitute seniors.",
            "benefit_hi": "निराश्रित वृद्धों के लिए प्रति माह 10 किग्रा मुफ्त अनाज।",
            "benefit_kn": "ನಿರ್ಗತಿಕ ಹಿರಿಯರಿಗೆ ಪ್ರತಿ ತಿಂಗಳು 10 ಕೆಜಿ ಉಚಿತ ಆಹಾರ ಧಾನ್ಯ.",
            "documents": json.dumps(["aadhaar", "ration_card"]),
            "application_url": "https://nsap.nic.in/",
            "office_template": "Block Development Office, {block}, {district}, {state}",
        },
        {
            "id": "adip",
            "title_en": "ADIP Scheme (Assistive Devices)",
            "title_hi": "ADIP योजना (सहायक उपकरण)",
            "title_kn": "ADIP ಯೋಜನೆ (ಸಹಾಯಕ ಸಾಧನಗಳು)",
            "ministry": "Ministry of Social Justice",
            "scope": "national",
            "state": None,
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
                {"field": "disability_percentage", "op": ">=", "value": 40},
            ]),
            "benefit_en": "Free assistive devices (wheelchairs, crutches, hearing aids).",
            "benefit_hi": "मुफ्त सहायक उपकरण (व्हीलचेयर, बैसाखी, श्रवण यंत्र)।",
            "benefit_kn": "ಉಚಿತ ಸಹಾಯಕ ಸಾಧನಗಳು (ಗಾಲಿಕುರ್ಚಿ, ಊರುಗೋಲು, ಶ್ರವಣ ಸಾಧನ).",
            "documents": json.dumps(["aadhaar", "disability_certificate", "income_certificate"]),
            "application_url": "https://www.nhfdc.nic.in/",
            "office_template": "District Disability Rehabilitation Centre, {district}, {state}",
        },
    ]

    for scheme in schemes:
        try:
            conn.execute(
                """INSERT OR REPLACE INTO schemes
                (id, title_en, title_hi, title_kn, ministry, scope, state,
                 category, eligibility, benefit_en, benefit_hi, benefit_kn,
                 documents, application_url, office_template)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scheme["id"], scheme["title_en"], scheme["title_hi"],
                    scheme["title_kn"], scheme["ministry"], scheme["scope"],
                    scheme["state"], scheme["category"], scheme["eligibility"],
                    scheme["benefit_en"], scheme["benefit_hi"], scheme["benefit_kn"],
                    scheme["documents"], scheme["application_url"],
                    scheme["office_template"],
                ),
            )
        except Exception as e:
            print(f"[seed] Error inserting {scheme['id']}: {e}")

    conn.commit()
    print(f"[seed] Inserted {len(schemes)} built-in schemes.")


def verify_database(conn: sqlite3.Connection):
    """Run validation queries to verify the seeded data."""
    cursor = conn.cursor()

    # Total count
    cursor.execute("SELECT COUNT(*) FROM schemes")
    total = cursor.fetchone()[0]
    print(f"[verify] Total schemes: {total}")

    # Category distribution
    cursor.execute("SELECT category, COUNT(*) FROM schemes GROUP BY category ORDER BY category")
    print("[verify] By category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Scope distribution
    cursor.execute("SELECT scope, COUNT(*) FROM schemes GROUP BY scope")
    print("[verify] By scope:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Test Rukmini query
    print("\n[verify] Rukmini test (widow, 52, AAY, Karnataka):")
    cursor.execute("SELECT id, title_en FROM schemes")
    all_schemes = cursor.fetchall()
    matches = 0
    for scheme_id, title in all_schemes:
        cursor.execute("SELECT eligibility FROM schemes WHERE id = ?", (scheme_id,))
        elig_json = cursor.fetchone()[0]
        predicates = json.loads(elig_json)
        # Simple check — does this scheme potentially match Rukmini?
        might_match = True
        for pred in predicates:
            field = pred["field"]
            op = pred["op"]
            val = pred["value"]
            if field == "marital_status" and op == "==" and val != "widow":
                might_match = False
            if field == "gender" and op == "==" and val != "F":
                might_match = False
            if field == "disability" and op == "==" and val is True:
                might_match = False
            if field == "age" and op == ">=" and val > 52:
                might_match = False
        if might_match:
            print(f"  * {scheme_id}: {title}")
            matches += 1

    print(f"\n[verify] Rukmini matches: {matches} (target: 4+)")


if __name__ == "__main__":
    print(f"[seed] Creating database at {DB_PATH}")
    conn = create_database()
    seed_from_csv(conn)
    verify_database(conn)
    conn.close()
    print("[seed] Done.")
