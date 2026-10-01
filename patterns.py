"""Pattern detection and weekly summary generation."""
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class PatternDetector:
    """Detects patterns in check-in history for weekly summaries."""

    def __init__(self):
        # In-memory storage of check-in history
        self.checkin_history = []  # List of checkin records

    def add_checkin(self, user_id: str, checkin_type: str,
                   response: str, timestamp: datetime, metadata: dict = None) -> None:
        """Add a check-in to the history."""
        metadata = metadata or {}

        # Add communication style from metadata if present
        if "communication_style" in metadata:
            response = f"{response} (style: {metadata['communication_style']})"

        self.checkin_history.append({
            "user_id": user_id,
            "type": checkin_type,
            "response": response,
            "metadata": metadata,
            "timestamp": timestamp,
            "date": timestamp.date(),
            "hour": timestamp.hour
        })

    def analyze_patterns(self, user_id: str, days: int = 7) -> Dict:
        """Analyze patterns for a user over specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        user_checkins = [
            c for c in self.checkin_history
            if c["user_id"] == user_id and c["timestamp"] >= cutoff
        ]

        if not user_checkins:
            return {"patterns": [], "summary": "No data available for pattern analysis."}

        patterns = self._detect_specific_patterns(user_checkins)
        summary = self._generate_summary(patterns, user_checkins)

        return {
            "patterns": patterns,
            "summary": summary,
            "total_checkins": len(user_checkins),
            "period_days": days
        }

    def _detect_specific_patterns(self, checkins: List[Dict]) -> List[Dict]:
        """Detect specific patterns in check-in data."""
        patterns = []

        if not checkins:
            return patterns

        # Get date range from the checkins
        dates = [c["date"] for c in checkins]
        start_date = min(dates)
        end_date = max(dates)

        # Generate all dates in the range
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        # Pattern 1: Missed meals - find days with no meal check-ins
        meal_days = {c["date"] for c in checkins if c["type"] == "meal"}
        missed_days = [date for date in all_dates if date not in meal_days]

        # Check for consecutive missed days
        if len(missed_days) >= 2:
            # Check if we have meal check-ins at all (otherwise no pattern)
            if meal_days:
                # Simple check: if more than 2 days missed, flag it
                if len(missed_days) >= 3:
                    patterns.append({
                        "type": "missed_meals",
                        "severity": "high",
                        "details": f"Missed meals for {len(missed_days)} days"
                    })
                else:
                    patterns.append({
                        "type": "missed_meals",
                        "severity": "medium",
                        "details": f"Missed meals for {len(missed_days)} days"
                    })

        # Pattern 2: Medication timing changes
        med_checkins = [c for c in checkins if c["type"] == "medication"]
        if len(med_checkins) >= 3:
            timings = [c["hour"] for c in med_checkins]
            avg_time = sum(timings) / len(timings)
            if abs(avg_time - 8) > 2:  # More than 2 hours from 8am
                patterns.append({
                    "type": "medication_timing",
                    "severity": "medium",
                    "details": f"Medication timing shifted to average {avg_time:.1f}h (from 8h)"
                })

        # Pattern 3: Response time changes
        slow_responses = sum(1 for c in checkins
                          if "slow_confused" in c.get("metadata", {}).get("communication_style", ""))

        if slow_responses >= 3:
            patterns.append({
                "type": "response_decline",
                "severity": "medium",
                "details": f"{slow_responses} recent slow responses"
            })

        return patterns

    def _find_consecutive_missed(self, all_dates: List, meal_dates: set) -> List[List]:
        """Find consecutive days with missed meals."""
        consecutive_missed = []
        current_streak = []

        for date in sorted(all_dates):
            if date not in meal_dates:
                current_streak.append(date)
            else:
                if len(current_streak) >= 2:
                    consecutive_missed.append(current_streak)
                current_streak = []

        # Add final streak if it exists
        if len(current_streak) >= 2:
            consecutive_missed.append(current_streak)

        return consecutive_missed

    def _generate_summary(self, patterns: List[Dict], checkins: List[Dict]) -> str:
        """Generate plain-language summary of patterns."""
        if not patterns:
            return f"No unusual patterns detected. Check-ins are consistent with normal routine. Total check-ins this week: {len(checkins)}"

        # Count by severity
        severity_count = Counter(p["severity"] for p in patterns)

        summary_parts = []

        if severity_count["high"]:
            summary_parts.append("Some concerning patterns detected that may need attention.")
        elif severity_count["medium"]:
            summary_parts.append("Minor changes in routine observed.")
        else:
            summary_parts.append("Generally consistent routine with minor variations.")

        # Add specific pattern details
        for pattern in patterns:
            if pattern["type"] == "missed_meals":
                summary_parts.append("- Meal patterns show some irregularities.")
            elif pattern["type"] == "medication_timing":
                summary_parts.append("- Medication timing has shifted from usual schedule.")
            elif pattern["type"] == "response_decline":
                summary_parts.append("- Response times have been slower recently.")

        summary_parts.append(f"Total check-ins this week: {len(checkins)}")

        return " ".join(summary_parts)


# Global instance for use across the application
pattern_detector = PatternDetector()