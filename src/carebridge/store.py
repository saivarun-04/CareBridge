"""Storage interface with in-memory and DynamoDB implementations."""
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Import moto only for testing
try:
    import moto
    HAS_MOTO = True
except ImportError:
    HAS_MOTO = False


class StorageInterface(ABC):
    """Abstract interface for data storage."""

    @abstractmethod
    def save_checkin(self, user_id: str, checkin_type: str,
                    response: str, metadata: Dict) -> str:
        """Save a check-in record and return checkin_id."""
        pass

    @abstractmethod
    def get_checkins(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get check-in history for a user."""
        pass

    @abstractmethod
    def save_profile(self, user_id: str, profile: Dict) -> None:
        """Save user profile."""
        pass

    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile."""
        pass

    @abstractmethod
    def save_escalation(self, checkin_id: str, state: str) -> None:
        """Save escalation state."""
        pass

    @abstractmethod
    def get_escalation(self, checkin_id: str) -> Optional[str]:
        """Get escalation state."""
        pass


class InMemoryStorage(StorageInterface):
    """Simple in-memory storage for development and testing."""

    def __init__(self):
        self.checkins = {}  # user_id: list of checkins
        self.profiles = {}  # user_id: profile dict
        self.escalations = {}  # checkin_id: state
        self.next_checkin_id = 1

    def save_checkin(self, user_id: str, checkin_type: str,
                    response: str, metadata: Dict) -> str:
        """Save check-in to in-memory storage."""
        checkin_id = f"checkin_{self.next_checkin_id}"
        self.next_checkin_id += 1

        # Use timestamp from metadata if provided, otherwise use current time
        timestamp_str = metadata.get("timestamp", datetime.now().isoformat())

        checkin = {
            "checkin_id": checkin_id,
            "user_id": user_id,
            "type": checkin_type,
            "response": response,
            "metadata": metadata,
            "timestamp": timestamp_str
        }

        if user_id not in self.checkins:
            self.checkins[user_id] = []
        self.checkins[user_id].append(checkin)

        return checkin_id

    def get_checkins(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get check-in history for a user."""
        if user_id not in self.checkins:
            return []

        cutoff = datetime.now() - timedelta(days=days)
        result = []

        for checkin in self.checkins[user_id]:
            checkin_time = datetime.fromisoformat(checkin["timestamp"])
            if checkin_time >= cutoff:
                result.append(checkin)

        return result

    def save_profile(self, user_id: str, profile: Dict) -> None:
        """Save user profile."""
        self.profiles[user_id] = profile

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile."""
        return self.profiles.get(user_id)

    def save_escalation(self, checkin_id: str, state: str) -> None:
        """Save escalation state."""
        self.escalations[checkin_id] = state

    def get_escalation(self, checkin_id: str) -> Optional[str]:
        """Get escalation state."""
        return self.escalations.get(checkin_id)


class DynamoDBStorage(StorageInterface):
    """DynamoDB storage implementation."""

    def __init__(self):
        if os.getenv("STORE") != "dynamodb":
            raise RuntimeError("DynamoDB storage requires STORE=dynamodb environment variable")

        import boto3
        from moto import mock_aws
        # Start Moto mock for DynamoDB
        self.mock = mock_aws()
        self.mock.start()


        # Mock DynamoDB already initialized above





        self.dynamodb = boto3.resource("dynamodb", region_name="ap-south-2")

        # Create tables (in real app, these would be pre-created)
        self._create_tables()

    def _create_tables(self):
        """Create DynamoDB tables for development."""
        # Check-ins table
        try:
            self.dynamodb.create_table(
                TableName="CareBridge_Checkins",
                KeySchema=[{"AttributeName": "checkin_id", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "checkin_id", "AttributeType": "S"},
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"}
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "user_id_index",
                        "KeySchema": [
                            {"AttributeName": "user_id", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ],
                BillingMode="PAY_PER_REQUEST"
            )
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            pass  # Table already exists

        # Profiles table
        try:
            self.dynamodb.create_table(
                TableName="CareBridge_Profiles",
                KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST"
            )
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            pass  # Table already exists

        self.checkins_table = self.dynamodb.Table("CareBridge_Checkins")
        self.profiles_table = self.dynamodb.Table("CareBridge_Profiles")

    def save_checkin(self, user_id: str, checkin_type: str,
                    response: str, metadata: Dict) -> str:
        """Save check-in to DynamoDB."""
        checkin_id = f"checkin_{int(time.time())}_{user_id[:8]}"

        item = {
            "checkin_id": checkin_id,
            "user_id": user_id,
            "type": checkin_type,
            "response": response,
            "metadata": json.dumps(metadata),
            "timestamp": datetime.now().isoformat()
        }

        self.checkins_table.put_item(Item=item)
        return checkin_id

    def get_checkins(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get check-in history for a user from DynamoDB."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        response = self.checkins_table.query(
            IndexName="user_id_index",
            KeyConditionExpression="user_id = :uid AND timestamp >= :cutoff",
            ExpressionAttributeValues={
                ":uid": user_id,
                ":cutoff": cutoff
            }
        )

        checkins = []
        for item in response["Items"]:
            checkins.append({
                "checkin_id": item["checkin_id"],
                "user_id": item["user_id"],
                "type": item["type"],
                "response": item["response"],
                "metadata": json.loads(item["metadata"]),
                "timestamp": item["timestamp"]
            })

        return checkins

    def save_profile(self, user_id: str, profile: Dict) -> None:
        """Save user profile to DynamoDB."""
        self.profiles_table.put_item(
            Item={
                "user_id": user_id,
                "profile": json.dumps(profile),
                "updated_at": datetime.now().isoformat()
            }
        )

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from DynamoDB."""
        response = self.profiles_table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            return json.loads(response["Item"]["profile"])
        return None

    def save_escalation(self, checkin_id: str, state: str) -> None:
        """Save escalation state (simplified for demo)."""
        # In real implementation, this would use a separate table or GSI
        pass

    def get_escalation(self, checkin_id: str) -> Optional[str]:
        """Get escalation state (simplified for demo)."""
        # In real implementation, this would use a separate table or GSI
        return None


_storage_instance = None


def get_storage() -> StorageInterface:
    """Get storage instance based on environment (singleton)."""
    global _storage_instance
    if _storage_instance is None:
        if os.getenv("STORE") == "dynamodb":
            _storage_instance = DynamoDBStorage()
        else:
            _storage_instance = InMemoryStorage()
    return _storage_instance


def reset_storage():
    """Reset the storage singleton (useful for tests)."""
    global _storage_instance
    _storage_instance = None


# Need to import time and timedelta for DynamoDBStorage
import time
from datetime import timedelta