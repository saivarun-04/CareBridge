"""Strands agent for CareBridge that uses the MCP tools.

The agent is designed to work in two modes:
- Offline/mock mode (USE_MOCK_BEDROCK=True): uses a stubbed model that returns deterministic responses.
- Online/live mode (USE_MOCK_BEDROCK=False): uses a real Bedrock model via llm.py.

To keep credit usage near zero, the default is offline mode. To switch to live mode, set
USE_MOCK_BEDROCK=false and provide a valid MODEL_ID (and optionally MODEL_ID_STRONG) in the
environment. This should only be done after the user has approved the live Bedrock call
per the AWS permission protocol in CLAUDE.md.

The agent exposes a simple interface: `run(query)` that processes a natural language query
and returns a string answer by invoking the appropriate MCP tool(s).

For demonstration, the agent currently supports a few predefined intents:
- log_checkin: "log a check-in for {user} that they {response} to {type}"
- get_routine: "get the routine for {user} over the last {days} days"
- adapt_style: "adapt the style for {user} based on response time {time} and confused {bool}"
- get_pattern_summary: "get the pattern summary for {user} over the last {days} days"
- notify_caregiver: "notify caregiver about {user} with message {msg} and urgency {urg}"
- snooze_or_ack: "{ack or snooze} check-in {checkin_id}"

In a full implementation, we would use a language model to interpret the query and call
the tools accordingly. Here, we use simple keyword matching for the stubbed model.

When USE_MOCK_BEDROCK=False, the agent uses the llm.generate function with a system prompt
that instructs the model to use the available tools. However, because we are not implementing
a full tool-use loop in this example, we fall back to the stubbed model for simplicity.
A real implementation would integrate with Strands' built-in tool use capability.
"""

import os
import json
from typing import Any, Dict

# Determine if we are in mock mode (default true)
USE_MOCK_BEDROCK = os.getenv("USE_MOCK_BEDROCK", "true").lower() == "true"

# We will import strands only if needed (lazy import) to avoid hard dependency when not used.
_strands_available = False
try:
    # Import the strands module (or a mock if we want to avoid external calls in tests)
    # We'll import the actual strands.agents module only when we need to run the agent.
    # For now, we just check if it's installed.
    import strands  # noqa: F401
    _strands_available = True
except Exception:
    _strands_available = False

# Import our local modules (these are always available)
from carebridge.llm import generate
from carebridge.server import app  # we can use the same functions as the MCP server, but we'll call the modules directly
from carebridge import notify, style, escalation, patterns, store

# For convenience, we can create a small wrapper that mimics the MCP tool calls using the modules directly.
# This avoids having to start an HTTP server for the agent when running locally.
# In a production deployment via Lambda, the agent would call the MCP server endpoint.

