"""Unit tests for escalation.py"""
import time
import pytest
import sys
sys.path.append('src')
from carebridge.escalation import escalation_manager, EscalationManager, EscalationState


class TestEscalationManager:
    """Test cases for EscalationManager class."""

    def setup_method(self):
        """Reset escalation manager before each test."""
        escalation_manager.escalation_states.clear()
        escalation_manager.checkin_timestamps.clear()
        escalation_manager.last_actions.clear()

    def test_initial_state(self):
        """Test that new check-ins start in PENDING state."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        state = escalation_manager.get_current_state(checkin_id)
        assert state == EscalationState.PENDING

    def test_no_escalation_initially(self):
        """Test that no escalation occurs immediately after starting."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        should_escalate = escalation_manager.should_escalate(checkin_id)
        assert should_escalate is None

    def test_escalation_to_reprompt(self):
        """Test escalation to REPROMPTED state after threshold."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Set timestamp to simulate time passing beyond threshold
        old_time = time.time() - 3700  # 1 hour and 100 seconds
        escalation_manager.checkin_timestamps[checkin_id] = old_time

        should_escalate = escalation_manager.should_escalate(checkin_id)
        assert should_escalate == EscalationState.REPROMPTED

    def test_escalation_to_caregiver(self):
        """Test escalation to CAREGIVER_NOTIFIED state after second threshold."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Set to reprompted state and simulate time passing
        escalation_manager.escalation_states[checkin_id] = EscalationState.REPROMPTED
        old_time = time.time() - 7300  # 2 hours and 100 seconds
        escalation_manager.checkin_timestamps[checkin_id] = old_time

        should_escalate = escalation_manager.should_escalate(checkin_id)
        assert should_escalate == EscalationState.CAREGIVER_NOTIFIED

    def test_escalation_to_urgent(self):
        """Test escalation to URGENT state after final threshold."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Set to caregiver notified and simulate time passing
        escalation_manager.escalation_states[checkin_id] = EscalationState.CAREGIVER_NOTIFIED
        old_time = time.time() - 14500  # 4 hours and 100 seconds
        escalation_manager.checkin_timestamps[checkin_id] = old_time

        should_escalate = escalation_manager.should_escalate(checkin_id)
        assert should_escalate == EscalationState.URGENT

    def test_acknowledge_resets_state(self):
        """Test that acknowledge resets state to PENDING."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)
        escalation_manager.escalation_states[checkin_id] = EscalationState.REPROMPTED

        escalation_manager.acknowledge(checkin_id)

        state = escalation_manager.get_current_state(checkin_id)
        assert state == EscalationState.PENDING

    def test_snooze_extends_timeout(self):
        """Test that snooze extends the check-in timeout."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        original_time = escalation_manager.checkin_timestamps[checkin_id]
        snooze_duration = 1800  # 30 minutes

        escalation_manager.snooze(checkin_id, snooze_duration)

        new_time = escalation_manager.checkin_timestamps[checkin_id]
        assert new_time == original_time + snooze_duration

    def test_is_escalated_detection(self):
        """Test detection of escalated states."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Initially not escalated
        assert not escalation_manager.is_escalated(checkin_id)

        # After escalation
        escalation_manager.escalation_states[checkin_id] = EscalationState.REPROMPTED
        assert escalation_manager.is_escalated(checkin_id)

    def test_escalation_level_scoring(self):
        """Test escalation level scoring for sorting."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Test each state's level
        escalation_manager.escalation_states[checkin_id] = EscalationState.PENDING
        assert escalation_manager.get_escalation_level(checkin_id) == 0

        escalation_manager.escalation_states[checkin_id] = EscalationState.REPROMPTED
        assert escalation_manager.get_escalation_level(checkin_id) == 1

        escalation_manager.escalation_states[checkin_id] = EscalationState.CAREGIVER_NOTIFIED
        assert escalation_manager.get_escalation_level(checkin_id) == 2

        escalation_manager.escalation_states[checkin_id] = EscalationState.URGENT
        assert escalation_manager.get_escalation_level(checkin_id) == 3

    def test_no_double_escalation(self):
        """Test that escalation doesn't occur if already at target state."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Set to reprompted
        escalation_manager.escalation_states[checkin_id] = EscalationState.REPROMPTED

        # Try to escalate again immediately
        escalated = escalation_manager.escalate(checkin_id)
        assert not escalated

    def test_escalate_method(self):
        """Test the escalate method transitions states correctly."""
        checkin_id = "test_checkin_1"
        escalation_manager.start_checkin(checkin_id)

        # Simulate time passing for reprompt
        old_time = time.time() - 3700
        escalation_manager.checkin_timestamps[checkin_id] = old_time

        # Escalate
        escalated = escalation_manager.escalate(checkin_id)
        assert escalated
        assert escalation_manager.get_current_state(checkin_id) == EscalationState.REPROMPTED

        # Should not escalate again
        escalated = escalation_manager.escalate(checkin_id)
        assert not escalated