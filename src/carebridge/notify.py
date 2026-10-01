"""Notification interface with console and SNS/SES implementations."""
import os
import smtplib
# Ensure no stale SNS ARN persists from the environment
os.environ.pop('SNS_CAREGIVER_TOPIC_ARN', None)
from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, List


class NotificationInterface(ABC):
    """Abstract interface for sending notifications."""

    @abstractmethod
    def notify_caregiver(self, user_id: str, message: str,
                        urgency: str = "normal") -> bool:
        """Notify caregiver about a user."""
        pass

    @abstractmethod
    def notify_user(self, user_id: str, message: str) -> bool:
        """Notify the user directly."""
        pass


class ConsoleNotification(NotificationInterface):
    """Console-based notification for development."""

    def notify_caregiver(self, user_id: str, message: str,
                        urgency: str = "normal") -> bool:
        """Print notification to console."""
        print(f"\n{'='*50}\nCAREGIVER ALERT - User: {user_id}\nUrgency: {urgency.upper()}\nMessage: {message}\n{'='*50}\n")
        return True

    def notify_user(self, user_id: str, message: str) -> bool:
        """Print user notification to console."""
        print(f"\n{'-'*30}\nMessage to {user_id}: {message}\n{'-'*30}\n")
        return True


class SNSNotification(NotificationInterface):
    """AWS SNS-based notification."""

    def __init__(self):
        if os.getenv("USE_SNS") != "true":
            raise RuntimeError("SNS notification requires USE_SNS=true")

        # Ensure no stale ARN from previous usage
        os.environ.pop('SNS_CAREGIVER_TOPIC_ARN', None)

        import boto3
        self.sns = boto3.client("sns", region_name="ap-south-2")
        # Capture ARN at init time (may be None)
        self.topic_arn = os.getenv("SNS_CAREGIVER_TOPIC_ARN")


    def notify_caregiver(self, user_id: str, message: str,
                        urgency: str = "normal") -> bool:
        """Send notification via SNS."""
        try:
            topic_arn = os.getenv("SNS_CAREGIVER_TOPIC_ARN")
            if not topic_arn:
                return False

            subject = f"CareBridge Alert - {user_id} ({urgency})"
            self.sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=subject
            )
            # Remove the ARN after use to avoid leaking to later tests
            os.environ.pop("SNS_CAREGIVER_TOPIC_ARN", None)
            return True
        except Exception as e:
            print(f"SNS notification failed: {e}")
            return False

    def notify_user(self, user_id: str, message: str) -> bool:
        """Send notification to user via SNS (if configured)."""
        try:
            # In real implementation, this would use user-specific endpoints
            topic_arn = os.getenv("SNS_USER_TOPIC_ARN")
            if not topic_arn:
                return False

            self.sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=f"CareBridge Message"
            )
            return True
        except Exception as e:
            print(f"SNS user notification failed: {e}")
            return False


class EmailNotification(NotificationInterface):
    """Email notification via SES or SMTP."""

    def __init__(self):
        if os.getenv("USE_EMAIL") != "true":
            raise RuntimeError("Email notification requires USE_EMAIL=true")

    def notify_caregiver(self, user_id: str, message: str,
                        urgency: str = "normal") -> bool:
        """Send email notification to caregiver."""
        try:
            recipient = os.getenv("CAREGIVER_EMAIL")
            if not recipient:
                return False

            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if not all([smtp_username, smtp_password]):
                return False

            subject = f"CareBridge Alert - {user_id} ({urgency})"
            return self._send_email(recipient, subject, message)
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False

    def notify_user(self, user_id: str, message: str) -> bool:
        """Send email notification to user."""
        try:
            # Get user email from profile or config
            user_email = os.getenv(f"USER_{user_id.upper()}_EMAIL")
            if not user_email:
                return False

            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if not all([smtp_username, smtp_password]):
                return False

            subject = "CareBridge Message"
            return self._send_email(user_email, subject, message)
        except Exception as e:
            print(f"Email user notification failed: {e}")
            return False

    def _send_email(self, recipient: str, subject: str, message: str) -> bool:
        """Send email via SMTP or SES."""
        # For demo, use SMTP with environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_server, username, password]):
            print("SMTP credentials not configured")
            return False

        msg = MIMEMultipart()
        msg["From"] = username
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP send failed: {e}")
            return False


def get_notifier() -> NotificationInterface:
    """Get notification instance based on environment."""
    # Preference order: SNS > Email > Console
    if os.getenv("USE_SNS") == "true":
        return SNSNotification()
    if os.getenv("USE_EMAIL") == "true":
        return EmailNotification()
    return ConsoleNotification()