import sys
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import execute_action

def make_page_mock():
    page = MagicMock()
    page.url = "https://example.com/dashboard"
    return page

def test_navigate_action():
    page = make_page_mock()
    action = {"action": "navigate", "url": "https://example.com/login",
               "target": "", "value": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.goto.assert_called_once_with("https://example.com/login")
    assert result["status"] == "PASS"

def test_fill_action():
    page = make_page_mock()
    action = {"action": "fill", "target": "username", "value": "admin",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.fill.assert_called_once()
    assert result["status"] == "PASS"

def test_click_action():
    page = make_page_mock()
    action = {"action": "click", "target": "login_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.click.assert_called_once()
    assert result["status"] == "PASS"

def test_low_confidence_marks_warn():
    page = make_page_mock()
    action = {"action": "click", "target": "some_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.4}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "WARN"

def test_error_action_marks_error():
    page = make_page_mock()
    action = {"action": "error", "error": "API failed", "target": "", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.0}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "ERROR"
    assert "API failed" in result["error"]

def test_playwright_exception_marks_fail():
    page = make_page_mock()
    page.click.side_effect = Exception("Element not found")
    action = {"action": "click", "target": "login_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "FAIL"
    assert "login_button" in result["error"]  # "No element found matching target 'login_button'"


def test_low_confidence_and_action_fails_marks_fail():
    """FAIL always takes precedence over WARN when confidence is low."""
    page = make_page_mock()
    page.click.side_effect = Exception("timeout")
    action = {"action": "click", "target": "btn", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.4}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "FAIL"


def test_build_url_relative_fragment():
    from web_executor import _build_url
    assert _build_url("https://example.com", "/login") == "https://example.com/login"
    assert _build_url("https://example.com/", "login") == "https://example.com/login"
    assert _build_url("https://example.com", "") == "https://example.com"
    assert _build_url("https://example.com", "https://other.com/page") == "https://other.com/page"


def test_build_url_http_prefix_not_treated_as_absolute():
    from web_executor import _build_url
    # "http-error" is a relative path, not an absolute URL
    result = _build_url("https://example.com", "http-error")
    assert result == "https://example.com/http-error"


def test_verify_url_assertion_pass():
    page = make_page_mock()
    page.url = "https://example.com/dashboard"
    action = {"action": "verify", "target": "", "value": "",
               "url": "", "assertion": {"type": "url", "expected": "/dashboard"}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "PASS"


def test_verify_url_assertion_fail():
    page = make_page_mock()
    page.url = "https://example.com/login"
    action = {"action": "verify", "target": "", "value": "",
               "url": "", "assertion": {"type": "url", "expected": "/dashboard"}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "FAIL"
    assert "dashboard" in result["error"]


def test_verify_unknown_assertion_type_fails():
    page = make_page_mock()
    action = {"action": "verify", "target": "", "value": "",
               "url": "", "assertion": {"type": "nonexistent", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "FAIL"
    assert "nonexistent" in result["error"]
