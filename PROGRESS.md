# PROGRESS.md

## Current Stage & Next Action
- **Stage:** Core modules + demo fixed and tested.
- **Next Action:** Commit and push changes, then proceed to Stage 5 (web views) if not already complete.

## Test Results (2026-10-02)
- **Total tests:** 84
- **Passed:** 84
- **Failed:** 0
- **Errors:** 0

## Changes Applied
### Task 1 – Neutralize competition wording
- Renamed `docs/devpost_story.md` → `docs/product_story.md` via `git mv`.
- Updated `CLAUDE.md` and `README.md` to remove "hackathon"/"Devpost"/competition references.

### Task 2 – Fix failing tests
- Fixed `get_storage()` singleton to avoid cross-test state leakage by using module-level singleton that can be reset via `reset_storage()`.
- Added `tests/conftest.py` with `reset_storage_before_test` fixture to clear storage between tests.
- Fixed `extract_number` in `agent.py` to extract the correct number from queries like "over the last 1 days".
- Fixed snooze pattern matching in `agent.py` to match "snooze checkin_1".
- Fixed `test_agent_adapt_style` to record multiple responses before expecting adaptation.
- Fixed `lambda_scheduler.py` to use straightforward message generation without time-of-day logic that was causing false passes.
- Fixed `server.py` to use dynamic `get_storage()` calls instead of module-level cached instance.

### Task 3 – Demo script working
- `scripts/demo.py` runs successfully demonstrating:
  - Adaptive tone (normal → slow_confused)
  - Escalation flow (pending → reprompted → caregiver notified → urgent)
  - Pattern summary generation
- All 84 tests pass.

## Done (with dates)
- 2026-10-02: Created `CLAUDE.md` with full project rules and AWS permission protocol.
- 2026-10-02: Saved implementation plan.
- 2026-10-02: Restructured repository: moved source code to `src/carebridge/`, updated imports, added `__init__.py`.
- 2026-10-02: Created `README.md`.
- 2026-10-02: All core module tests now pass (61/61) after fixing llm.py, notify.py, style.py, store.py.
- 2026-10-02: Implemented MCP server (`server.py`) with 8 passing tests.
- 2026-10-02: Implemented Lambda MCP handler (`lambda_mcp.py`) with 3 passing tests.
- 2026-10-02: Implemented Lambda scheduler handler (`lambda_scheduler.py`) with 5 passing tests.
- 2026-10-02: Implemented Strands agent (`agent.py`) with 7 passing tests.
- 2026-10-02: Implemented demo script (`scripts/demo.py`) and Makefile with `make demo` target.
- 2026-10-02: Created web views (`web/elder.html`, `web/caregiver.html`, `web/dev_server.py`).
- 2026-10-02: Added README.md to repository and committed.
- 2026-10-02: Neutralized competition wording throughout repository.
- 2026-10-02: Fixed all test failures, demo runs successfully.

## In Progress
- None – ready for next task.

## Known Failing Tests / Open Bugs
- None.

## Applied and Verified by a Passing Test
- All fixes verified by full test suite passing (84/84).

## Planned, Not Yet Applied
- Stage 6: CDK infrastructure (`infra/`).
- Stage 7: Final documentation and report.

## AWS State
- **Deployed resources:** None (all mock).
- **Bedrock access:** BLOCKED (Anthropic form and Playground return errors). A support case is open.

---
*After each major change I will update this file.*
