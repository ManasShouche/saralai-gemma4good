# Test Aadhaar Images

These are **redacted demo images** for CI/demo use only.
All real Aadhaar numbers are masked as XXXX XXXX XXXX.

## Files

| File | Persona | Notes |
|------|---------|-------|
| `rukmini_aadhaar_redacted.jpg` | Rukmini Devi, F, 52, Tumkur | Primary test persona |
| `raju_aadhaar_redacted.jpg` | Raju Kumar, M, 34, Mysuru | Secondary test persona |

## Generating test fixtures

To add a new test fixture:
1. Use a synthetic Aadhaar generator (e.g. https://github.com/saralai/fixtures)
2. Mask the UID as `XXXX XXXX XXXX` before committing
3. Never commit real Aadhaar data

## Usage

```python
# In backend tests
from pathlib import Path
TEST_AADHAAR = Path(__file__).parent / "test_aadhaars" / "rukmini_aadhaar_redacted.jpg"
```
