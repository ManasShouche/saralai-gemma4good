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

        # ── WIDOW / WOMEN SCHEMES ──────────────────────────────────────────────

        {
            # Source: Ministry of Women & Child Development, National Mission for
            # Empowerment of Women. Official portal: wcd.nic.in/schemes-listing
            "id": "nmew_widow_support",
            "title_en": "National Mission for Empowerment of Women (Widow Support)",
            "title_hi": "महिला सशक्तिकरण राष्ट्रीय मिशन (विधवा सहायता)",
            "title_kn": "ಮಹಿಳಾ ಸಬಲೀಕರಣ ರಾಷ್ಟ್ರೀಯ ಮಿಶನ್ (ವಿಧವಾ ಬೆಂಬಲ)",
            "ministry": "Ministry of Women and Child Development",
            "scope": "national",
            "state": None,
            "category": "widow",
            "eligibility": json.dumps([
                {"field": "marital_status", "op": "==", "value": "widow"},
                {"field": "gender", "op": "==", "value": "F"},
            ]),
            "benefit_en": "Convergence of government services: legal aid, skill training, healthcare linkage, and social protection for widows.",
            "benefit_hi": "कानूनी सहायता, कौशल प्रशिक्षण, स्वास्थ्य सेवा और सामाजिक सुरक्षा का अभिसरण।",
            "benefit_kn": "ಕಾನೂನು ನೆರವು, ಕೌಶಲ ತರಬೇತಿ, ಆರೋಗ್ಯ ಸಂಪರ್ಕ ಮತ್ತು ಸಾಮಾಜಿಕ ರಕ್ಷಣೆ.",
            "documents": json.dumps(["aadhaar", "death_certificate", "ration_card"]),
            "application_url": "https://wcd.nic.in/schemes-listing",
            "office_template": "District Women and Child Development Officer, {district}, {state}",
        },
        {
            # Source: PM Matru Vandana Yojana — Ministry of WCD, pmmvy.nic.in
            "id": "pmmvy",
            "title_en": "Pradhan Mantri Matru Vandana Yojana",
            "title_hi": "प्रधानमंत्री मातृ वंदना योजना",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಮಾತೃ ವಂದನಾ ಯೋಜನೆ",
            "ministry": "Ministry of Women and Child Development",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "gender", "op": "==", "value": "F"},
                {"field": "is_pregnant_or_lactating", "op": "==", "value": True},
            ]),
            "benefit_en": "Cash incentive of ₹5,000 in three instalments for first live birth to promote maternal and child health.",
            "benefit_hi": "पहले जीवित प्रसव के लिए तीन किश्तों में ₹5,000 नकद प्रोत्साहन।",
            "benefit_kn": "ಮೊದಲ ಜೀವಂತ ಜನನಕ್ಕಾಗಿ ಮೂರು ಕಂತುಗಳಲ್ಲಿ ₹5,000 ನಗದು ಪ್ರೋತ್ಸಾಹ.",
            "documents": json.dumps(["aadhaar", "bank_passbook", "mother_child_protection_card"]),
            "application_url": "https://pmmvy.wcd.gov.in/",
            "office_template": "Anganwadi Centre / CDPO Office, {block}, {district}, {state}",
        },
        {
            # Source: Sukanya Samriddhi Yojana — Ministry of Finance / India Post
            # Eligibility: girl child below 10 years; parent/guardian opens account
            "id": "sukanya_samriddhi",
            "title_en": "Sukanya Samriddhi Yojana",
            "title_hi": "सुकन्या समृद्धि योजना",
            "title_kn": "ಸುಕನ್ಯಾ ಸಮೃದ್ಧಿ ಯೋಜನೆ",
            "ministry": "Ministry of Finance",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "has_girl_child_below_10", "op": "==", "value": True},
            ]),
            "benefit_en": "High-interest savings account (8.2% p.a.) for girl child education and marriage; minimum deposit ₹250/year.",
            "benefit_hi": "बालिका की शिक्षा और विवाह के लिए उच्च ब्याज बचत खाता (8.2% प्रतिवर्ष); न्यूनतम ₹250/वर्ष।",
            "benefit_kn": "ಹೆಣ್ಣು ಮಗಳ ಶಿಕ್ಷಣ ಮತ್ತು ವಿವಾಹಕ್ಕಾಗಿ ಹೆಚ್ಚಿನ ಬಡ್ಡಿ ಉಳಿತಾಯ ಖಾತೆ (8.2% ವಾರ್ಷಿಕ).",
            "documents": json.dumps(["aadhaar", "birth_certificate_of_girl", "photo"]),
            "application_url": "https://www.indiapost.gov.in/Financial/Pages/Content/Sukanya-Samriddhi-Account.aspx",
            "office_template": "Nearest Post Office or bank branch, {district}",
        },
        {
            # Source: Karnataka Stree Shakti programme — WCD Karnataka
            "id": "ka_stree_shakti",
            "title_en": "Karnataka Stree Shakti Self-Help Group Programme",
            "title_hi": "कर्नाटक स्त्री शक्ति स्वयं सहायता समूह",
            "title_kn": "ಕರ್ನಾಟಕ ಸ್ತ್ರೀ ಶಕ್ತಿ ಸ್ವ-ಸಹಾಯ ಗುಂಪು ಕಾರ್ಯಕ್ರಮ",
            "ministry": "Department of Women and Child Development, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "gender", "op": "==", "value": "F"},
                {"field": "state", "op": "==", "value": "Karnataka"},
            ]),
            "benefit_en": "Subsidised microfinance loans, training, and market linkages for women's self-help groups.",
            "benefit_hi": "महिला स्वयं सहायता समूहों के लिए सब्सिडीयुक्त माइक्रोफाइनेंस ऋण, प्रशिक्षण।",
            "benefit_kn": "ಮಹಿಳಾ ಸ್ವ-ಸಹಾಯ ಗುಂಪುಗಳಿಗೆ ಸಹಾಯದಾಯಿ ಸೂಕ್ಷ್ಮ ಹಣಕಾಸು ಸಾಲ ಮತ್ತು ತರಬೇತಿ.",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook", "photo"]),
            "application_url": "https://wcdkarnataka.gov.in/",
            "office_template": "Taluk Women and Child Development Office, {district}, Karnataka",
        },
        {
            # Source: Karnataka Bhagyalakshmi scheme — WCD Karnataka
            # Benefit: ₹1 lakh bond on birth of girl child in BPL family
            "id": "ka_bhagyalakshmi",
            "title_en": "Karnataka Bhagyalakshmi Scheme",
            "title_hi": "कर्नाटक भाग्यलक्ष्मी योजना",
            "title_kn": "ಕರ್ನಾಟಕ ಭಾಗ್ಯಲಕ್ಷ್ಮಿ ಯೋಜನೆ",
            "ministry": "Department of Women and Child Development, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "has_girl_child_below_10", "op": "==", "value": True},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
                {"field": "state", "op": "==", "value": "Karnataka"},
            ]),
            "benefit_en": "₹1 lakh bond (matures at 18 years) for girl child born in BPL family; ₹25,000 life insurance for mother.",
            "benefit_hi": "BPL परिवार में जन्मी बालिका के लिए ₹1 लाख बांड (18 वर्ष में परिपक्व); माँ के लिए ₹25,000 बीमा।",
            "benefit_kn": "BPL ಕುಟುಂಬದ ಹೆಣ್ಣು ಮಗಳಿಗೆ ₹1 ಲಕ್ಷ ಬಾಂಡ್ (18 ವರ್ಷಕ್ಕೆ ಮ್ಯಾಚ್ಯೂರ್); ತಾಯಿಗೆ ₹25,000 ವಿಮೆ.",
            "documents": json.dumps(["aadhaar", "ration_card", "birth_certificate_of_girl", "bank_passbook"]),
            "application_url": "https://wcdkarnataka.gov.in/",
            "office_template": "Anganwadi Centre / Taluk WCD Office, {district}, Karnataka",
        },

        # ── DISABILITY SCHEMES ────────────────────────────────────────────────

        {
            # Source: Deen Dayal Disabled Rehabilitation Scheme — Ministry of Social Justice
            "id": "dddrs",
            "title_en": "Deen Dayal Disabled Rehabilitation Scheme",
            "title_hi": "दीन दयाल विकलांग पुनर्वास योजना",
            "title_kn": "ದೀನ್ ದಯಾಳ್ ಅಂಗವಿಕಲ ಪುನರ್ವಸತಿ ಯೋಜನೆ",
            "ministry": "Ministry of Social Justice and Empowerment",
            "scope": "national",
            "state": None,
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
            ]),
            "benefit_en": "Grant-in-aid to NGOs running special schools, vocational training, and rehabilitation centres for persons with disabilities.",
            "benefit_hi": "विकलांग व्यक्तियों के लिए विशेष स्कूल, व्यावसायिक प्रशिक्षण चलाने वाले NGO को अनुदान।",
            "benefit_kn": "ಅಂಗವಿಕಲರಿಗೆ ವಿಶೇಷ ಶಾಲೆ, ವೃತ್ತಿ ತರಬೇತಿ ನಡೆಸುವ NGOಗಳಿಗೆ ಅನುದಾನ.",
            "documents": json.dumps(["aadhaar", "disability_certificate"]),
            "application_url": "https://disabilityaffairs.gov.in/content/page/dddrs.php",
            "office_template": "District Social Welfare Office, {district}, {state}",
        },
        {
            # Source: National Handicapped Finance and Development Corporation
            # Loan scheme for self-employment of persons with disability
            "id": "nhfdc_loan",
            "title_en": "NHFDC Loan for Self-Employment of Disabled Persons",
            "title_hi": "NHFDC विकलांग स्वरोजगार ऋण योजना",
            "title_kn": "NHFDC ಅಂಗವಿಕಲರ ಸ್ವ-ಉದ್ಯೋಗ ಸಾಲ ಯೋಜನೆ",
            "ministry": "Ministry of Social Justice and Empowerment",
            "scope": "national",
            "state": None,
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
                {"field": "disability_percentage", "op": ">=", "value": 40},
                {"field": "age", "op": "between", "value": [18, 55]},
            ]),
            "benefit_en": "Concessional loans up to ₹30 lakh at 5% interest for self-employment projects.",
            "benefit_hi": "स्वरोजगार परियोजनाओं के लिए 5% ब्याज पर ₹30 लाख तक रियायती ऋण।",
            "benefit_kn": "ಸ್ವ-ಉದ್ಯೋಗ ಯೋಜನೆಗಳಿಗೆ 5% ಬಡ್ಡಿಯಲ್ಲಿ ₹30 ಲಕ್ಷ ವರೆಗೆ ರಿಯಾಯಿತಿ ಸಾಲ.",
            "documents": json.dumps(["aadhaar", "disability_certificate", "income_certificate", "bank_passbook", "photo"]),
            "application_url": "https://www.nhfdc.nic.in/",
            "office_template": "State Channelising Agency / District Social Welfare Office, {district}, {state}",
        },
        {
            # Source: Unique Disability ID (UDID) — Ministry of Social Justice
            "id": "udid",
            "title_en": "Unique Disability ID (UDID) Card",
            "title_hi": "विशिष्ट विकलांगता पहचान (UDID) कार्ड",
            "title_kn": "ವಿಶೇಷ ಅಂಗವಿಕಲ ಗುರುತಿನ (UDID) ಕಾರ್ಡ್",
            "ministry": "Ministry of Social Justice and Empowerment",
            "scope": "national",
            "state": None,
            "category": "disability",
            "eligibility": json.dumps([
                {"field": "disability", "op": "==", "value": True},
                {"field": "disability_percentage", "op": ">=", "value": 40},
            ]),
            "benefit_en": "National digital disability identity card — gateway to all disability benefits, concessions, and reservations.",
            "benefit_hi": "राष्ट्रीय डिजिटल विकलांगता पहचान पत्र — सभी विकलांगता लाभों का प्रवेश द्वार।",
            "benefit_kn": "ರಾಷ್ಟ್ರೀಯ ಡಿಜಿಟಲ್ ಅಂಗವಿಕಲ ಗುರುತಿನ ಪತ್ರ — ಎಲ್ಲ ಅಂಗವಿಕಲ ಸೌಲಭ್ಯಗಳ ದ್ವಾರ.",
            "documents": json.dumps(["aadhaar", "photo", "medical_report"]),
            "application_url": "https://www.swavlambancard.gov.in/",
            "office_template": "Chief Medical Officer / Civil Surgeon, District Hospital, {district}, {state}",
        },

        # ── EDUCATION SCHEMES ─────────────────────────────────────────────────

        {
            # Source: National Scholarship Portal — scholarships.gov.in
            # Pre-Matric Scholarship for SC students — Ministry of Social Justice
            "id": "pre_matric_sc",
            "title_en": "Pre-Matric Scholarship for SC Students",
            "title_hi": "SC छात्रों के लिए प्री-मैट्रिक छात्रवृत्ति",
            "title_kn": "SC ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಪ್ರಿ-ಮೆಟ್ರಿಕ್ ವಿದ್ಯಾರ್ಥಿ ವೇತನ",
            "ministry": "Ministry of Social Justice and Empowerment",
            "scope": "national",
            "state": None,
            "category": "education",
            "eligibility": json.dumps([
                {"field": "caste_category", "op": "in", "value": ["SC", "ST"]},
                {"field": "children_in_education", "op": "==", "value": True},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "Annual scholarship of ₹150–₹750 + maintenance allowance for SC/ST students in Class 9 and 10.",
            "benefit_hi": "कक्षा 9-10 के SC/ST छात्रों के लिए ₹150–₹750 वार्षिक छात्रवृत्ति + रखरखाव भत्ता।",
            "benefit_kn": "9-10ನೇ ತರಗತಿಯ SC/ST ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ₹150–₹750 ವಾರ್ಷಿಕ ವಿದ್ಯಾರ್ಥಿ ವೇತನ.",
            "documents": json.dumps(["aadhaar", "caste_certificate", "school_certificate", "ration_card", "bank_passbook"]),
            "application_url": "https://scholarships.gov.in/",
            "office_template": "District Social Welfare Office / School Principal, {district}, {state}",
        },
        {
            # Source: Post-Matric Scholarship for SC — scholarships.gov.in
            "id": "post_matric_sc",
            "title_en": "Post-Matric Scholarship for SC Students",
            "title_hi": "SC छात्रों के लिए पोस्ट-मैट्रिक छात्रवृत्ति",
            "title_kn": "SC ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಪೋಸ್ಟ್-ಮೆಟ್ರಿಕ್ ವಿದ್ಯಾರ್ಥಿ ವೇತನ",
            "ministry": "Ministry of Social Justice and Empowerment",
            "scope": "national",
            "state": None,
            "category": "education",
            "eligibility": json.dumps([
                {"field": "caste_category", "op": "in", "value": ["SC", "ST"]},
                {"field": "children_in_education", "op": "==", "value": True},
                {"field": "annual_income", "op": "<=", "value": 250000},
            ]),
            "benefit_en": "Scholarship covering tuition fee + maintenance for SC students in Class 11 and above (up to PhD).",
            "benefit_hi": "Class 11 से PhD तक SC छात्रों के लिए ट्यूशन शुल्क + रखरखाव छात्रवृत्ति।",
            "benefit_kn": "11ನೇ ತರಗತಿಯಿಂದ PhD ವರೆಗೆ SC ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಶಿಕ್ಷಣ ಶುಲ್ಕ + ನಿರ್ವಹಣಾ ವಿದ್ಯಾರ್ಥಿ ವೇತನ.",
            "documents": json.dumps(["aadhaar", "caste_certificate", "school_certificate", "income_certificate", "bank_passbook"]),
            "application_url": "https://scholarships.gov.in/",
            "office_template": "District Social Welfare Office, {district}, {state}",
        },
        {
            # Source: NSP — National Merit cum Means Scholarship
            "id": "nmmss",
            "title_en": "National Means cum Merit Scholarship Scheme",
            "title_hi": "राष्ट्रीय साधन-सह-मेधा छात्रवृत्ति योजना",
            "title_kn": "ರಾಷ್ಟ್ರೀಯ ಆರ್ಥಿಕ-ಸಹ-ಮೆಧಾ ವಿದ್ಯಾರ್ಥಿ ವೇತನ ಯೋಜನೆ",
            "ministry": "Ministry of Education",
            "scope": "national",
            "state": None,
            "category": "education",
            "eligibility": json.dumps([
                {"field": "children_in_education", "op": "==", "value": True},
                {"field": "annual_income", "op": "<=", "value": 150000},
            ]),
            "benefit_en": "₹12,000/year (₹1,000/month) for meritorious students from Class 9 to 12 from low-income families.",
            "benefit_hi": "कम आय परिवारों के Class 9-12 के मेधावी छात्रों को ₹12,000/वर्ष।",
            "benefit_kn": "ಕಡಿಮೆ ಆದಾಯದ ಕುಟುಂಬಗಳ 9-12 ತರಗತಿ ಮೆಧಾವಿ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ₹12,000/ವರ್ಷ.",
            "documents": json.dumps(["aadhaar", "school_certificate", "income_certificate", "bank_passbook"]),
            "application_url": "https://scholarships.gov.in/",
            "office_template": "District Education Officer, {district}, {state}",
        },
        {
            # Source: Karnataka Rajiv Gandhi National Fellowship for SC/ST — UGC
            "id": "ka_hs_scholarship",
            "title_en": "Karnataka Higher Education Scholarship for SC/ST",
            "title_hi": "कर्नाटक SC/ST उच्च शिक्षा छात्रवृत्ति",
            "title_kn": "ಕರ್ನಾಟಕ SC/ST ಉನ್ನತ ಶಿಕ್ಷಣ ವಿದ್ಯಾರ್ಥಿ ವೇತನ",
            "ministry": "Department of Social Welfare, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "education",
            "eligibility": json.dumps([
                {"field": "caste_category", "op": "in", "value": ["SC", "ST"]},
                {"field": "children_in_education", "op": "==", "value": True},
                {"field": "state", "op": "==", "value": "Karnataka"},
            ]),
            "benefit_en": "Full fee waiver + ₹750–₹1,500/month maintenance for SC/ST students in degree and diploma courses in Karnataka.",
            "benefit_hi": "कर्नाटक में डिग्री/डिप्लोमा कोर्स में SC/ST छात्रों के लिए पूर्ण शुल्क छूट + ₹750–₹1,500/माह।",
            "benefit_kn": "ಕರ್ನಾಟಕದ ಪದವಿ/ಡಿಪ್ಲೊಮಾ ಕೋರ್ಸ್‌ಗಳಲ್ಲಿ SC/ST ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಸಂಪೂರ್ಣ ಶುಲ್ಕ ವಿನಾಯಿತಿ + ₹750–₹1,500/ತಿಂಗಳು.",
            "documents": json.dumps(["aadhaar", "caste_certificate", "school_certificate", "bank_passbook", "income_certificate"]),
            "application_url": "https://sw.kar.nic.in/",
            "office_template": "District Social Welfare Office, {district}, Karnataka",
        },

        # ── AGRICULTURE SCHEMES ───────────────────────────────────────────────

        {
            # Source: Kisan Credit Card — RBI / NABARD / Ministry of Agriculture
            "id": "kisan_credit_card",
            "title_en": "Kisan Credit Card Scheme",
            "title_hi": "किसान क्रेडिट कार्ड योजना",
            "title_kn": "ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ಯೋಜನೆ",
            "ministry": "Ministry of Agriculture and Farmers Welfare",
            "scope": "national",
            "state": None,
            "category": "agriculture",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["farmer", "agricultural_laborer"]},
                {"field": "age", "op": ">=", "value": 18},
            ]),
            "benefit_en": "Short-term crop loan up to ₹3 lakh at 4% interest (2% interest subvention for timely repayment).",
            "benefit_hi": "4% ब्याज पर ₹3 लाख तक अल्पकालिक फसल ऋण (समय पर चुकाने पर 2% ब्याज छूट)।",
            "benefit_kn": "4% ಬಡ್ಡಿಯಲ್ಲಿ ₹3 ಲಕ್ಷ ವರೆಗೆ ಅಲ್ಪಕಾಲಿಕ ಬೆಳೆ ಸಾಲ (ಸಮಯಕ್ಕೆ ತೀರಿಸಿದರೆ 2% ಬಡ್ಡಿ ರಿಯಾಯಿತಿ).",
            "documents": json.dumps(["aadhaar", "bank_passbook", "land_record"]),
            "application_url": "https://www.pmkisan.gov.in/kcc.aspx",
            "office_template": "Nearest bank branch / Primary Agriculture Cooperative Society, {district}",
        },
        {
            # Source: Soil Health Card — Ministry of Agriculture, soilhealth.dac.gov.in
            "id": "soil_health_card",
            "title_en": "Soil Health Card Scheme",
            "title_hi": "मृदा स्वास्थ्य कार्ड योजना",
            "title_kn": "ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಯೋಜನೆ",
            "ministry": "Ministry of Agriculture and Farmers Welfare",
            "scope": "national",
            "state": None,
            "category": "agriculture",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["farmer"]},
            ]),
            "benefit_en": "Free soil testing and a Soil Health Card with crop-wise fertiliser recommendations every 2 years.",
            "benefit_hi": "हर 2 साल में मुफ्त मिट्टी परीक्षण और फसलवार उर्वरक सिफारिशों सहित मृदा स्वास्थ्य कार्ड।",
            "benefit_kn": "ಪ್ರತಿ 2 ವರ್ಷಕ್ಕೊಮ್ಮೆ ಉಚಿತ ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮತ್ತು ಬೆಳೆವಾರು ಗೊಬ್ಬರ ಶಿಫಾರಸಿನ ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಕಾರ್ಡ್.",
            "documents": json.dumps(["aadhaar", "land_record"]),
            "application_url": "https://soilhealth.dac.gov.in/",
            "office_template": "Agriculture Department / Krishi Vigyan Kendra, {district}, {state}",
        },
        {
            # Source: Karnataka Raitha Siri / Krishi Bhagya — Agriculture Dept Karnataka
            "id": "ka_krishi_bhagya",
            "title_en": "Karnataka Krishi Bhagya Scheme",
            "title_hi": "कर्नाटक कृषि भाग्य योजना",
            "title_kn": "ಕರ್ನಾಟಕ ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆ",
            "ministry": "Department of Agriculture, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "agriculture",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["farmer"]},
                {"field": "state", "op": "==", "value": "Karnataka"},
                {"field": "land_holding_acres", "op": "<=", "value": 5},
            ]),
            "benefit_en": "Subsidy for farm pond construction (up to ₹1 lakh) + pump set + drip irrigation for small and marginal farmers.",
            "benefit_hi": "छोटे/सीमांत किसानों के लिए फार्म पॉन्ड निर्माण (₹1 लाख तक) + पम्प + ड्रिप सिंचाई सब्सिडी।",
            "benefit_kn": "ಸಣ್ಣ/ಅತಿ ಸಣ್ಣ ರೈತರಿಗೆ ಕೃಷಿ ಕೊಳ ನಿರ್ಮಾಣ (₹1 ಲಕ್ಷ ವರೆಗೆ) + ಪಂಪ್ ಸೆಟ್ + ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ.",
            "documents": json.dumps(["aadhaar", "bank_passbook", "land_record", "photo"]),
            "application_url": "https://raitamitra.karnataka.gov.in/",
            "office_template": "Taluk Agriculture Officer, {district}, Karnataka",
        },

        # ── SENIOR CITIZEN SCHEMES ────────────────────────────────────────────

        {
            # Source: Varishtha Pension Bima Yojana — LIC / Ministry of Finance
            "id": "vpby",
            "title_en": "Varishtha Pension Bima Yojana",
            "title_hi": "वरिष्ठ पेंशन बीमा योजना",
            "title_kn": "ವರಿಷ್ಠ ಪಿಂಚಣಿ ಬೀಮಾ ಯೋಜನೆ",
            "ministry": "Ministry of Finance / LIC of India",
            "scope": "national",
            "state": None,
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 60},
            ]),
            "benefit_en": "Guaranteed pension of 7.4% per annum on lump-sum deposit; minimum purchase price ₹1.56 lakh for ₹1,000/month pension.",
            "benefit_hi": "एकमुश्त जमा पर 7.4% प्रति वर्ष गारंटीशुदा पेंशन; ₹1,000/माह के लिए न्यूनतम ₹1.56 लाख।",
            "benefit_kn": "ಏಕ ಮೊತ್ತ ಠೇವಣಿಯಲ್ಲಿ 7.4% ವಾರ್ಷಿಕ ಖಾತ್ರಿ ಪಿಂಚಣಿ; ₹1,000/ತಿಂಗಳಿಗೆ ₹1.56 ಲಕ್ಷ ಕನಿಷ್ಟ ಖರೀದಿ.",
            "documents": json.dumps(["aadhaar", "pan", "bank_passbook", "photo"]),
            "application_url": "https://licindia.in/",
            "office_template": "Nearest LIC Branch Office, {district}",
        },
        {
            # Source: Indira Gandhi National Old Age Pension — 80+ tier
            # Already have ignoaps (60+); this is the 80+ enhanced tier (₹500/month central share)
            "id": "ignoaps_80plus",
            "title_en": "IGNOAPS Enhanced Pension for 80+ Seniors",
            "title_hi": "80+ वर्ष वृद्धों के लिए IGNOAPS वृद्धावस्था पेंशन",
            "title_kn": "80+ ವರ್ಷದ ಹಿರಿಯರಿಗೆ IGNOAPS ವರ್ಧಿತ ಪಿಂಚಣಿ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 80},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY"]},
            ]),
            "benefit_en": "₹500/month pension from central government (80+ BPL seniors); states typically add top-up.",
            "benefit_hi": "80+ वर्ष के BPL वृद्धों को केंद्र से ₹500/माह पेंशन; राज्य अतिरिक्त देते हैं।",
            "benefit_kn": "80+ ವರ್ಷದ BPL ಹಿರಿಯರಿಗೆ ಕೇಂದ್ರದಿಂದ ₹500/ತಿಂಗಳು ಪಿಂಚಣಿ; ರಾಜ್ಯ ಹೆಚ್ಚುವರಿ ನೀಡುತ್ತವೆ.",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook"]),
            "application_url": "https://nsap.nic.in/",
            "office_template": "Block Development Office, {block}, {district}, {state}",
        },
        {
            # Source: Karnataka Sandhya Suraksha Yojana (main senior pension)
            "id": "ka_sandhya_suraksha",
            "title_en": "Karnataka Sandhya Suraksha Yojana (Senior Citizen Pension)",
            "title_hi": "कर्नाटक संध्या सुरक्षा योजना (वरिष्ठ नागरिक पेंशन)",
            "title_kn": "ಕರ್ನಾಟಕ ಸಂಧ್ಯಾ ಸುರಕ್ಷಾ ಯೋಜನೆ (ಹಿರಿಯ ನಾಗರಿಕ ಪಿಂಚಣಿ)",
            "ministry": "Department of Social Welfare, Karnataka",
            "scope": "state",
            "state": "Karnataka",
            "category": "senior_citizen",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 65},
                {"field": "state", "op": "==", "value": "Karnataka"},
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY", "PHH"]},
            ]),
            "benefit_en": "₹1,000/month state pension (inclusive of NSAP central share) for BPL senior citizens in Karnataka.",
            "benefit_hi": "कर्नाटक में BPL वरिष्ठ नागरिकों को ₹1,000/माह राज्य पेंशन (NSAP केंद्रीय हिस्सा सहित)।",
            "benefit_kn": "ಕರ್ನಾಟಕದ BPL ಹಿರಿಯ ನಾಗರಿಕರಿಗೆ ₹1,000/ತಿಂಗಳು ರಾಜ್ಯ ಪಿಂಚಣಿ (NSAP ಕೇಂದ್ರ ಪಾಲು ಸೇರಿದಂತೆ).",
            "documents": json.dumps(["aadhaar", "ration_card", "bank_passbook"]),
            "application_url": "https://ksp.karnataka.gov.in/",
            "office_template": "Taluk Social Welfare Office, {district}, Karnataka",
        },

        # ── EMPLOYMENT SCHEMES ─────────────────────────────────────────────────

        {
            # Source: MGNREGS — Ministry of Rural Development, nrega.nic.in
            "id": "mgnregs",
            "title_en": "Mahatma Gandhi National Rural Employment Guarantee Scheme",
            "title_hi": "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी योजना",
            "title_kn": "ಮಹಾತ್ಮಾ ಗಾಂಧಿ ರಾಷ್ಟ್ರೀಯ ಗ್ರಾಮೀಣ ಉದ್ಯೋಗ ಖಾತ್ರಿ ಯೋಜನೆ",
            "ministry": "Ministry of Rural Development",
            "scope": "national",
            "state": None,
            "category": "employment",
            "eligibility": json.dumps([
                {"field": "age", "op": ">=", "value": 18},
                {"field": "occupation", "op": "in", "value": ["agricultural_laborer", "daily_laborer", "none", "farmer"]},
            ]),
            "benefit_en": "Guaranteed 100 days of unskilled wage employment per year at state minimum wage (₹200–₹350/day depending on state).",
            "benefit_hi": "राज्य न्यूनतम मजदूरी (₹200–₹350/दिन) पर प्रति वर्ष 100 दिन कुशलताहीन मजदूरी रोजगार की गारंटी।",
            "benefit_kn": "ರಾಜ್ಯ ಕನಿಷ್ಠ ವೇತನದಲ್ಲಿ (₹200–₹350/ದಿನ) ವರ್ಷಕ್ಕೆ 100 ದಿನ ಅಕೌಶಲ ವೇತನ ಉದ್ಯೋಗ ಖಾತ್ರಿ.",
            "documents": json.dumps(["aadhaar", "bank_passbook", "ration_card"]),
            "application_url": "https://nrega.nic.in/",
            "office_template": "Gram Panchayat Office, {block}, {district}, {state}",
        },
        {
            # Source: PM SVANidhi — Ministry of Housing & Urban Affairs
            "id": "pm_svanidhi",
            "title_en": "PM SVANidhi (Street Vendor Micro-Credit)",
            "title_hi": "पीएम स्वनिधि (स्ट्रीट वेंडर माइक्रो-क्रेडिट)",
            "title_kn": "ಪಿಎಂ ಸ್ವನಿಧಿ (ಬೀದಿ ವ್ಯಾಪಾರಿ ಸಾಲ)",
            "ministry": "Ministry of Housing and Urban Affairs",
            "scope": "national",
            "state": None,
            "category": "employment",
            "eligibility": json.dumps([
                {"field": "occupation", "op": "in", "value": ["street_vendor", "daily_laborer"]},
                {"field": "age", "op": ">=", "value": 18},
            ]),
            "benefit_en": "Collateral-free working capital loan: ₹10,000 (1st), ₹20,000 (2nd), ₹50,000 (3rd) for street vendors.",
            "benefit_hi": "सड़क विक्रेताओं के लिए बिना गारंटी कार्यशील पूंजी ऋण: ₹10,000 (पहली), ₹20,000 (दूसरी), ₹50,000 (तीसरी बार)।",
            "benefit_kn": "ಬೀದಿ ವ್ಯಾಪಾರಿಗಳಿಗೆ ಜಾಮೀನು ರಹಿತ ಸಾಲ: ₹10,000 (1ನೇ), ₹20,000 (2ನೇ), ₹50,000 (3ನೇ).",
            "documents": json.dumps(["aadhaar", "bank_passbook", "vendor_certificate_or_letter_of_recommendation"]),
            "application_url": "https://pmsvanidhi.mohua.gov.in/",
            "office_template": "Urban Local Body / Town Vending Committee, {district}",
        },

        # ── HEALTH / INSURANCE SCHEMES ─────────────────────────────────────────

        {
            # Source: PM Jan Arogya Yojana / Ayushman Bharat — NHA, pmjay.gov.in
            "id": "pmjay",
            "title_en": "Pradhan Mantri Jan Arogya Yojana (Ayushman Bharat)",
            "title_hi": "प्रधानमंत्री जन आरोग्य योजना (आयुष्मान भारत)",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಜನ ಆರೋಗ್ಯ ಯೋಜನೆ (ಆಯುಷ್ಮಾನ್ ಭಾರತ)",
            "ministry": "Ministry of Health and Family Welfare",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "ration_category", "op": "in", "value": ["BPL", "AAY", "PHH"]},
            ]),
            "benefit_en": "Health insurance cover of ₹5 lakh per family per year for secondary and tertiary hospitalisation at empanelled hospitals.",
            "benefit_hi": "सूचीबद्ध अस्पतालों में द्वितीयक/तृतीयक अस्पताल भर्ती के लिए प्रति परिवार ₹5 लाख वार्षिक स्वास्थ्य बीमा।",
            "benefit_kn": "ನೋಂದಾಯಿತ ಆಸ್ಪತ್ರೆಗಳಲ್ಲಿ ದ್ವಿತೀಯ/ತೃತೀಯ ಆಸ್ಪತ್ರೆ ದಾಖಲಾತಿಗೆ ಪ್ರತಿ ಕುಟುಂಬಕ್ಕೆ ₹5 ಲಕ್ಷ ವಾರ್ಷಿಕ ಆರೋಗ್ಯ ವಿಮೆ.",
            "documents": json.dumps(["aadhaar", "ration_card"]),
            "application_url": "https://pmjay.gov.in/",
            "office_template": "Nearest empanelled hospital / Common Service Centre, {district}, {state}",
        },
        {
            # Source: PM Jeevan Jyoti Bima Yojana — Ministry of Finance
            "id": "pmjjby",
            "title_en": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
            "title_hi": "प्रधानमंत्री जीवन ज्योति बीमा योजना",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಜೀವನ ಜ್ಯೋತಿ ಬೀಮಾ ಯೋಜನೆ",
            "ministry": "Ministry of Finance",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "age", "op": "between", "value": [18, 50]},
                {"field": "has_bank_account", "op": "==", "value": True},
            ]),
            "benefit_en": "Life insurance cover of ₹2 lakh for death due to any cause; annual premium ₹436 auto-debited from bank account.",
            "benefit_hi": "किसी भी कारण से मृत्यु पर ₹2 लाख जीवन बीमा; वार्षिक प्रीमियम ₹436 बैंक खाते से स्वतः काटा जाता है।",
            "benefit_kn": "ಯಾವುದೇ ಕಾರಣದ ಮರಣಕ್ಕೆ ₹2 ಲಕ್ಷ ಜೀವ ವಿಮೆ; ₹436 ವಾರ್ಷಿಕ ಪ್ರೀಮಿಯಂ ಬ್ಯಾಂಕ್ ಖಾತೆಯಿಂದ ಸ್ವಯಂ ಕಡಿತ.",
            "documents": json.dumps(["aadhaar", "bank_passbook"]),
            "application_url": "https://financialservices.gov.in/insurance-divisions/Government-Sponsored-Socially-Oriented-Insurance-Schemes/Pradhan-Mantri-Jeevan-Jyoti-Bima-Yojana%28PMJJBY%29",
            "office_template": "Nearest bank branch, {district}",
        },
        {
            # Source: PM Suraksha Bima Yojana — Ministry of Finance
            "id": "pmsby",
            "title_en": "Pradhan Mantri Suraksha Bima Yojana",
            "title_hi": "प्रधानमंत्री सुरक्षा बीमा योजना",
            "title_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಸುರಕ್ಷಾ ಬೀಮಾ ಯೋಜನೆ",
            "ministry": "Ministry of Finance",
            "scope": "national",
            "state": None,
            "category": "women_child",
            "eligibility": json.dumps([
                {"field": "age", "op": "between", "value": [18, 70]},
                {"field": "has_bank_account", "op": "==", "value": True},
            ]),
            "benefit_en": "Accidental death/disability cover of ₹2 lakh; annual premium only ₹20 auto-debited from bank account.",
            "benefit_hi": "आकस्मिक मृत्यु/विकलांगता के लिए ₹2 लाख बीमा; वार्षिक प्रीमियम केवल ₹20।",
            "benefit_kn": "ಆಕಸ್ಮಿಕ ಮರಣ/ಅಂಗವಿಕಲತೆಗೆ ₹2 ಲಕ್ಷ ವಿಮೆ; ₹20 ವಾರ್ಷಿಕ ಪ್ರೀಮಿಯಂ.",
            "documents": json.dumps(["aadhaar", "bank_passbook"]),
            "application_url": "https://financialservices.gov.in/insurance-divisions/Government-Sponsored-Socially-Oriented-Insurance-Schemes/Pradhan-Mantri-Suraksha-Bima-Yojana(PMSBY)",
            "office_template": "Nearest bank branch, {district}",
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
