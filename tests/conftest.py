"""Pytest configuration for CareBridge tests."""

import pytest
from carebridge.store import reset_storage


@pytest.fixture(autouse=True)
def reset_storage_before_test():
    """Reset storage singleton before each test to prevent state leakage."""
    reset_storage()
    yield
