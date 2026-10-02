"""Unit tests for the Strands agent (src/carebridge/agent.py)."""

import sys
sys.path.append('src')

from carebridge.agent import CareBridgeAgent


def test_agent_log_checkin():
    """Test that the agent can log a check-in."""
    agent = CareBridgeAgent(use_mock=True)  # force mock mode
    query = "log a check-in for user1 that they took their medicine"
    response = agent.run(query)
    assert "Logged check-in" in response
    assert "user1" in response
    assert "medication" in response


def test_agent_get_routine():
    """Test that the agent can get a routine."""
    agent = CareBridgeAgent(use_mock=True)
    # First, log a check-in so there is something to get
    agent.run("log a check-in for user2 that they ate breakfast")
    query = "get the routine for user2 over the last 1 days"
    response = agent.run(query)
    assert "Found 1 check-ins for user2" in response


def test_agent_adapt_style():
    """Test that the agent can adapt style."""
    agent = CareBridgeAgent(use_mock=True)
    # We need to record enough responses (at least 3) for style adaptation to trigger
    # Or confusion > 2. Let's record multiple slow/confused responses to trigger slow_confused.
    query = "adapt the style for user3 based on response time 150 seconds and confused True"
    agent.run(query)
    agent.run(query)
    response = agent.run(query)
    assert "The adapted communication style for user3 is 'slow_confused'" in response


def test_agent_get_pattern_summary():
    """Test that the agent can get a pattern summary."""
    agent = CareBridgeAgent(use_mock=True)
    # We don't need to log any check-ins for this test because the summary for no data is expected.
    query = "get the pattern summary for user4 over the last 7 days"
    response = agent.run(query)
    assert "Pattern summary for user4" in response
    assert "No data available for pattern analysis." in response


def test_agent_notify_caregiver():
    """Test that the agent can notify a caregiver."""
    agent = CareBridgeAgent(use_mock=True)
    query = "notify caregiver about user5 with message Please check on the user and urgency high"
    response = agent.run(query)
    assert "Caregiver notification sent: True" in response


def test_agent_snooze_or_ack():
    """Test that the agent can snooze or acknowledge a check-in."""
    agent = CareBridgeAgent(use_mock=True)
    # First, we need a check-in to snooze/ack. We'll log one.
    agent.run("log a check-in for user6 that they are OK")
    # Now acknowledge it
    query = "acknowledge check-in checkin_1"
    response = agent.run(query)
    assert "Check-in checkin_1 acknowledged." in response
    # Now snooze it
    query = "snooze checkin_1 for 30 minutes"
    response = agent.run(query)
    assert "Check-in checkin_1 snoozed for 30 minutes." in response


def test_agent_fallback():
    """Test that the agent falls back to a generic response when it doesn't understand."""
    agent = CareBridgeAgent(use_mock=True)
    query = "what is the meaning of life?"
    response = agent.run(query)
    assert "I'm not sure how to help with that" in response