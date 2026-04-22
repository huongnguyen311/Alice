import sys
from pathlib import Path
import tempfile
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import write_report

SAMPLE_RESULTS = [
    {
        "id": "TC-01",
        "name": "Valid login",
        "status": "PASS",
        "duration_s": 2.3,
        "steps": [
            {"action": "navigate", "target": "", "status": "PASS", "actual": "Navigated to /login", "error": "", "screenshot_hint": False},
            {"action": "fill", "target": "username", "status": "PASS", "actual": "Filled username with 'admin'", "error": "", "screenshot_hint": False},
            {"action": "verify", "target": "", "status": "PASS", "actual": "URL contains /dashboard", "error": "", "screenshot_hint": False},
        ],
    },
    {
        "id": "TC-02",
        "name": "Empty username",
        "status": "FAIL",
        "duration_s": 1.1,
        "steps": [
            {"action": "navigate", "target": "", "status": "PASS", "actual": "Navigated to /login", "error": "", "screenshot_hint": False},
            {"action": "verify", "target": "error_message", "status": "FAIL", "actual": "", "error": "Text 'Username required' not visible", "screenshot_hint": True},
        ],
    },
]

def test_write_report_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        assert out_path.exists()

def test_write_report_contains_tc_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        content = out_path.read_text(encoding="utf-8")
        assert "TC-01" in content
        assert "TC-02" in content
        assert "PASS" in content
        assert "FAIL" in content
        assert "Total" in content

def test_write_report_stats_row():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        content = out_path.read_text(encoding="utf-8")
        assert "2026-04-22" in content
        assert "https://example.com" in content

def test_write_report_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "nested" / "dir" / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        assert out_path.exists()

def test_write_report_stop_on_fail_flag_reflected():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=True,
            run_date="2026-04-22",
        )
        content = out_path.read_text(encoding="utf-8")
        assert "Yes" in content
