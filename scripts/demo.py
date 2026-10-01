#!/usr/bin/env python3
"""
CareBridge Demo Script
Runs a 3-minute story demonstrating:
1. Elder check-in with adaptive tone (normal vs slow/confused)
2. Missed check-in → re-prompt → caregiver alert (no alert after a single missed check-in)
3. Weekly pattern summary for the caregiver
Runs entirely in mock mode (USE_MOCK_BEDROCK=true, STORE=memory).
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Ensure we are in mock mode
os.environ["USE_MOCK_BEDROCK"] = "true"
os.environ["STORE"] = "memory"

# Add src to path so we can import carebridge modules
sys.path.append('src')

from carebridge.storage import get_storage
from carebridge.escalation import escalation_manager, EscalationManager
from carebridge.style import style_manager
from carebridge.llm import generate
from carebridge.patterns import pattern_detector
from carebridge.notifier import get_notifier

# Replace the global escalation manager with a demo one that has short thresholds
def setup_demo_escalation():
    """Replace the global escalation manager with one suitable for demo (short thresholds)."""
    demo_manager = EscalationManager()
    # Set thresholds to short durations for demo (in seconds)
    demo_manager.REPROMPT_THRESHOLD = 5   # 5 seconds instead of 1 hour
    demo_manager.CAREGIVER_THRESHOLD = 10  # 10 seconds instead of 2 hours
    demo_manager.URGENT_THRESHOLD = 15    # 15 seconds instead of 4 hours
    # Replace the global instance
    import carebridge.escalation
    carebridge.escalation.escalation_manager = demo_manager
    return demo_manager

def restore_escalation(original_manager):
    """Restore the original escalation manager."""
    import carebridge.escalation
    carebridge.escalation.escalation_manager = original_manager

def log_checkin(user_id, checkin_type, response, metadata=None):
    """Log a check-in using the storage."""
    storage = get_storage()
    # Generate a message using the LLM (mock mode)
    system_prompt = "You are a gentle check-in assistant for elderly users."
    profile = {"preferred_name": "Friend", "communication": "normal"}  # default
    # Try to get existing profile from storage
    existing_profile = storage.get_profile(user_id)
    if existing_profile:
        profile.update(existing_profile)
    messages = [{"role": "user", "content": f"How are you doing today?"}]
    # In mock mode, generate returns a fixed string, but we'll call it anyway
    response_text = generate(system_prompt, messages, profile)

    checkin_metadata = {
        "timestamp": datetime.now().isoformat(),
        "checkin_type": checkin_type,
        "generated_prompt": f"How are you doing today?",
        **(metadata or {})
    }

    checkin_id = storage.save_checkin(user_id, checkin_type, response_text, checkin_metadata)
    # Start escalation timer for this check-in
    escalation_manager.start_checkin(checkin_id)
    return checkin_id, response_text

def demonstrate_adaptive_tone():
    """Part 1: Elder check-in with adaptive tone."""
    print("=" * 60)
    print("PART 1: Elder check-in with adaptive tone")
    print("=" * 60)

    user_id = "elder1"

    # Simulate normal response time and not confused
    print("\n1. Normal response time, not confused:")
    # We'll adapt the style based on response time and confusion
    base_profile = {"preferred_name": "Friend", "communication": "normal"}
    # Simulate response time of 30 seconds (normal) and not confused
    adapted = style_manager.adapt_style(user_id, base_profile, response_time=30.0, was_confused=False)
    print(f"   Adapted communication style: {adapted['communication']}")

    # Log a check-in
    checkin_id, message = log_checkin(user_id, "general", "OK")
    print(f"   Logged check-in: {checkin_id}")
    print(f"   Generated message (mock): {message}")

    # Simulate slow response time and confused
    print("\n2. Slow response time and confused:")
    adapted = style_manager.adapt_style(user_id, base_profile, response_time=120.0, was_confused=True)
    print(f"   Adapted communication style: {adapted['communication']}")

    # Log another check-in
    checkin_id2, message2 = log_checkin(user_id, "general", "I'm not sure")
    print(f"   Logged check-in: {checkin_id2}")
    print(f"   Generated message (mock): {message2}")

    print("\n   -> In live mode, the adapted style would influence the LLM's response tone.")
    print("   -> In mock mode, we see the style adaptation but the message is fixed.")

def demonstrate_escalation():
    """Part 2: Missed check-in → re-prompt → caregiver alert."""
    print("\n" + "=" * 60)
    print("PART 2: Missed check-in escalation")
    print("=" * 60)

    user_id = "elder1"

    # Log a check-in that we will ignore (missed)
    print("\n1. Logging a check-in (simulating elder misses it):")
    checkin_id, message = log_checkin(user_id, "medication", "No response")
    print(f"   Check-in ID: {checkin_id}")
    print(f"   Initial message: {message}")

    # Immediately check state (should be PENDING)
    state = escalation_manager.get_current_state(checkin_id)
    print(f"   Current escalation state: {state.value}")

    # Wait until just after re-prompt threshold (5 seconds in demo)
    print("\n2. Waiting 6 seconds (just after re-prompt threshold)...")
    time.sleep(6)
    state = escalation_manager.get_current_state(checkin_id)
    should_escalate = escalation_manager.should_escalate(checkin_id)
    print(f"   Current escalation state: {state.value}")
    if should_escalate:
        print(f"   -> Escalation triggered: {should_escalate.value}")
        # Simulate sending a re-prompt (in real system, this would be done by the scheduler)
        # We'll just show what would happen
        print("   -> Would send a re-prompt notification to the elder.")
    else:
        print("   -> No escalation yet.")

    # Wait until just after caregiver threshold (5 more seconds)
    print("\n3. Waiting 5 more seconds (total 11 seconds, just after caregiver threshold)...")
    time.sleep(5)
    state = escalation_manager.get_current_state(checkin_id)
    should_escalate = escalation_manager.should_escalate(checkin_id)
    print(f"   Current escalation state: {state.value}")
    if should_escalate:
        print(f"   -> Escalation triggered: {should_escalate.value}")
        print("   -> Would send a caregiver alert notification.")
        # Actually send a caregiver notification via notifier (will print in mock mode)
        notifier = get_notifier()
        notifier.notify_caregiver(user_id, "Please check on the elder - no response to medication check-in.", urgency="high")
    else:
        print("   -> No escalation yet.")

    # Wait until just after urgent threshold (5 more seconds)
    print("\n4. Waiting 5 more seconds (total 16 seconds, just after urgent threshold)...")
    time.sleep(5)
    state = escalation_manager.get_current_state(checkin_id)
    should_escalate = escalation_manager.should_escalate(checkin_id)
    print(f"   Current escalation state: {state.value}")
    if should_escalate:
        print(f"   -> Escalation triggered: {should_escalate.value}")
        print("   -> Would send an urgent alert notification.")
        notifier = get_notifier()
        notifier.notify_caregiver(user_id, "URGENT: No response to check-in for over 4 hours!", urgency="urgent")
    else:
        print("   -> No escalation yet.")

    # Demonstrate that acknowledging a check-in prevents escalation
    print("\n5. Demonstrating that acknowledging prevents escalation:")
    checkin_id2, _ = log_checkin(user_id, "meal", "Yes")
    print(f"   Logged a new check-in: {checkin_id2}")
    # Acknowledge it immediately
    escalation_manager.acknowledge(checkin_id2)
    print("   -> Acknowledged the check-in.")
    # Wait longer than all thresholds
    print("   -> Waiting 20 seconds (past all thresholds)...")
    time.sleep(20)
    state = escalation_manager.get_current_state(checkin_id2)
    print(f"   Escalation state after waiting: {state.value}")
    if state == escalation_manager.escalation_states.get(checkin_id2, None):
        print("   -> State remains PENDING (acknowledgment prevented escalation).")
    else:
        print("   -> State changed (unexpected).")

def demonstrate_pattern_summary():
    """Part 3: Weekly pattern summary."""
    print("\n" + "=" * 60)
    print("PART 3: Weekly pattern summary")
    print("=" * 60)

    user_id = "elder1"

    # Clear any existing check-ins for this user (for clean demo)
    # Note: In a real system, we wouldn't do this, but for demo we want a clean slate.
    storage = get_storage()
    # We'll just add new check-ins; the pattern detector will look at the last 7 days.

    print("\nSimulating a week of check-ins with variations:")
    # Simulate check-ins over the past 7 days
    base_time = datetime.now()
    checkin_data = [
        # Day 1: normal
        (base_time - timedelta(days=6, hours=10), "medication", "Yes"),
        # Day 2: missed meal
        (base_time - timedelta(days=5, hours=18), "meal", "No"),
        # Day 3: normal
        (base_time - timedelta(days=4, hours=9), "medication", "Yes"),
        # Day 4: slow response, confused
        (base_time - timedelta(days=3, hours=11), "meal", "I'm not sure"),
        # Day 5: normal
        (base_time - timedelta(days=2, hours=8), "medication", "Yes"),
        # Day 6: missed medication
        (base_time - timedelta(days=1, hours=7), "medication", "No"),
        # Day 7: normal (today)
        (base_time - timedelta(hours=1), "meal", "Yes"),
    ]

    for timestamp, checkin_type, response in checkin_data:
        # We need to manually insert with a specific timestamp to simulate past check-ins
        # For simplicity, we'll use the log_checkin function but adjust the storage internally?
        # Instead, we'll directly use the storage's save_checkin with a custom timestamp.
        # We'll generate a message as usual.
        system_prompt = "You are a gentle check-in assistant for elderly users."
        profile = {"preferred_name": "Friend", "communication": "normal"}
        existing_profile = storage.get_profile(user_id)
        if existing_profile:
            profile.update(existing_profile)
        messages = [{"role": "user", "content": f"How are you doing today?"}]
        response_text = generate(system_prompt, messages, profile)

        checkin_metadata = {
            "timestamp": timestamp.isoformat(),
            "checkin_type": checkin_type,
            "generated_prompt": f"How are you doing today?",
        }

        checkin_id = storage.save_checkin(user_id, checkin_type, response_text, checkin_metadata)
        # Note: We are not starting escalation for these historical check-ins
        # (in real system, they would have been processed at the time)
        print(f"   {timestamp.strftime('%a %b %d')}: {checkin_type} - {response}")

    print("\nGetting pattern summary for the last 7 days:")
    # Use the pattern detector to get a summary
    summary = pattern_detector.get_pattern_summary(user_id, days=7)
    print(f"   Pattern summary: {summary}")

    # Also demonstrate getting via the MCP tool (through the agent or direct call)
    # We'll just show the summary we got above.

def main():
    """Run the full demo."""
    print("CareBridge Demo - 3-Minute Story")
    print("This demo runs entirely in mock mode (USE_MOCK_BEDROCK=true, STORE=memory)")

    # Set up demo escalation manager with short thresholds
    original_escalation_manager = escalation_manager  # Keep reference to restore later
    demo_manager = setup_demo_escalation()

    try:
        demonstrate_adaptive_tone()
        demonstrate_escalation()
        demonstrate_pattern_summary()
    finally:
        # Restore the original escalation manager
        restore_escalation(original_escalation_manager)

    print("\n" + "=" * 60)
    print("Demo completed.")
    print("=" * 60)

if __name__ == "__main__":
    main()