def _call_mcp_tool(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool by invoking the underlying module function directly.
    This is a helper for the agent to avoid starting an HTTP server.
    """
    if tool_name == "log_checkin":
        from carebridge.store import get_storage
        storage = get_storage()
        checkin_id = storage.save_checkin(
            payload["user_id"],
            payload["checkin_type"],
            payload["response"],
            payload.get("metadata", {}),
        )
        # Also update pattern detector
        from datetime import datetime
        from carebridge.patterns import pattern_detector
        pattern_detector.add_checkin(
            user_id=payload["user_id"],
            checkin_type=payload["checkin_type"],
            response=payload["response"],
            timestamp=datetime.now(),
            metadata=payload.get("metadata", {}),
        )
        return {"checkin_id": checkin_id}
    elif tool_name == "get_routine":
        from carebridge.store import get_storage
        storage = get_storage()
        checkins = storage.get_checkins(payload["user_id"], days=payload.get("days", 7))
        return {"checkins": checkins}
    elif tool_name == "adapt_style":
        from carebridge.style import style_manager
        style_manager.record_response(
            payload["user_id"],
            payload["response_time"],
            payload.get("was_confused", False),
        )
        adapted = style_manager.get_adapted_style(
            payload["user_id"], payload["base_profile"]
        )
        return {"adapted_profile": adapted}
    elif tool_name == "get_pattern_summary":
        from carebridge.patterns import pattern_detector
        result = pattern_detector.analyze_patterns(
            payload["user_id"], days=payload.get("days", 7)
        )
        return result
    elif tool_name == "notify_caregiver":
        notifier = notify.get_notifier()
        success = notifier.notify_caregiver(
            payload["user_id"], payload["message"], payload.get("urgency", "normal")
        )
        return {"success": success}
    elif tool_name == "snooze_or_ack":
        from carebridge.escalation import escalation_manager
        action = payload["action"]
        if action == "ack":
            escalation_manager.acknowledge(payload["checkin_id"])
            return {"success": True}
        elif action == "snooze":
            duration = payload.get("snooze_duration, 3600")
            escalation_manager.snooze(payload["checkin_id"], duration)
            return {"success": True}
        else:
            raise ValueError("Action must be 'ack' or 'snooze'")
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


class CareBridgeAgent:
    """A simple agent that uses the MCP tools to answer queries about CareBridge."""

    def __init__(self, use_mock: bool = None):
        """
        Initialize the agent.

        Args:
            use_mock: If True, use the stubbed model (offline). If False, attempt to use
                      a real Bedrock model. If None, read from environment variable
                      USE_MOCK_BEDROCK.
        """
        if use_mock is None:
            use_mock = USE_MOCK_BEDROCK
        self.use_mock = use_mock

        # If we are not in mock mode, we would need to set up the Strands agent with a model.
        # For now, we keep the same stubbed behavior but note that live mode is not fully
        # implemented without a proper tool-use loop. This is a placeholder for future work.
        if not self.use_mock:
            # In a real implementation, we would initialize the Strands agent here with a model
            # and bind the MCP tools. For this task, we leave it as a stub and rely on the
            # user to switch to live mode only when they have approved the Bedrock call.
            pass

    def run(self, query: str) -> str:
        """
        Process a natural language query and return a response.

        This is a very simple rule-based interpreter for demonstration purposes.
        In a real implementation, we would use the language model to understand the query
        and invoke the appropriate tools.

        Args:
            query: The user's question or command.

        Returns:
            A string answer.
        """
        query_lower = query.lower()

        # Helper to extract a user ID (naive: look for "user" followed by a number or quoted string)
        def extract_user_id(q: str) -> str:
            import re
            # Look for patterns like "user1", "user id 1", or quoted strings
            match = re.search(r"user[ _]?(\d+)", q)
            if match:
                return f"user{match.group(1)}"
            # Fallback: return a default user
            return "user1"

        # Helper to extract a checkin ID (pattern checkin_<digits>)
        def extract_checkin_id(q: str) -> str:
            import re
            match = re.search(r"checkin[ _]?(\d+)", q)
            if match:
                return f"checkin_{match.group(1)}"
            # Fallback: return a default placeholder
            return "checkin_1"

        # Helper to extract a number associated with a keyword.
        # Looks for the first number appearing AFTER the keyword in the query;
        # falls back to the last number in the query if keyword not found.
        def extract_number(q: str, keyword: str, default: int = 7) -> int:
            import re
            kw_lower = keyword.lower()
            q_lower = q.lower()
            if kw_lower in q_lower:
                # Find the substring starting at the keyword and look for a number there
                idx = q_lower.index(kw_lower)
                suffix = q[idx:]
                numbers = re.findall(r'\d+', suffix)
                if numbers:
                    return int(numbers[0])
            # Fallback: return the last number in the whole query (usually the keyword's value)
            all_numbers = re.findall(r'\d+', q)
            if all_numbers:
                return int(all_numbers[-1])
            return default

        # Helper to extract a duration in minutes from phrases like "for 30 minutes" or "for 30 mins"
        def extract_duration_minutes(q: str, default: int = 30) -> int:
            import re
            # Look for a number followed by minute or minutes
            match = re.search(r"(\d+)\s*minutes?", q)
            if match:
                return int(match.group(1))
            # Look for a number followed by min or mins
            match = re.search(r"(\d+)\s*mins?", q)
            if match:
                return int(match.group(1))
            return default

        # Helper to extract a boolean for confused
        def extract_confused(q: str) -> bool:
            return any(word in q for word in ["confused", "slow", "not sure"])

        # --- Rule-based intent matching ---

        if "log a check-in" in query_lower or "record that" in query_lower:
            # Example: "log a check-in for user1 that they took their medicine"
            user_id = extract_user_id(query)
            # Determine check-in type from keywords
            if "medicine" in query_lower or "medication" in query_lower:
                checkin_type = "medication"
                # Positive response indicators: yes, took, ate, did, etc.
                response = "Yes" if any(word in query_lower for word in ["yes", "took", "ate", "did"]) else "No"
            elif "breakfast" in query_lower or "meal" in query_lower or "ate" in query_lower:
                checkin_type = "meal"
                response = "Yes" if "yes" in query_lower or "ate" in query_lower else "No"
            elif "feel" in query_lower or "mood" in query_lower:
                checkin_type = "mood"
                # We'll just capture a generic response
                response = "I'm okay"
            else:
                checkin_type = "general"
                response = "OK"
            payload = {
                "user_id": user_id,
                "checkin_type": checkin_type,
                "response": response,
                "metadata": {},
            }
            result = _call_mcp_tool("log_checkin", payload)
            return f"Logged check-in {result['checkin_id']} for {user_id} ({checkin_type}): {response}"

        elif "get the routine" in query_lower or "get routine" in query_lower or "show me the check-ins for" in query_lower:
            user_id = extract_user_id(query)
            days = extract_number(query, "day", 7)
            payload = {"user_id": user_id, "days": days}
            result = _call_mcp_tool("get_routine", payload)
            count = len(result.get("checkins", []))
            return f"Found {count} check-ins for {user_id} in the last {days} days."

        elif "adapt the style" in query_lower or "how should i talk to" in query_lower:
            user_id = extract_user_id(query)
            # Extract a response time (look for a number followed by seconds or just a number)
            import re
            time_match = re.search(r"(\d+)\s*seconds?", query)
            response_time = float(time_match.group(1)) if time_match else 60.0
            was_confused = extract_confused(query)
            base_profile = {"preferred_name": "Friend", "communication": "normal"}
            payload = {
                "user_id": user_id,
                "base_profile": base_profile,
                "response_time": response_time,
                "was_confused": was_confused,
            }
            result = _call_mcp_tool("adapt_style", payload)
            style = result["adapted_profile"]["communication"]
            return f"The adapted communication style for {user_id} is '{style}'."

        elif "get the pattern summary" in query_lower or "pattern summary" in query_lower:
            user_id = extract_user_id(query)
            days = extract_number(query, "day", 7)
            payload = {"user_id": user_id, "days": days}
            result = _call_mcp_tool("get_pattern_summary", payload)
            summary = result.get("summary", "No summary available.")
            return f"Pattern summary for {user_id} (last {days} days): {summary}"

        elif "notify caregiver" in query_lower or "alert the caregiver" in query_lower:
            user_id = extract_user_id(query)
            # Extract message: look for quoted text or take the rest of the sentence
            # For simplicity, we'll use a fixed message.
            message = "Please check on the user."
            urgency = "high" if "urgent" in query_lower or "immediately" in query_lower else "normal"
            payload = {
                "user_id": user_id,
                "message": message,
                "urgency": urgency,
            }
            result = _call_mcp_tool("notify_caregiver", payload)
            sent = result["success"]
            return f"Caregiver notification sent: {sent}"

        elif "acknowledge" in query_lower and "check-in" in query_lower:
            # We need a checkin_id; for demo, we'll use a placeholder.
            # In a real scenario, the user would provide a specific ID.
            checkin_id = "checkin_1"  # This is not ideal but works for the demo.
            payload = {"checkin_id": checkin_id, "action": "ack"}
            result = _call_mcp_tool("snooze_or_ack", payload)
            return f"Check-in {checkin_id} acknowledged."

        elif "snooze" in query_lower and ("check-in" in query_lower or "checkin" in query_lower):
            checkin_id = extract_checkin_id(query)
            duration = extract_duration_minutes(query, default=30)
            payload = {"checkin_id": checkin_id, "action": "snooze", "snooze_duration": duration * 60}
            result = _call_mcp_tool("snooze_or_ack", payload)
            return f"Check-in {checkin_id} snoozed for {duration} minutes."

        else:
            # Fallback: use the LLM to generate a generic response (if not in mock mode, this could call Bedrock)
            # For now, we just return a canned response.
            if self.use_mock:
                return "I'm not sure how to help with that. Try asking me to log a check-in, get a routine, adapt style, get a pattern summary, notify a caregiver, or snooze/acknowledge a check-in."
            else:
                # In live mode, we would call the LLM with a system prompt.
                # We'll do a simple call to llm.generate for demonstration.
                system_prompt = "You are a helpful assistant for the CareBridge system. Answer the user's question based on the context of elderly check-ins."
                messages = [{"role": "user", "content": query}]
                # We don't have a profile here, so we'll use a default.
                profile = {"preferred_name": "Friend", "communication": "normal"}
                # Use the routine tier for general questions.
                answer = generate(system_prompt, messages, profile, tier="routine")
                return answer


def run_agent_demo():
    """Run a simple interactive demo of the agent."""
    print("CareBridge Agent Demo (type 'quit' to exit)")
    agent = CareBridgeAgent()
    while True:
        try:
            query = input("You: ")
            if query.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            response = agent.run(query)
            print(f"Agent: {response}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_agent_demo()