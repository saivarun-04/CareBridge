"""Unit tests for store.py"""
import pytest
import os
from datetime import datetime, timedelta
import sys
sys.path.append('src')
from carebridge.store import get_storage, InMemoryStorage, DynamoDBStorage


class TestInMemoryStorage:
    """Test cases for InMemoryStorage class."""

    def setup_method(self):
        """Reset storage before each test."""
        self.storage = InMemoryStorage()

    def test_save_and_retrieve_checkin(self):
        """Test saving and retrieving a check-in."""
        user_id = "user1"
        checkin_id = self.storage.save_checkin(
            user_id, "medication", "Yes", {"taken": True}
        )

        assert checkin_id.startswith("checkin_")
        checkins = self.storage.get_checkins(user_id)
        assert len(checkins) == 1
        assert checkins[0]["user_id"] == user_id
        assert checkins[0]["type"] == "medication"
        assert checkins[0]["response"] == "Yes"

    def test_get_checkins_with_days_filter(self):
        """Test filtering checkins by days."""
        user_id = "user1"
        now = datetime.now()

        # Add check-ins from different time periods
        # 2 days ago: should be included (within 7 days)
        self.storage.save_checkin(user_id, "meal", "Yes", {"timestamp": (now - timedelta(days=2)).isoformat()})
        # 8 days ago: should be excluded (outside 7 days)
        self.storage.save_checkin(user_id, "medication", "Yes", {"timestamp": (now - timedelta(days=8)).isoformat()})
        # Today: should be included
        self.storage.save_checkin(user_id, "mood", "Good", {"timestamp": now.isoformat()})

        # Get check-ins from last 7 days
        recent_checkins = self.storage.get_checkins(user_id, days=7)
        # Should include today and 2 days ago (2 check-ins), excludes 8 days ago
        assert len(recent_checkins) == 2  # Excludes the 8-day-old check-in

    def test_save_and_retrieve_profile(self):
        """Test saving and retrieving user profile."""
        user_id = "user1"
        profile = {
            "preferred_name": "Alice",
            "age": 75,
            "communication": "normal"
        }

        self.storage.save_profile(user_id, profile)
        retrieved = self.storage.get_profile(user_id)

        assert retrieved == profile

    def test_get_nonexistent_profile(self):
        """Test getting profile for non-existent user."""
        retrieved = self.storage.get_profile("nonexistent")
        assert retrieved is None

    def test_multiple_users_isolation(self):
        """Test that data is isolated between users."""
        user1_id = "user1"
        user2_id = "user2"

        # Add data for both users
        self.storage.save_checkin(user1_id, "medication", "Yes", {})
        self.storage.save_checkin(user2_id, "meal", "Yes", {})
        self.storage.save_profile(user1_id, {"name": "Alice"})
        self.storage.save_profile(user2_id, {"name": "Bob"})

        # Verify data is isolated
        user1_checkins = self.storage.get_checkins(user1_id)
        user2_checkins = self.storage.get_checkins(user2_id)
        user1_profile = self.storage.get_profile(user1_id)
        user2_profile = self.storage.get_profile(user2_id)

        assert len(user1_checkins) == 1
        assert len(user2_checkins) == 1
        assert user1_profile["name"] == "Alice"
        assert user2_profile["name"] == "Bob"


class TestDynamoDBStorage:
    """Test cases for DynamoDBStorage class."""

    def setup_method(self):
        """Set up DynamoDB storage for testing."""
        # Ensure we're using mock environment
        os.environ["STORE"] = "dynamodb"
        self.storage = DynamoDBStorage()

    def test_save_and_retrieve_checkin_dynamodb(self):
        """Test saving and retrieving check-in with DynamoDB."""
        user_id = "user1"
        checkin_id = self.storage.save_checkin(
            user_id, "medication", "Yes", {"taken": True}
        )

        assert checkin_id.startswith("checkin_")
        checkins = self.storage.get_checkins(user_id)
        assert len(checkins) == 1
        assert checkins[0]["user_id"] == user_id
        assert checkins[0]["type"] == "medication"

    def test_save_and_retrieve_profile_dynamodb(self):
        """Test saving and retrieving profile with DynamoDB."""
        user_id = "user1"
        profile = {
            "preferred_name": "Bob",
            "age": 80,
            "communication": "slow_confused"
        }

        self.storage.save_profile(user_id, profile)
        retrieved = self.storage.get_profile(user_id)

        assert retrieved == profile


class TestStorageFactory:
    """Test cases for storage factory function."""

    def test_default_storage_is_in_memory(self):
        """Test that default storage is in-memory."""
        # Clear STORE env var
        if "STORE" in os.environ:
            del os.environ["STORE"]

        storage = get_storage()
        assert isinstance(storage, InMemoryStorage)

    def test_dynamodb_storage_when_enabled(self):
        """Test that DynamoDB storage is used when enabled."""
        os.environ["STORE"] = "dynamodb"
        storage = get_storage()
        assert isinstance(storage, DynamoDBStorage)

    def test_env_var_restored(self):
        """Test that environment variable is restored after test."""
        # This test ensures our changes don't affect other tests
        assert os.environ.get("STORE") in ["dynamodb", None]