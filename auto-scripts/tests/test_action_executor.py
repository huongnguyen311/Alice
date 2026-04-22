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
