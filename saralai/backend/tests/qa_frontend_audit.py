"""Agent 6: Frontend Code Quality Audit — static analysis of TSX/TS files."""
import os, re, json

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

def test_frontend_code_quality():
    issues = []
    warnings = []
    
    def scan_file(path, rel):
        content = open(path, "r", encoding="utf-8", errors="replace").read()
        lines = content.split("\n")

        # Check for console.log left in (except DevLogger)
        if "DevLogger" not in rel:
            for i, line in enumerate(lines):
                if "console.log(" in line and "//" not in line.split("console.log")[0]:
                    warnings.append(f"{rel}:{i+1} console.log left in code")

        # Check for hardcoded localhost URLs
        for i, line in enumerate(lines):
            if "localhost" in line and "next.config" not in rel and "// " not in line.split("localhost")[0]:
                warnings.append(f"{rel}:{i+1} hardcoded localhost reference")

        # Check for missing error handling in fetch calls
        fetch_count = content.count("fetch(")
        catch_count = content.count(".catch(") + content.count("try {") + content.count("try{")
        if fetch_count > 0 and catch_count == 0 and "api.ts" not in rel:
            warnings.append(f"{rel} has {fetch_count} fetch calls but no catch/try blocks")

        # Check for unused imports (basic check)
        import_re = re.findall(r'import\s+\{([^}]+)\}\s+from', content)
        for imp_group in import_re:
            for imp in imp_group.split(","):
                imp = imp.strip().split(" as ")[-1].strip()
                if imp and len(imp) > 1 and "type " not in imp:
                    # Count usages after import block
                    usage_count = content.count(imp) - 1  # minus the import itself
                    if usage_count <= 0:
                        warnings.append(f"{rel} unused import: {imp}")

        # Check for TODO/FIXME/HACK comments
        for i, line in enumerate(lines):
            for marker in ["TODO", "FIXME", "HACK", "XXX"]:
                if marker in line and ("//" in line or "/*" in line or "#" in line):
                    warnings.append(f"{rel}:{i+1} {marker}: {line.strip()[:80]}")

        return len(lines)

    def scan_dir(dirpath, prefix=""):
        total_lines = 0
        file_count = 0
        for entry in sorted(os.listdir(dirpath)):
            full = os.path.join(dirpath, entry)
            rel = os.path.join(prefix, entry) if prefix else entry
            if entry.startswith(".") or entry == "node_modules" or entry == ".next":
                continue
            if os.path.isdir(full):
                l, c = scan_dir(full, rel)
                total_lines += l
                file_count += c
            elif entry.endswith((".tsx", ".ts", ".js", ".css")):
                total_lines += scan_file(full, rel)
                file_count += 1
        return total_lines, file_count

    print("=== Frontend Code Quality Audit ===\n")

    # Scan all frontend source files
    total_lines, file_count = scan_dir(FRONTEND)
    print(f"Scanned {file_count} files, {total_lines} total lines\n")

    # Check i18n completeness
    i18n_path = os.path.join(FRONTEND, "lib", "i18n.ts")
    if os.path.exists(i18n_path):
        content = open(i18n_path, "r", encoding="utf-8").read()
        # Count keys per language
        en_keys = len(re.findall(r'"[^"]+"\s*:', content.split("en:")[1].split("},")[0])) if "en:" in content else 0
        hi_keys = len(re.findall(r'"[^"]+"\s*:', content.split("hi:")[1].split("},")[0])) if "hi:" in content else 0
        kn_keys = len(re.findall(r'"[^"]+"\s*:', content.split("kn:")[1].split("},")[0])) if "kn:" in content else 0
        print(f"i18n keys: en={en_keys}, hi={hi_keys}, kn={kn_keys}")
        if en_keys != hi_keys:
            issues.append(f"i18n mismatch: en has {en_keys} keys, hi has {hi_keys}")
        if en_keys != kn_keys:
            issues.append(f"i18n mismatch: en has {en_keys} keys, kn has {kn_keys}")

    # Check package.json for missing scripts
    pkg_path = os.path.join(FRONTEND, "package.json")
    if os.path.exists(pkg_path):
        pkg = json.load(open(pkg_path))
        scripts = pkg.get("scripts", {})
        if "test" not in scripts:
            warnings.append("No 'test' script in package.json")
        if "lint" not in scripts:
            warnings.append("No 'lint' script in package.json")
        print(f"Scripts: {list(scripts.keys())}")

    # Check for missing pages per route mapping
    expected_dirs = ["onboarding", "scan", "speak", "results", "scheme"]
    app_dir = os.path.join(FRONTEND, "app")
    for d in expected_dirs:
        dp = os.path.join(app_dir, d)
        if not os.path.isdir(dp):
            issues.append(f"Missing route directory: app/{d}")
        else:
            has_page = any("page.tsx" in f for f in os.listdir(dp))
            if not has_page:
                # Check subdirs
                has_page = any(
                    os.path.exists(os.path.join(dp, sub, "page.tsx"))
                    for sub in os.listdir(dp) if os.path.isdir(os.path.join(dp, sub))
                )
            if not has_page:
                issues.append(f"Missing page.tsx in app/{d}/")

    # Check for missing components referenced in design
    expected_components = ["CameraView", "FieldChip", "GiantCTA", "HoldToTalk",
                           "LanguageToggle", "ListenFAB", "ReasoningStream",
                           "SchemeCard", "TrustStrip", "Waveform"]
    comp_dir = os.path.join(FRONTEND, "components")
    for comp in expected_components:
        if not os.path.exists(os.path.join(comp_dir, f"{comp}.tsx")):
            issues.append(f"Missing component: {comp}.tsx")

    print(f"\n{'='*60}")
    print(f"FRONTEND CODE QUALITY REPORT")
    print(f"{'='*60}")
    if issues:
        print(f"\nISSUES ({len(issues)}):")
        for i in issues:
            print(f"  !! {i}")
    else:
        print("\nNo critical issues found")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  -- {w}")
    else:
        print("\nNo warnings")
        
    assert len(issues) == 0, f"Found {len(issues)} frontend code quality issues"

if __name__ == "__main__":
    test_frontend_code_quality()
