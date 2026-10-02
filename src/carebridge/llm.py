"""Single entry point for all model calls in CareBridge.

USE_MOCK_BEDROCK=true  -> canned, profile-aware replies (free, offline)
USE_MOCK_BEDROCK=false -> real Bedrock Converse API
MODEL_ID and AWS_REGION come from environment variables.

Note: Some third-party models on Bedrock may not support the Converse API.
If such a model is used, only the live branch of generate() needs changing.
"""
import os
import sys

# Dynamic evaluation of mock mode via module __getattr__
# No static USE_MOCK variable; callers should access it via attribute lookup.

MODEL_ID = os.getenv("MODEL_ID", "REPLACE_WITH_MODEL_OR_PROFILE_ID")
MODEL_ID_STRONG = os.getenv("MODEL_ID_STRONG", "REPLACE_WITH_MODEL_OR_PROFILE_ID_STRONG")
REGION = os.getenv("AWS_REGION", "ap-south-2")

def __getattr__(name):
    if name == "USE_MOCK":
        return os.getenv("USE_MOCK_BEDROCK", "true").lower() == "true"
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")



def _mock_reply(profile: dict, user_text: str, tier: str = "routine") -> str:
    """Generate mock replies based on profile and check-in type."""
    name = profile.get("preferred_name", "friend")
    comm_style = profile.get("communication", "normal")

    # Check-in type detection
    if "medicine" in user_text.lower() or "medication" in user_text.lower():
        checkin_type = "medication"
    elif "meal" in user_text.lower() or "eat" in user_text.lower():
        checkin_type = "meal"
    elif "mood" in user_text.lower() or "feel" in user_text.lower():
        checkin_type = "mood"
    else:
        checkin_type = "general"

    # Adaptive responses based on communication style
    if comm_style == "slow_confused":
        if checkin_type == "medication":
            return f"Hello {name}. Did you take your medicine? Take your time."
        elif checkin_type == "meal":
            return f"Hi {name}. Did you eat your meal today? It's okay to take your time."
        elif checkin_type == "mood":
            return f"Hello {name}. How are you feeling today? Just say a little if you need to."
        else:
            return f"Hello {name}. How are you today?"
    else:
        if checkin_type == "medication":
            return f"Good morning, {name}! Have you taken your 8 am medicine today?"
        elif checkin_type == "meal":
            return f"Good morning, {name}! How was your breakfast today?"
        elif checkin_type == "mood":
            return f"Good morning, {name}! How are you feeling today?"
        else:
            return f"Good morning, {name}! Hope you're having a great day!"


def generate(system_prompt: str, messages: list, profile: dict | None = None,
             max_tokens: int = 200, tier: str = "routine") -> str:
    """Generate responses using either mock or real Bedrock API.

    Args:
        system_prompt: System instruction for the model
        messages: List of message dicts with role/content
        profile: User profile dict with preferences
        max_tokens: Maximum tokens for response
        tier: "routine" or "strong" - determines which model to use
    """
    profile = profile or {}
    # Evaluate USE_MOCK at call time to allow tests to toggle it
    use_mock = os.getenv("USE_MOCK_BEDROCK", "true").lower() == "true"

    if use_mock:
        last = messages[-1]["content"] if messages else ""
        return _mock_reply(profile, last, tier)

    # Live mode - import boto3 only when needed
    import boto3
    model_id = os.getenv('MODEL_ID_STRONG' if tier == "strong" else 'MODEL_ID',
                        'REPLACE_WITH_MODEL_OR_PROFILE_ID')
    client = boto3.client("bedrock-runtime", region_name=REGION)

    resp = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": m["role"], "content": [{"text": m["content"]}]}
                  for m in messages],
        inferenceConfig={"maxTokens": max_tokens},
    )
    return resp["output"]["message"]["content"][0]["text"]


if __name__ == "__main__":
    sys_prompt = "You are a gentle check-in assistant for elderly users."
    msgs = [{"role": "user", "content": "Start the 8 am check-in."}]

    print("normal :", generate(sys_prompt, msgs, {"preferred_name": "Nani"}))
    print("slow   :", generate(sys_prompt, msgs,
          {"preferred_name": "Nani", "communication": "slow_confused"}))
    print("meds   :", generate(sys_prompt,
          [{"role": "user", "content": "Have you taken your medicine today?"}],
          {"preferred_name": "Ramesh"}, tier="routine"))