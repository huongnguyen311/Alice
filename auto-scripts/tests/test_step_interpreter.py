import json
import sys
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import interpret_steps

STEPS_RAW = "1. Navigate to /login\n2. Enter username \"admin\"\n3. Click Login button\n4. Verify redirect to /dashboard"
TEST_DATA = "username: admin, password: secret"

MOCK_ACTIONS = [
    {"action": "navigate", "target": "", "value": "", "url": "/login", "assertion": {"type": "", "expected": ""}, "confidence": 0.95},
    {"action": "fill", "target": "username", "value": "admin", "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9},
    {"action": "click", "target": "login_button", "value": "", "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.85},
    {"action": "verify", "target": "", "value": "", "url": "", "assertion": {"type": "url", "expected": "/dashboard"}, "confidence": 0.9},
]

def test_interpret_steps_returns_list():
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=f"```json\n{json.dumps(MOCK_ACTIONS)}\n```")]
    mock_client.messages.create.return_value = mock_msg

    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    assert isinstance(actions, list)
    assert len(actions) == 4

def test_interpret_steps_action_schema():
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(MOCK_ACTIONS))]
    mock_client.messages.create.return_value = mock_msg

    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    for action in actions:
        assert "action" in action
        assert "confidence" in action
        assert action["action"] in ("navigate", "click", "fill", "select", "verify", "wait")

def test_interpret_steps_api_failure_returns_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")

    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    assert len(actions) == 1
    assert actions[0]["action"] == "error"
    assert "API error" in actions[0]["error"]
