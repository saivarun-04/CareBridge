# PROGRESS.md

## Current Stage & Next Action
- **Stage:** Stage 4 – Demo script (`scripts/demo.py`) implemented and tested.
- **Next Action:** Implement Stage 5 – web views (`web/elder.html`, `web/caregiver.html`, `dev_server.py`).

## Test Results (2026-10-02)
- **Total tests:** 77 (core 61 + server 8 + Lambda handlers 3+5 = 77)
- **Passed:** 77
- **Failed:** 0
- **Errors:** 0

## Done (with dates)
- 2026-10-02: Created `CLAUDE.md` with full project rules and AWS permission protocol.
- 2026-10-02: Saved implementation plan at `C:\Users\gsaiv\.claude\plans\serialized-chasing-stonebraker.md`.
- 2026-10-02: Restructured repository: moved source code to `src/carebridge/`, updated imports, added `__init__.py`.
- 2026-10-02: Created `README.md` with project overview, architecture, status, limitations, getting started, layout, roadmap, and disclaimer.
- 2026-10-02: All core module tests now pass (61/61) after fixing:
  - `llm.py`: fetch model IDs from environment at call time.
  - `notify.py`: console notifications single print, SNS/Email return False when missing config.
  - `style.py`: `_should_adapt` only considers time_since_adapt if an adaptation has occurred.
  - `store.py`: switched to `mock_aws`, fixed DynamoDB table schema (removed unused timestamp from AttributeDefinitions), added missing `timedelta` import.
- 2026-10-02: Implemented MCP server (`src/carebridge/server.py`) exposing the six tools via Streamable HTTP (FastAPI).
- 2026-10-02: Wrote unit tests for the MCP server (`tests/test_server.py`) and they pass (8/8).
- 2026-10-02: Implemented Lambda MCP handler (`src/carebridge/lambda_mcp.py`) using Mangum to wrap the FastAPI app.
- 2026-10-02: Wrote unit tests for the Lambda MCP handler (`tests/test_lambda_mcp.py`) and they pass (3/3).
- 2026-10-02: Implemented Lambda scheduler handler (`src/carebridge/lambda_scheduler.py`) to start a check‑in for a user.
- 2026-10-02: Wrote unit tests for the Lambda scheduler handler (`tests/test_lambda_scheduler.py`) and they pass (5/5).
- 2026-10-02: Implemented Strands agent (`src/carebridge/agent.py`) that uses the MCP tools, with a stubbed model for offline mode and a documented flag to switch to real Bedrock.
- 2026-10-02: Wrote unit tests for the Strands agent (`tests/test_agent.py`) and they pass (7/7).
- 2026-10-02: Implemented demo script (`scripts/demo.py`) that runs a 3‑minute story demonstrating adaptive tone, missed check‑in escalation, and weekly pattern summary, all in mock mode.
- 2026-10-02: Added `make demo` target in the Makefile.

## In Progress
- None – ready to start Stage 5.

## Known Failing Tests / Open Bugs
- None.

## Applied and Verified by a Passing Test
- All fixes and implementations listed above have been applied and verified by the full test suite passing.

## Planned, Not Yet Applied
- Implement web views (`web/elder.html`, `web/caregiver.html`, `dev_server.py`).
- Implement CDK infrastructure (`infra/`).
- Final documentation and report.

## AWS State
- **Deployed resources:** None (all mock).
- **Bedrock access:** BLOCKED (Anthropic form and Playground return errors). A support case is open.

---
*After each major change I will update this file.*