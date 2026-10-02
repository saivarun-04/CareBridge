"""MCP server for CareBridge exposing tools via Streamable HTTP (stateless)."""

import json
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from carebridge.llm import generate, USE_MOCK
from carebridge.style import style_manager
from carebridge.escalation import escalation_manager
from carebridge.patterns import pattern_detector
from carebridge.store import get_storage
from carebridge.notify import get_notifier

app = FastAPI(title="CareBridge MCP Server", version="0.1.0")

# In-memory instances (already created as singletons in the modules)
# NOTE: storage is resolved dynamically per-request to support test isolation.
notifier = get_notifier()


@app.post("/mcp/log_checkin")
async def log_checkin(payload: Dict[str, Any]) -> JSONResponse:
    """
    Log a check-in for a user.
    Expected payload: {
        "user_id": str,
        "checkin_type": str,  # e.g., "medication", "meal", "mood", "general"
        "response": str,
        "metadata": dict (optional)
    }
    Returns: {"checkin_id": str}
    """
    try:
        user_id = payload["user_id"]
        checkin_type = payload["checkin_type"]
        response = payload["response"]
        metadata = payload.get("metadata", {})
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    from carebridge.store import get_storage
    store = get_storage()
    checkin_id = store.save_checkin(user_id, checkin_type, response, metadata)
    # Also add to pattern detector for weekly summaries
    from datetime import datetime
    pattern_detector.add_checkin(
        user_id=user_id,
        checkin_type=checkin_type,
        response=response,
        timestamp=datetime.now(),
        metadata=metadata,
    )
    return JSONResponse(content={"checkin_id": checkin_id})


@app.post("/mcp/get_routine")
async def get_routine(payload: Dict[str, Any]) -> JSONResponse:
    """
    Get the routine (check-in history) for a user.
    Expected payload: {
        "user_id": str,
        "days": int (optional, default 7)
    }
    Returns: {"checkins": list}
    """
    try:
        user_id = payload["user_id"]
        days = payload.get("days", 7)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    from carebridge.store import get_storage
    store = get_storage()
    checkins = store.get_checkins(user_id, days=days)
    return JSONResponse(content={"checkins": checkins})


@app.post("/mcp/adapt_style")
async def adapt_style(payload: Dict[str, Any]) -> JSONResponse:
    """
    Adapt communication style based on recent responses.
    Expected payload: {
        "user_id": str,
        "base_profile": dict,
        "response_time": float,
        "was_confused": bool (optional, default False)
    }
    Returns: {"adapted_profile": dict}
    """
    try:
        user_id = payload["user_id"]
        base_profile = payload["base_profile"]
        response_time = payload["response_time"]
        was_confused = payload.get("was_confused", False)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    # Record the response for style adaptation
    style_manager.record_response(user_id, response_time, was_confused)
    adapted = style_manager.get_adapted_style(user_id, base_profile)
    return JSONResponse(content={"adapted_profile": adapted})


@app.post("/mcp/get_pattern_summary")
async def get_pattern_summary(payload: Dict[str, Any]) -> JSONResponse:
    """
    Get weekly pattern summary for a user.
    Expected payload: {
        "user_id": str,
        "days": int (optional, default 7)
    }
    Returns: {"patterns": list, "summary": str, "total_checkins": int, "period_days": int}
    """
    try:
        user_id = payload["user_id"]
        days = payload.get("days", 7)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    result = pattern_detector.analyze_patterns(user_id, days=days)
    return JSONResponse(content=result)


@app.post("/mcp/notify_caregiver")
async def notify_caregiver(payload: Dict[str, Any]) -> JSONResponse:
    """
    Notify caregiver about a user.
    Expected payload: {
        "user_id": str,
        "message": str,
        "urgency": str (optional, default "normal")
    }
    Returns: {"success": bool}
    """
    try:
        user_id = payload["user_id"]
        message = payload["message"]
        urgency = payload.get("urgency", "normal")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    success = notifier.notify_caregiver(user_id, message, urgency)
    return JSONResponse(content={"success": success})


@app.post("/mcp/snooze_or_ack")
async def snooze_or_ack(payload: Dict[str, Any]) -> JSONResponse:
    """
    Snooze or acknowledge a check-in.
    Expected payload: {
        "checkin_id": str,
        "action": str,  # "ack" or "snooze"
        "snooze_duration": int (optional, default 3600 seconds)
    }
    Returns: {"success": bool}
    """
    try:
        checkin_id = payload["checkin_id"]
        action = payload["action"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")

    if action == "ack":
        escalation_manager.acknowledge(checkin_id)
        return JSONResponse(content={"success": True})
    elif action == "snooze":
        duration = payload.get("snooze_duration", 3600)
        escalation_manager.snooze(checkin_id, duration)
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="Action must be 'ack' or 'snooze'")


def main() -> None:
    """Run the server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()