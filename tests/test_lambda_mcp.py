"""Unit tests for the Lambda MCP handler (src/carebridge/lambda_mcp.py)."""

import json
import os
import sys
sys.path.append('src')

from unittest.mock import patch

import boto3
from moto import mock_aws

# Set environment variables for DynamoDB and MCP server
os.environ["STORE"] = "dynamodb"
# Ensure no interference from existing env vars
os.environ.pop("SNS_CAREGIVER_TOPIC_ARN", None)
os.environ.pop("USE_SNS", None)
os.environ.pop("USE_EMAIL", None)
os.environ.pop("USE_MOCK_BEDROCK", None)
os.environ["USE_MOCK_BEDROCK"] = "true"  # keep mock mode for llm

from carebridge.lambda_mcp import handler as lambda_handler


def _create_api_gateway_v2_event(http_method, path, body=None):
    """Create a minimal API Gateway v2.0 event for HTTP API."""
    event = {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"Content-Type": "application/json"},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "api-id",
            "domainName": "id.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "id",
            "http": {
                "method": http_method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "test"
            },
            "routeKey": "$default",
            "stage": "$default",
        },
        "body": json.dumps(body) if body is not None else "",
        "isBase64Encoded": False,
    }
    return event


def test_lambda_mcp_log_checkin():
    """Test the MCP server via Lambda handler: log_checkin."""
    with mock_aws():
        event = _create_api_gateway_v2_event(
            "POST",
            "/mcp/log_checkin",
            {
                "user_id": "user1",
                "checkin_type": "medication",
                "response": "Yes",
                "metadata": {"taken": True},
            },
        )
        response = lambda_handler(event, {})
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "checkin_id" in body
        assert body["checkin_id"].startswith("checkin_")


def test_lambda_mcp_get_routine():
    """Test the MCP server via Lambda handler: get_routine."""
    with mock_aws():
        # First, add a check-in
        event = _create_api_gateway_v2_event(
            "POST",
            "/mcp/log_checkin",
            {
                "user_id": "user2",
                "checkin_type": "meal",
                "response": "Yes",
                "metadata": {},
            },
        )
        lambda_handler(event, {})

        # Now get routine
        event = _create_api_gateway_v2_event(
            "POST",
            "/mcp/get_routine",
            {"user_id": "user2", "days": 7},
        )
        response = lambda_handler(event, {})
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "checkins" in body
        assert len(body["checkins"]) == 1
        assert body["checkins"][0]["user_id"] == "user2"


def test_lambda_mcp_adapt_style():
    """Test the MCP server via Lambda handler: adapt_style."""
    with mock_aws():
        # First three calls to build up confusion
        event = _create_api_gateway_v2_event(
            "POST",
            "/mcp/adapt_style",
            {
                "user_id": "user3",
                "base_profile": {"preferred_name": "Alice", "communication": "normal"},
                "response_time": 100.0,
                "was_confused": True,
            },
        )
        for _ in range(3):
            lambda_handler(event, {})

        # Fourth call should now adapt to slow_confused
        event = _create_api_gateway_v2_event(
            "POST",
            "/mcp/adapt_style",
            {
                "user_id": "user3",
                "base_profile": {"preferred_name": "Alice", "communication": "normal"},
                "response_time": 100.0,
                "was_confused": True,
            },
        )
        response = lambda_handler(event, {})
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "adapted_profile" in body
        assert body["adapted_profile"]["communication"] == "slow_confused"