"""Unit tests for patterns.py"""
import pytest
from datetime import datetime, timedelta
import sys
sys.path.append('src')
from carebridge.patterns import pattern_detector, PatternDetector


class TestPatternDetector:
    """Test cases for PatternDetector class."""

    def setup_method(self):
        """Reset pattern detector before each test."""
        pattern_detector.checkin_history.clear()

    def test_no_data_returns_empty_summary(self):
        """Test that no data returns appropriate summary."""
        result = pattern_detector.analyze_patterns("user1")
        assert result["patterns"] == []
        assert "No data available" in result["summary"]

    def test_detects_missed_meals_pattern(self):
        """Test detection of missed meals."""
        user_id = "user1"
        now = datetime.now()

        # Add check-ins for 7 days
        # Days 0,1,4,5,6: meal check-ins
        # Days 2,3: no meal check-ins (missed meals)
        for i in range(7):
            date = now - timedelta(days=i)
            # Miss meals on days 2 and 3 (relative to now)
            if i == 2 or i == 3:
                # No meal check-in - missed meal
                pass
            else:
                pattern_detector.add_checkin(user_id, "meal", "Yes", date)

        result = pattern_detector.analyze_patterns(user_id)
        missed_meal_patterns = [p for p in result["patterns"] if p["type"] == "missed_meals"]
        assert len(missed_meal_patterns) == 1
        assert missed_meal_patterns[0]["severity"] == "medium"
        assert "2 days" in missed_meal_patterns[0]["details"]

    def test_detects_medication_timing_shift(self):
        """Test detection of medication timing changes."""
        user_id = "user1"
        now = datetime.now()

        # Add medication check-ins with shifted timing (more than 2 hours from 8am)
        for i in range(5):
            time_shifted = now - timedelta(hours=i*24)  # Daily
            # Record at 11am instead of 8am (3 hours difference)
            time_shifted = time_shifted.replace(hour=11)
            pattern_detector.add_checkin(user_id, "medication", "Yes", time_shifted)

        result = pattern_detector.analyze_patterns(user_id)
        timing_patterns = [p for p in result["patterns"] if p["type"] == "medication_timing"]
        assert len(timing_patterns) == 1
        assert timing_patterns[0]["severity"] == "medium"
        assert "shifted to average 11.0h" in timing_patterns[0]["details"]

    def test_detects_response_decline(self):
        """Test detection of response decline pattern."""
        user_id = "user1"
        now = datetime.now()

        # Add check-ins with slow responses
        for i in range(3):
            time_point = now - timedelta(hours=i*6)  # Every 6 hours
            pattern_detector.add_checkin(
                user_id, "general", "Slow response",
                time_point, {"communication_style": "slow_confused"}
            )

        result = pattern_detector.analyze_patterns(user_id)
        response_patterns = [p for p in result["patterns"] if p["type"] == "response_decline"]
        assert len(response_patterns) == 1
        assert response_patterns[0]["severity"] == "medium"
        assert "3 recent slow responses" in response_patterns[0]["details"]

    def test_no_patterns_returns_normal_summary(self):
        """Test that normal routine returns appropriate summary."""
        user_id = "user1"
        now = datetime.now()

        # Add consistent check-ins at normal times (8am for medication)
        for i in range(5):
            date = now - timedelta(days=i)
            # Add meal check-in
            pattern_detector.add_checkin(user_id, "meal", "Yes", date)
            # Add medication check-in at 8am (normal time)
            medication_time = date.replace(hour=8)
            pattern_detector.add_checkin(user_id, "medication", "Yes", medication_time)

        result = pattern_detector.analyze_patterns(user_id)
        # Should have no patterns for normal routine
        assert result["patterns"] == []
        assert "No unusual patterns detected" in result["summary"]

    def test_multiple_patterns_detected(self):
        """Test detection of multiple patterns simultaneously."""
        user_id = "user1"
        now = datetime.now()

        # Reset pattern detector
        pattern_detector.checkin_history.clear()

        # Miss meals for 2 consecutive days
        pattern_detector.add_checkin(user_id, "meal", "No", now - timedelta(days=1))
        pattern_detector.add_checkin(user_id, "meal", "No", now - timedelta(days=2))
        # Add a meal check-in to establish baseline
        pattern_detector.add_checkin(user_id, "meal", "Yes", now - timedelta(days=0))

        # Shifted medication timing (more than 2 hours from 8am)
        for i in range(3):
            time_shifted = now.replace(hour=11) - timedelta(days=i)
            pattern_detector.add_checkin(user_id, "medication", "Yes", time_shifted)

        # Slow responses
        pattern_detector.add_checkin(
            user_id, "general", "Slow",
            now, {"communication_style": "slow_confused"}
        )
        pattern_detector.add_checkin(
            user_id, "general", "Slow",
            now - timedelta(hours=1), {"communication_style": "slow_confused"}
        )
        pattern_detector.add_checkin(
            user_id, "general", "Slow",
            now - timedelta(hours=2), {"communication_style": "slow_confused"}
        )

        result = pattern_detector.analyze_patterns(user_id)
        # Should detect at least some patterns
        assert len(result["patterns"]) >= 1

        # Check that we detect the expected pattern types
        pattern_types = [p["type"] for p in result["patterns"]]
        # At least one of these should be present
        expected_patterns = ["missed_meals", "medication_timing", "response_decline"]
        assert any(pattern in pattern_types for pattern in expected_patterns)

    def test_custom_period_analysis(self):
        """Test pattern analysis over custom time periods."""
        user_id = "user1"
        now = datetime.now()

        # Add check-ins for 14 days
        for i in range(14):
            date = now - timedelta(days=i)
            if i % 3 == 0:  # Miss every 3rd day
                pass  # Miss meal
            else:
                pattern_detector.add_checkin(user_id, "meal", "Yes", date)

        # Analyze for last 7 days
        recent_result = pattern_detector.analyze_patterns(user_id, days=7)
        # Analyze for last 14 days
        full_result = pattern_detector.analyze_patterns(user_id, days=14)

        # Should detect more patterns in full period
        assert len(full_result["patterns"]) >= len(recent_result["patterns"])
        assert full_result["period_days"] == 14
        assert recent_result["period_days"] == 7

    def test_summary_includes_total_checkins(self):
        """Test that summary includes total check-in count."""
        user_id = "user1"
        now = datetime.now()

        # Add 5 check-ins
        for i in range(5):
            date = now - timedelta(days=i)
            pattern_detector.add_checkin(user_id, "meal", "Yes", date)

        result = pattern_detector.analyze_patterns(user_id)
        assert result["total_checkins"] == 5
        assert "Total check-ins this week: 5" in result["summary"]