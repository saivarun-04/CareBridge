"""Unit tests for llm.py"""
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.append('src')
from carebridge.llm import generate, _mock_reply, USE_MOCK


class TestLLMModule:
    """Test cases for llm.py module."""

    def test_mock_reply_normal_communication(self):
        """Test mock reply with normal communication style."""
        profile = {"preferred_name": "Alice"}
        user_text = "Have you taken your medicine today?"

        result = _mock_reply(profile, user_text)

        assert "Alice" in result
        assert "medicine" in result.lower()

    def test_mock_reply_slow_confused_communication(self):
        """Test mock reply with slow_confused communication style."""
        profile = {
            "preferred_name": "Bob",
            "communication": "slow_confused"
        }
        user_text = "Have you taken your medicine today?"

        result = _mock_reply(profile, user_text)

        assert "Bob" in result
        assert "Hello" in result
        assert "medicine" in result.lower()
        assert "Take your time" in result

    def test_mock_reply_different_checkin_types(self):
        """Test mock reply detection of different check-in types."""
        profile = {"preferred_name": "Charlie"}

        # Test medication check-in
        result_meds = _mock_reply(profile, "Have you taken your medication today?")
        assert "medicine" in result_meds.lower()

        # Test meal check-in
        result_meal = _mock_reply(profile, "How was your breakfast?")
        assert "meal" in result_meal.lower() or "eat" in result_meal.lower()

        # Test mood check-in
        result_mood = _mock_reply(profile, "How are you feeling today?")
        assert "mood" in result_mood.lower() or "feel" in result_mood.lower()

    def test_mock_reply_general_checkin(self):
        """Test mock reply for general check-ins."""
        profile = {"preferred_name": "Diana"}
        user_text = "Start the check-in"

        result = _mock_reply(profile, user_text)

        assert "Diana" in result
        assert "Good morning" in result

    def test_generate_with_mock_mode(self):
        """Test generate function in mock mode."""
        # Ensure we're in mock mode
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            from carebridge.llm import USE_MOCK
            assert USE_MOCK is True

            system_prompt = "You are a gentle check-in assistant."
            messages = [{"role": "user", "content": "Have you taken your medicine?"}]
            profile = {"preferred_name": "Eve"}

            result = generate(system_prompt, messages, profile)

            assert "Eve" in result
            assert "medicine" in result.lower()

    def test_generate_with_mock_mode_and_tier(self):
        """Test generate function in mock mode with tier parameter."""
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            system_prompt = "You are a gentle check-in assistant."
            messages = [{"role": "user", "content": "How are you feeling?"}]
            profile = {"preferred_name": "Frank"}

            # Test routine tier
            result_routine = generate(system_prompt, messages, profile, tier="routine")
            assert "Frank" in result_routine

            # Test strong tier (should still use mock)
            result_strong = generate(system_prompt, messages, profile, tier="strong")
            assert "Frank" in result_strong

    @patch('boto3.client')
    def test_generate_with_live_mode(self, mock_boto3):
        """Test generate function in live mode."""
        # Mock boto3 client
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        # Mock Bedrock response
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "Live response from Bedrock"}]
                }
            }
        }

        with patch.dict('os.environ', {
            'USE_MOCK_BEDROCK': 'false',
            'MODEL_ID': 'test-model-id',
            'AWS_REGION': 'ap-south-2'
        }):
            from carebridge.llm import USE_MOCK
            assert USE_MOCK is False

            system_prompt = "You are a gentle check-in assistant."
            messages = [{"role": "user", "content": "Hello"}]

            result = generate(system_prompt, messages)

            assert result == "Live response from Bedrock"
            mock_client.converse.assert_called_once()

    @patch('boto3.client')
    def test_generate_strong_uses_strong_model(self, mock_boto3):
        """Test that strong tier uses MODEL_ID_STRONG."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "Strong model response"}]
                }
            }
        }

        with patch.dict('os.environ', {
            'USE_MOCK_BEDROCK': 'false',
            'MODEL_ID': 'routine-model',
            'MODEL_ID_STRONG': 'strong-model',
            'AWS_REGION': 'ap-south-2'
        }):
            system_prompt = "Test prompt"
            messages = [{"role": "user", "content": "Test"}]

            # Test routine tier
            generate(system_prompt, messages, tier="routine")
            args1 = mock_client.converse.call_args_list[0]
            assert args1[1]['modelId'] == 'routine-model'

            # Test strong tier
            generate(system_prompt, messages, tier="strong")
            args2 = mock_client.converse.call_args_list[1]
            assert args2[1]['modelId'] == 'strong-model'

    def test_generate_with_max_tokens(self):
        """Test generate function with max_tokens parameter."""
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            system_prompt = "Test prompt"
            messages = [{"role": "user", "content": "Hello"}]

            # This should not raise an error
            result = generate(system_prompt, messages, max_tokens=100)
            assert isinstance(result, str)

    def test_generate_without_messages(self):
        """Test generate function without messages."""
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            system_prompt = "Test prompt"
            messages = []

            result = generate(system_prompt, messages)
            assert isinstance(result, str)

    def test_generate_with_empty_profile(self):
        """Test generate function with empty profile."""
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            system_prompt = "Test prompt"
            messages = [{"role": "user", "content": "Hello"}]
            profile = {}

            result = generate(system_prompt, messages, profile)
            assert isinstance(result, str)

    def test_generate_with_none_profile(self):
        """Test generate function with None profile."""
        with patch.dict('os.environ', {'USE_MOCK_BEDROCK': 'true'}):
            system_prompt = "Test prompt"
            messages = [{"role": "user", "content": "Hello"}]

            result = generate(system_prompt, messages, None)
            assert isinstance(result, str)