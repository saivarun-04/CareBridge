"""Unit tests for notify.py"""
import pytest
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.append('src')
from carebridge.notify import get_notifier, ConsoleNotification, SNSNotification, EmailNotification


class TestConsoleNotification:
    """Test cases for ConsoleNotification class."""

    def setup_method(self):
        """Set up console notification for testing."""
        self.notifier = ConsoleNotification()

    @patch('builtins.print')
    def test_notify_caregiver_prints_to_console(self, mock_print):
        """Test that caregiver notification prints to console."""
        user_id = "user1"
        message = "Test caregiver alert"
        urgency = "high"

        result = self.notifier.notify_caregiver(user_id, message, urgency)

        assert result is True
        mock_print.assert_called()
        # Check that the output contains expected content
        call_args = mock_print.call_args
        assert f"CAREGIVER ALERT - User: {user_id}" in call_args[0][0]
        assert f"Urgency: {urgency.upper()}" in call_args[0][0]
        assert f"Message: {message}" in call_args[0][0]

    @patch('builtins.print')
    def test_notify_user_prints_to_console(self, mock_print):
        """Test that user notification prints to console."""
        user_id = "user1"
        message = "Test user message"

        result = self.notifier.notify_user(user_id, message)

        assert result is True
        mock_print.assert_called()
        call_args = mock_print.call_args
        assert f"Message to {user_id}: {message}" in call_args[0][0]

    def test_console_notification_always_returns_true(self):
        """Test that console notification always returns True."""
        result = self.notifier.notify_caregiver("user1", "test")
        assert result is True

        result = self.notifier.notify_user("user1", "test")
        assert result is True


class TestSNSNotification:
    """Test cases for SNSNotification class."""

    def setup_method(self):
        """Set up SNS notification for testing."""
        # Mock environment
        self.patch_environ = patch.dict(os.environ, {
            "USE_SNS": "true",
            "SNS_CAREGIVER_TOPIC_ARN": "arn:aws:sns:ap-south-2:123456789:caregiver-alerts"
        })
        self.patch_environ.start()

        # Mock boto3 client
        with patch('boto3.client') as mock_client:
            self.mock_sns = MagicMock()
            mock_client.return_value = self.mock_sns
            self.notifier = SNSNotification()

    def teardown_method(self):
        """Clean up patches."""
        self.patch_environ.stop()

    def test_notify_caregiver_with_sns(self):
        """Test that caregiver notification uses SNS."""
        user_id = "user1"
        message = "Test SNS alert"
        urgency = "medium"

        result = self.notifier.notify_caregiver(user_id, message, urgency)

        assert result is True
        self.mock_sns.publish.assert_called_once()
        call_args = self.mock_sns.publish.call_args
        assert call_args[1]["TopicArn"] == "arn:aws:sns:ap-south-2:123456789:caregiver-alerts"
        assert call_args[1]["Message"] == message
        assert f"CareBridge Alert - {user_id} ({urgency})" in call_args[1]["Subject"]

    def test_notify_caregiver_without_topic_arn(self):
        """Test behavior when topic ARN is not set."""
        # Remove topic ARN and set USE_SNS=true
        with patch.dict(os.environ, {"USE_SNS": "true"}, clear=False):
            # Ensure ARN is not set
            os.environ.pop('SNS_CAREGIVER_TOPIC_ARN', None)
            with patch('boto3.client') as mock_client:
                mock_sns = MagicMock()
                mock_client.return_value = mock_sns
                notifier = SNSNotification()

                result = notifier.notify_caregiver("user1", "test")

                assert result is False
                mock_sns.publish.assert_not_called()

    def test_sns_notification_fails_gracefully(self):
        """Test that SNS notification failure doesn't crash."""
        # Make publish raise an exception
        self.mock_sns.publish.side_effect = Exception("SNS error")

        result = self.notifier.notify_caregiver("user1", "test")

        assert result is False


class TestEmailNotification:
    """Test cases for EmailNotification class."""

    def setup_method(self):
        """Set up email notification for testing."""
        self.patch_environ = patch.dict(os.environ, {
            "USE_EMAIL": "true",
            "CAREGIVER_EMAIL": "caregiver@example.com",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@gmail.com",
            "SMTP_PASSWORD": "password"
        })
        self.patch_environ.start()

    def teardown_method(self):
        """Clean up patches."""
        self.patch_environ.stop()

    @patch('smtplib.SMTP')
    def test_notify_caregiver_with_email(self, mock_smtp):
        """Test that caregiver notification uses email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        from carebridge.notify import EmailNotification
        notifier = EmailNotification()

        user_id = "user1"
        message = "Test email alert"
        urgency = "high"

        result = notifier.notify_caregiver(user_id, message, urgency)

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_notify_caregiver_without_credentials(self, mock_smtp):
        """Test behavior when email credentials are not set."""
        with patch.dict(os.environ, {
            "USE_EMAIL": "true",
            "CAREGIVER_EMAIL": "caregiver@example.com"
        }, clear=True):
            from carebridge.notify import EmailNotification
            notifier = EmailNotification()

            result = notifier.notify_caregiver("user1", "test")

            assert result is False
            mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_email_notification_fails_gracefully(self, mock_smtp):
        """Test that email notification failure doesn't crash."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = Exception("Email error")

        from carebridge.notify import EmailNotification
        notifier = EmailNotification()

        result = notifier.notify_caregiver("user1", "test")

        assert result is False


class TestNotificationFactory:
    """Test cases for notification factory function."""

    def test_default_notification_is_console(self):
        """Test that default notification is console."""
        with patch.dict(os.environ, {}, clear=True):
            notifier = get_notifier()
            assert isinstance(notifier, ConsoleNotification)

    def test_sns_notification_when_enabled(self):
        """Test that SNS notification is used when enabled."""
        with patch.dict(os.environ, {"USE_SNS": "true"}, clear=False):
            with patch('boto3.client') as mock_client:
                mock_client.return_value = MagicMock()
                notifier = get_notifier()
                assert isinstance(notifier, SNSNotification)

    def test_email_notification_when_enabled(self):
        """Test that email notification is used when enabled."""
        with patch.dict(os.environ, {"USE_EMAIL": "true"}, clear=False):
            notifier = get_notifier()
            assert isinstance(notifier, EmailNotification)

    def test_sns_takes_precedence_over_email(self):
        """Test that SNS takes precedence when both are enabled."""
        with patch.dict(os.environ, {
            "USE_SNS": "true",
            "USE_EMAIL": "true"
        }, clear=False):
            with patch('boto3.client') as mock_client:
                mock_client.return_value = MagicMock()
                notifier = get_notifier()
                assert isinstance(notifier, SNSNotification)


# Need to import os for the tests
import os