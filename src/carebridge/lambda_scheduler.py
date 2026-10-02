"""Lambda handler for EventBridge Scheduler to start a check-in for a user."""

import json
import os
from datetime import datetime

import boto3

from carebridge.llm import generate
from carebridge.escalation import escalation_manager
from carebridge.notify import get_notifier
from carebridge.store import get_storage
from carebridge.style import style_manager

# Get singletons
storage = get_storage()
notifier = get_notifier()


def lambda_handler(event, context):
    """
    EventBridge Scheduler would call this to start a check-in for a user.
    Expected event format (from EventBridge Scheduler input):
    {
        "user_id": "string",
        "checkin_type": "string" (optional, default "general"),
        "metadata": dict (optional)
    }
    The function will:
    1. Retrieve or create user profile (for simplicity, we'll use a default)
    2. Generate a check-in message using llm.py
    3. Save the check-in record
    4. Start escalation timer
    5. Send the initial check-in notification to the user
    Returns: {"checkin_id": str, "message": str}
    """
    try:
        user_id = event["user_id"]
        checkin_type = event.get("checkin_type", "general")
        metadata = event.get("metadata", {})
    except KeyError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing user_id in event"})
        }

    # Get or create user profile (in a real app, this would come from a database)
    # For now, we'll use a default profile; in production, this would be fetched from storage
    profile = {
        "preferred_name": "Friend",
        "communication": "normal"
    }
    # Try to get existing profile from storage
    existing_profile = storage.get_profile(user_id)
    if existing_profile:
        profile.update(existing_profile)

    # Generate the check-in message using llm.py
    system_prompt = "You are a gentle check-in assistant for elderly users."
    if checkin_type == "medication":
        user_content = "Have you taken your medicine today?"
    elif checkin_type == "meal":
        user_content = "How was your meal today?"
    elif checkin_type == "mood":
        user_content = "How are you feeling today?"
    else:
        user_content = "How are you doing today?"

    messages = [{"role": "user", "content": user_content}]

    # Generate response (will use mock mode if USE_MOCK_BEDROCK=true)
    response_text = generate(system_prompt, messages, profile)

    # Prepare metadata for storage
    checkin_metadata = {
        "timestamp": datetime.now().isoformat(),
        "checkin_type": checkin_type,
        "generated_prompt": user_content,
        **metadata
    }

    # Save the check-in
    checkin_id = storage.save_checkin(user_id, checkin_type, response_text, checkin_metadata)

    # Start escalation timer for this check-in
    escalation_manager.start_checkin(checkin_id)

    # Send the check-in message to the user (this simulates the Alexa+ experience)
    notifier.notify_user(user_id, response_text)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "checkin_id": checkin_id,
            "message": response_text,
            "user_id": user_id,
            "checkin_type": checkin_type
        })
    }