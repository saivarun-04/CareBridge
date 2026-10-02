"""Unit tests for the MCP server (src/carebridge/server.py)."""

import sys
sys.path.append('src')

from fastapi.testclient import TestClient

from carebridge.server import app

client = TestClient(app)


def test_log_checkin():
    payload = {
        "user_id": "user1",
        "checkin_type": "medication",
        "response": "Yes",
        "metadata": {"taken": True}
    }
    response = client.post("/mcp/log_checkin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "checkin_id" in data
    assert data["checkin_id"].startswith("checkin_")


def test_get_routine():
    # First, add a check-in
    payload = {
        "user_id": "user2",
        "checkin_type": "meal",
        "response": "Yes",
        "metadata": {}
    }
    client.post("/mcp/log_checkin", json=payload)

    # Now get routine
    payload = {"user_id": "user2", "days": 7}
    response = client.post("/mcp/get_routine", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "checkins" in data
    assert len(data["checkins"]) == 1
    assert data["checkins"][0]["user_id"] == "user2"
    assert data["checkins"][0]["type"] == "meal"


def test_adapt_style():
    from carebridge.style import style_manager
    # Clear any existing state for a clean test
    user_id = "user3_adapt"
    style_manager.response_times.pop(user_id, None)
    style_manager.confusion_indicators.pop(user_id, None)
    style_manager.last_adaptation.pop(user_id, None)

    base_profile = {"preferred_name": "Alice", "communication": "normal"}
    # First call: should not adapt yet (only one confused response)
    payload = {
        "user_id": user_id,
        "base_profile": base_profile,
        "response_time": 100.0,
        "was_confused": True
    }
    response = client.post("/mcp/adapt_style", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["adapted_profile"]["communication"] == "normal"
    # Second call: still not enough confusion (2)
    response = client.post("/mcp/adapt_style", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["adapted_profile"]["communication"] == "normal"
    # Third call: now confusion=3, avg_time=100 -> should adapt to slow_confused
    response = client.post("/mcp/adapt_style", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["adapted_profile"]["communication"] == "slow_confused"


def test_get_pattern_summary():
    # Add some check-ins for a user
    user_id = "user4"
    from datetime import datetime, timedelta
    # We'll rely on the pattern detector's internal state, but we can also call log_checkin multiple times.
    # For simplicity, we'll just call the endpoint with no prior data (should return no patterns).
    payload = {"user_id": user_id, "days": 7}
    response = client.post("/mcp/get_pattern_summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "patterns" in data
    assert "summary" in data
    assert "total_checkins" in data
    assert "period_days" in data
    assert data["total_checkins"] == 0
    assert data["period_days"] == 7


def test_notify_caregiver():
    payload = {
        "user_id": "user5",
        "message": "Test message",
        "urgency": "high"
    }
    response = client.post("/mcp/notify_caregiver", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    # In console mode, it should return True
    assert data["success"] is True


def test_snooze_or_ack():
    # First, we need a checkin_id to snooze/ack. We'll create one via log_checkin.
    payload = {
        "user_id": "user6",
        "checkin_type": "general",
        "response": "OK",
        "metadata": {}
    }
    response = client.post("/mcp/log_checkin", json=payload)
    assert response.status_code == 200
    checkin_id = response.json()["checkin_id"]

    # Test ack
    payload = {"checkin_id": checkin_id, "action": "ack"}
    response = client.post("/mcp/snooze_or_ack", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Test snooze
    payload = {"checkin_id": checkin_id, "action": "snooze", "snooze_duration": 1800}
    response = client.post("/mcp/snooze_or_ack", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_error_missing_field():
    payload = {"user_id": "user7"}  # missing checkin_type and response
    response = client.post("/mcp/log_checkin", json=payload)
    assert response.status_code == 400
    assert "Missing field" in response.json()["detail"]


def test_error_invalid_action():
    payload = {"checkin_id": "test", "action": "invalid"}
    response = client.post("/mcp/snooze_or_ack", json=payload)
    assert response.status_code == 400
    assert "Action must be 'ack' or 'snooze'" in response.json()["detail"]