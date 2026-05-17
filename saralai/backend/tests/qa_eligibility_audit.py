"""Agent 5: Eligibility Accuracy Audit — checks for over/under-matching."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.scheme_finder import find_schemes_by_profile

def test_eligibility_accuracy():
    issues = []
    print("=== Eligibility Accuracy Audit ===\n")

    # 1. Rukmini (52F widow AAY) - should match widow, women schemes; NOT disability-only
    r1 = find_schemes_by_profile(state="Karnataka",age=52,gender="F",marital_status="widow",ration_category="AAY")
    ids1 = [x["id"] for x in r1]
    full1 = [x for x in r1 if x["match_quality"]=="full"]
    part1 = [x for x in r1 if x["match_quality"]=="partial"]
    print(f"Rukmini (52F widow AAY): {len(r1)} matches ({len(full1)} full, {len(part1)} partial)")
    if "igw_pension" not in ids1:
        issues.append("Rukmini MISSING igw_pension (widow pension)")
    for x in r1:
        if "disability" in x["id"] and x["match_quality"]=="full" and not any("disability" in f for f in x.get("matched_fields",[])):
            issues.append(f"Rukmini FALSE POSITIVE: {x['id']} (disability scheme, she has none)")

    # 2. Suresh (45M disabled BPL married) - should match disability schemes
    r2 = find_schemes_by_profile(state="Karnataka",age=45,gender="M",marital_status="married",ration_category="BPL",disability=True)
    ids2 = [x["id"] for x in r2]
    full2 = [x for x in r2 if x["match_quality"]=="full"]
    part2 = [x for x in r2 if x["match_quality"]=="partial"]
    print(f"Suresh (45M disabled BPL): {len(r2)} matches ({len(full2)} full, {len(part2)} partial)")
    disab_matches = [x for x in r2 if "disab" in x["id"].lower()]
    print(f"  Disability-specific: {[x['id'] for x in disab_matches]}")

    # 3. Young APL male - should NOT match widow/senior schemes as full
    r3 = find_schemes_by_profile(state="Karnataka",age=25,gender="M",marital_status="single",ration_category="APL")
    ids3 = [x["id"] for x in r3]
    full3 = [x for x in r3 if x["match_quality"]=="full"]
    bad = [x["id"] for x in full3 if "widow" in x["id"] or "senior" in x["id"]]
    if bad:
        issues.append(f"25M APL single FULL match on: {bad}")
    print(f"Young male (25M APL single): {len(r3)} matches ({len(full3)} full)")

    # 4. Lakshmi (69F BPL married) - should match senior schemes
    r4 = find_schemes_by_profile(state="Karnataka",age=69,gender="F",marital_status="married",ration_category="BPL")
    ids4 = [x["id"] for x in r4]
    full4 = [x for x in r4 if x["match_quality"]=="full"]
    senior = [x for x in r4 if "senior" in x["id"].lower()]
    print(f"Lakshmi (69F BPL married): {len(r4)} matches ({len(full4)} full)")
    print(f"  Senior-specific: {[x['id'] for x in senior]}")

    # 5. Over-matching analysis - partial matches with many unknowns
    print("\n--- Over-matching Analysis ---")
    for name, results in [("Rukmini", r1), ("Suresh", r2), ("Young male", r3), ("Lakshmi", r4)]:
        heavy_partial = [x for x in results if x["match_quality"]=="partial" and len(x.get("unknown_fields",[]))>2]
        if heavy_partial:
            print(f"  {name}: {len(heavy_partial)} matches with 3+ unknown fields (likely over-matching)")
            for hp in heavy_partial[:3]:
                print(f"    {hp['id']}: unknown={hp.get('unknown_fields',[])} unmatched={hp.get('unmatched_fields',[])}")

    # 6. National vs state scope check
    print("\n--- Scope Analysis ---")
    r_other = find_schemes_by_profile(state="Tamil Nadu", age=40, gender="F", ration_category="BPL")
    ka_schemes = [x for x in r_other if x.get("scope")=="state"]
    if ka_schemes:
        issues.append(f"Tamil Nadu query returning Karnataka state schemes: {[x['id'] for x in ka_schemes]}")
    print(f"Tamil Nadu query: {len(r_other)} matches, {len(ka_schemes)} state-scoped")

    print(f"\n{'='*60}")
    print(f"ELIGIBILITY AUDIT REPORT")
    print(f"{'='*60}")
    if issues:
        print(f"ISSUES FOUND ({len(issues)}):")
        for i in issues:
            print(f"  !! {i}")
    else:
        print("No critical accuracy issues found")

    assert len(issues) == 0, f"Found {len(issues)} eligibility issues"

if __name__ == "__main__":
    test_eligibility_accuracy()
