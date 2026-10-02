"""Unit tests for style.py"""
import time
import pytest
import sys
sys.path.append('src')
from carebridge.style import style_manager, CommunicationStyle


class TestCommunicationStyle:
    """Test cases for CommunicationStyle class."""

    def setup_method(self):
        """Reset style manager before each test."""
        style_manager.response_times.clear()
        style_manager.confusion_indicators.clear()
        style_manager.last_adaptation.clear()

    def test_normal_style_by_default(self):
        """Test that normal style is used by default."""
        base_profile = {"preferred_name": "Alice"}
        adapted = style_manager.get_adapted_style("user1", base_profile)
        assert adapted["communication"] == "normal"

    def test_slow_confusion_adaptation(self):
        """Test adaptation to slow_confused style based on response patterns."""
        user_id = "user1"
        base_profile = {"preferred_name": "Alice"}

        # Record slow and confused responses
        style_manager.record_response(user_id, 120, was_confused=True)
        style_manager.record_response(user_id, 150, was_confused=True)
        style_manager.record_response(user_id, 90, was_confused=True)

        adapted = style_manager.get_adapted_style(user_id, base_profile)
        assert adapted["communication"] == "slow_confused"

    def test_slow_response_adaptation(self):
        """Test adaptation to slow style based on response times."""
        user_id = "user1"
        base_profile = {"preferred_name": "Bob"}

        # Record slow but not confused responses
        style_manager.record_response(user_id, 80)
        style_manager.record_response(user_id, 90)
        style_manager.record_response(user_id, 100)

        adapted = style_manager.get_adapted_style(user_id, base_profile)
        assert adapted["communication"] == "slow"

    def test_no_adaptation_with_faster_responses(self):
        """Test no adaptation when responses are normal speed."""
        user_id = "user1"
        base_profile = {"preferred_name": "Charlie"}

        # Record normal response times
        style_manager.record_response(user_id, 30)
        style_manager.record_response(user_id, 25)
        style_manager.record_response(user_id, 35)

        adapted = style_manager.get_adapted_style(user_id, base_profile)
        assert adapted["communication"] == "normal"

    def test_confusion_decay(self):
        """Test that confusion indicators decay over time."""
        user_id = "user1"
        base_profile = {"preferred_name": "Diana"}

        # Record initial confused responses
        style_manager.record_response(user_id, 60, was_confused=True)
        style_manager.record_response(user_id, 70, was_confused=True)

        # Record non-confused responses (should reduce confusion score)
        style_manager.record_response(user_id, 30)
        style_manager.record_response(user_id, 25)

        # Should not adapt yet
        adapted = style_manager.get_adapted_style(user_id, base_profile)
        assert adapted["communication"] == "normal"

    def test_preserves_other_profile_attributes(self):
        """Test that adaptation preserves other profile attributes."""
        user_id = "user1"
        base_profile = {
            "preferred_name": "Eve",
            "age": 75,
            "language": "English"
        }

        style_manager.record_response(user_id, 120, was_confused=True)
        style_manager.record_response(user_id, 130, was_confused=True)
        style_manager.record_response(user_id, 140, was_confused=True)

        adapted = style_manager.get_adapted_style(user_id, base_profile)
        assert adapted["preferred_name"] == "Eve"
        assert adapted["age"] == 75
        assert adapted["language"] == "English"
        assert adapted["communication"] == "slow_confused"

    def test_respects_existing_communication_style(self):
        """Test that existing communication style is respected when no adaptation needed."""
        user_id = "user1"
        base_profile = {
            "preferred_name": "Frank",
            "communication": "custom"
        }

        # Record some responses but not enough to trigger adaptation
        style_manager.record_response(user_id, 30)
        style_manager.record_response(user_id, 25)
        style_manager.record_response(user_id, 20)  # Fast responses

        adapted = style_manager.get_adapted_style(user_id, base_profile)
        # With only 3 fast responses, should not adapt and keep original style
        assert adapted["communication"] == "custom"