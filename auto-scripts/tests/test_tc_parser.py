import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import parse_tc_markdown

SAMPLE_MD = """# Test Cases: Login

| TC ID | Name | Module | Priority | Type | Test Data | Steps | Expected Result |
|---|---|---|---|---|---|---|---|
| TC-01 | Valid login | Auth | High | Functional | username: admin, password: secret | 1. Navigate to /login\\n2. Enter username "admin"\\n3. Enter password "secret"\\n4. Click Login button\\n5. Verify redirect to /dashboard | User is redirected to dashboard |
| TC-02 | Empty username | Auth | Medium | Negative | username: (empty), password: secret | 1. Navigate to /login\\n2. Leave username empty\\n3. Enter password "secret"\\n4. Click Login button\\n5. Verify error message displayed | Error message "Username required" shown |
"""

def test_parse_returns_two_tcs():
    tcs = parse_tc_markdown(SAMPLE_MD)
    assert len(tcs) == 2

def test_parse_tc_fields():
    tcs = parse_tc_markdown(SAMPLE_MD)
    tc = tcs[0]
    assert tc["id"] == "TC-01"
    assert tc["name"] == "Valid login"
    assert tc["priority"] == "High"
    assert "Navigate to /login" in tc["steps_raw"]
    assert "redirected to dashboard" in tc["expected_result"]

def test_parse_test_data():
    tcs = parse_tc_markdown(SAMPLE_MD)
    assert "admin" in tcs[0]["test_data"]

def test_parse_skips_non_tc_rows():
    md = """
| Header | Row | x | x | x | x | x | x |
|---|---|---|---|---|---|---|---|
| TC-01 | Name | Mod | High | Func | data | 1. step | result |
## Coverage Matrix
| Requirement | TC IDs |
| FR-01 | TC-01 |
"""
    tcs = parse_tc_markdown(md)
    assert len(tcs) == 1
    assert tcs[0]["id"] == "TC-01"
