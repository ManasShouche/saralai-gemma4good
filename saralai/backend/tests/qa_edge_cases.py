"""Agent 4: Edge Case & Security Testing."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.scheme_finder import find_schemes_by_profile, evaluate_predicate
from tools.scheme_details import get_scheme_details
from tools.office_finder import find_nearest_office
from tools.form_generator import generate_application_form
from ollama_client import mask_aadhaar, mask_aadhaar_in_dict, load_prompt
from routes.schemes import _compute_age

passed = 0
failed = 0

def ok(msg):
    global passed; passed += 1; print(f"  PASS: {msg}")

def fail(msg):
    global failed; failed += 1; print(f"  FAIL: {msg}")

print("=== Scheme Finder Edge Cases ===")
for label, kw in [
    ("age=0", dict(state="Karnataka", age=0, gender="F")),
    ("age=-5", dict(state="Karnataka", age=-5, gender="M")),
    ("age=150", dict(state="Karnataka", age=150, gender="F")),
    ("unknown state", dict(state="Nonexistent", age=30, gender="M")),
    ("gender=X", dict(state="Karnataka", age=30, gender="X")),
    ("empty state", dict(state="", age=30, gender="F")),
    ("SQL inject", dict(state="'; DROP TABLE schemes; --", age=30, gender="M")),
    ("all None opts", dict(state="Karnataka", age=45, gender="F")),
    ("bad category", dict(state="Karnataka", age=30, gender="M", categories_filter=["nope"])),
]:
    try:
        r = find_schemes_by_profile(**kw)
        ok(f"{label} -> {len(r)} results")
    except Exception as e:
        fail(f"{label} error: {e}")

print("\n=== Predicate Edge Cases ===")
r = evaluate_predicate({"field":"age","op":"between","value":"invalid"},{"age":30})
ok("between/str") if r is False else fail(f"between/str -> {r}")
r = evaluate_predicate({"field":"x","op":"in","value":"invalid"},{"x":"a"})
ok("in/str") if r is False else fail(f"in/str -> {r}")
r = evaluate_predicate({"field":"age","op":"BAD","value":30},{"age":30})
ok("unknown op") if r is None else fail(f"unknown op -> {r}")

print("\n=== Tool Function Tests ===")
r = get_scheme_details("igw_pension")
ok("details(igw_pension)") if "error" not in r else fail("details(igw_pension)")
r = get_scheme_details("nonexistent")
ok("details(missing) -> error") if "error" in r else fail("details(missing)")
r = get_scheme_details("")
ok("details('') -> error") if "error" in r else fail("details('')")
r = find_nearest_office("igw_pension","Tumkur","Karnataka")
ok("office(igw_pension)") if "error" not in r else fail("office(igw_pension)")
r = find_nearest_office("nonexistent","Tumkur","Karnataka")
ok("office(missing) -> error") if "error" in r else fail("office(missing)")

td = {"name":"Test","dob":"1990-01-01","gender":"M","state":"Karnataka"}
try:
    r = generate_application_form("igw_pension", td)
    fp = r.get("file_path","")
    if os.path.exists(fp):
        ok(f"gen_form -> {os.path.getsize(fp)} bytes")
        os.remove(fp)
    else: fail("gen_form no file")
except Exception as e: fail(f"gen_form: {e}")

try:
    r = generate_application_form("igw_pension", {})
    fp = r.get("file_path","")
    if os.path.exists(fp):
        ok("gen_form(empty)")
        os.remove(fp)
    else: fail("gen_form(empty) no file")
except Exception as e: fail(f"gen_form(empty): {e}")

try:
    r = generate_application_form("igw_pension", {"name":"<script>alert(1)</script>"})
    ok("XSS in name handled")
    fp = r.get("file_path","")
    if os.path.exists(fp): os.remove(fp)
except Exception as e: fail(f"XSS: {e}")

try:
    r = generate_application_form("../../etc/passwd", {"name":"Test"})
    fp = r.get("file_path","")
    fail(f"Path traversal NOT blocked -> {fp}")
    if os.path.exists(fp): os.remove(fp)
except Exception: ok("Path traversal blocked")

print("\n=== Aadhaar Masking ===")
assert mask_aadhaar("1234 5678 9012") == "XXXX XXXX 9012"; ok("standard mask")
assert mask_aadhaar("123456789012") == "XXXX XXXX 9012"; ok("no-space mask")
assert mask_aadhaar("Hello") == "Hello"; ok("non-aadhaar unchanged")
assert mask_aadhaar("") == ""; ok("empty string")
m = mask_aadhaar_in_dict({"aadhaar_number":"1234 5678 9012","name":"R","n":42,"v":None})
assert m["aadhaar_number"] == "XXXX XXXX 9012" and m["name"]=="R" and m["n"]==42
ok("dict masking")

print("\n=== Prompt Loading ===")
for pn in ["extract_aadhaar","extract_ration_card","transcribe","find_schemes_system","explain_scheme"]:
    try:
        p = load_prompt(pn); ok(f"prompt({pn}) {len(p)}ch") if len(p)>10 else fail(f"prompt({pn}) short")
    except: fail(f"prompt({pn}) missing")
try: load_prompt("nonexistent"); fail("nonexistent prompt no error")
except FileNotFoundError: ok("missing prompt raises error")

print("\n=== Age Computation ===")
ok("valid date") if _compute_age("2000-01-15") > 20 else fail("valid date")
ok("invalid date") if _compute_age("invalid") == 0 else fail("invalid date")
ok("None date") if _compute_age(None) == 0 else fail("None date")

print(f"\n{'='*60}")
print(f"TOTAL: {passed+failed} | PASSED: {passed} | FAILED: {failed}")
if failed: print(f"WARNING: {failed} tests FAILED")
else: print("ALL TESTS PASSED")
