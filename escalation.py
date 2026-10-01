"""Tiered escalation system for check-in responses."""
import time
from enum import Enum
from typing import Dict, Optional


class EscalationState(Enum):
    """States in the escalation state machine."""
    PENDING = "pending"
    REPROMPTED = "reprompted"
    CAREGIVER_NOTIFIED = "caregiver_notified"
    URGENT = "urgent"


class EscalationManager:
    """Manages escalation state for each user's check-ins."""

    # Configuration thresholds (in seconds)
    REPROMPT_THRESHOLD = 3600  # 1 hour
    CAREGIVER_THRESHOLD = 7200  # 2 hours
    URGENT_THRESHOLD = 14400  # 4 hours

    def __init__(self):
        # Track escalation state per check-in
        self.escalation_states = {}  # checkin_id: EscalationState
        self.checkin_timestamps = {}  # checkin_id: timestamp
        self.last_actions = {}  # checkin_id: {"type": "ack|snooze", "timestamp": float}

    def start_checkin(self, checkin_id: str) -> None:
        """Start a new check-in at PENDING state."""
        self.escalation_states[checkin_id] = EscalationState.PENDING
        self.checkin_timestamps[checkin_id] = time.time()
        self.last_actions[checkin_id] = None

    def get_current_state(self, checkin_id: str) -> Optional[EscalationState]:
        """Get current escalation state for a check-in."""
        return self.escalation_states.get(checkin_id)

    def should_escalate(self, checkin_id: str) -> Optional[EscalationState]:
        """Determine if escalation is needed and return target state."""
        if checkin_id not in self.escalation_states:
            return None

        current_state = self.escalation_states[checkin_id]
        elapsed = time.time() - self.checkin_timestamps[checkin_id]

        # Check time-based escalation
        if current_state == EscalationState.PENDING and elapsed > self.REPROMPT_THRESHOLD:
            return EscalationState.REPROMPTED
        elif current_state == EscalationState.REPROMPTED and elapsed > self.CAREGIVER_THRESHOLD:
            return EscalationState.CAREGIVER_NOTIFIED
        elif current_state == EscalationState.CAREGIVER_NOTIFIED and elapsed > self.URGENT_THRESHOLD:
            return EscalationState.URGENT

        return None

    def escalate(self, checkin_id: str) -> bool:
        """Escalate to next state if appropriate."""
        target_state = self.should_escalate(checkin_id)
        if target_state and self.escalation_states[checkin_id] != target_state:
            self.escalation_states[checkin_id] = target_state
            return True
        return False

    def acknowledge(self, checkin_id: str) -> None:
        """Acknowledge check-in - reset to PENDING and update timestamp."""
        if checkin_id in self.escalation_states:
            self.escalation_states[checkin_id] = EscalationState.PENDING
            self.checkin_timestamps[checkin_id] = time.time()
            self.last_actions[checkin_id] = {"type": "ack", "timestamp": time.time()}

    def snooze(self, checkin_id: str, duration_seconds: int = 3600) -> None:
        """Snooze a check-in - extend the timeout."""
        if checkin_id in self.escalation_states:
            self.checkin_timestamps[checkin_id] += duration_seconds
            self.last_actions[checkin_id] = {"type": "snooze", "timestamp": time.time()}

    def is_escalated(self, checkin_id: str) -> bool:
        """Check if a check-in has escalated beyond PENDING."""
        state = self.get_current_state(checkin_id)
        return state is not None and state != EscalationState.PENDING

    def get_escalation_level(self, checkin_id: str) -> int:
        """Get numeric escalation level for sorting/filtering."""
        state = self.get_current_state(checkin_id)
        if state is None:
            return 0
        return {
            EscalationState.PENDING: 0,
            EscalationState.REPROMPTED: 1,
            EscalationState.CAREGIVER_NOTIFIED: 2,
            EscalationState.URGENT: 3,
        }[state]


# Global instance for use across the application
escalation_manager = EscalationManager()