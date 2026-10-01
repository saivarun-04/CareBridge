"""Adaptive communication style based on response patterns."""
import time
from typing import Dict, Optional


class CommunicationStyle:
    """Manages adaptive communication style for each user."""

    def __init__(self):
        # Track response times and confusion indicators per user
        self.response_times = {}  # user_id: list of response times in seconds
        self.confusion_indicators = {}  # user_id: count of confused responses
        self.last_adaptation = {}  # user_id: timestamp of last adaptation

    def record_response(self, user_id: str, response_time: float,
                       was_confused: bool = False) -> None:
        """Record a response for style adaptation analysis."""
        if user_id not in self.response_times:
            self.response_times[user_id] = []
            self.confusion_indicators[user_id] = 0

        # Record response time (keep only last 5 responses)
        self.response_times[user_id].append(response_time)
        if len(self.response_times[user_id]) > 5:
            self.response_times[user_id].pop(0)

        # Track confusion indicators
        if was_confused:
            self.confusion_indicators[user_id] += 1
        else:
            # Decay confusion score over time
            self.confusion_indicators[user_id] = max(0, self.confusion_indicators[user_id] - 0.1)

    def get_adapted_style(self, user_id: str, base_profile: Dict) -> Dict:
        """Get adapted communication style based on recent patterns."""
        adapted = base_profile.copy()

        # Check if we should adapt
        if self._should_adapt(user_id):
            style = self._determine_new_style(user_id)
            adapted["communication"] = style
            self.last_adaptation[user_id] = time.time()
        else:
            # Keep existing style or use normal as default
            adapted["communication"] = base_profile.get("communication", "normal")

        return adapted

    def _should_adapt(self, user_id: str) -> bool:
        """Determine if style adaptation is needed."""
        if user_id not in self.response_times:
            return False

        times = self.response_times[user_id]
        confusion = self.confusion_indicators.get(user_id, 0)

        # Adapt if:
        # 1. Average response time > 60 seconds AND we have 3+ responses
        # 2. Confusion score > 2
        # 3. Last adaptation was > 24 hours ago (only if an adaptation has occurred)
        avg_time = sum(times) / len(times) if times else 0

        recent_adaptation = self.last_adaptation.get(user_id)
        if recent_adaptation is not None:
            time_since_adapt = time.time() - recent_adaptation
        else:
            time_since_adapt = None

        return (len(times) >= 3 and avg_time > 60) or confusion > 2 or (time_since_adapt is not None and time_since_adapt > 86400)

    def _determine_new_style(self, user_id: str) -> str:
        """Determine the new communication style based on patterns."""
        times = self.response_times[user_id]
        confusion = self.confusion_indicators.get(user_id, 0)

        avg_time = sum(times) / len(times) if times else 0

        if confusion > 2 or avg_time > 120:
            return "slow_confused"
        elif avg_time > 60:
            return "slow"
        else:
            return "normal"


# Global instance for use across the application
style_manager = CommunicationStyle()