# PROGRESS.md

## Current Stage & Next Action
- **Stage:** Core module bug fixing (identified failing tests).
- **Next Action:** Implement fixes in `llm.py`, `notify.py`, `style.py`, and `store.py`.

## Test Results (2026-10-02)
- **Total tests:** 61
- **Passed:** 52
- **Failed:** 7
  - `test_generate_strong_uses_strong_model` (llm.py) – model id placeholder used.
  - `test_notify_caregiver_prints_to_console`, `test_notify_user_prints_to_console` (notify.py) – multiple `print` calls.
  - `test_notify_caregiver_without_topic_arn` (notify.py) – SNS returns True when ARN missing.
  - `test_notify_caregiver_without_credentials` (notify.py) – Email returns True when SMTP credentials missing.
  - `test_dynamodb_storage_when_enabled` (store.py) – DynamoDB mock import error.
  - `test_respects_existing_communication_style` (style.py) – adaptation respects custom communication style.
- **Errors:** 2
  - `test_save_and_retrieve_checkin_dynamodb`, `test_save_and_retrieve_profile_dynamodb` (store.py) – Moto import error (`mock_dynamodb2` not available).

## Done (with dates)
- 2026-10-02: Created `CLAUDE.md` with full project rules and AWS permission protocol.
- 2026-10-02: Saved implementation plan at `C:\Users\gsaiv\.claude\plans\serialized-chasing-stonebraker.md`.

## In Progress
- Fixing failing unit tests (7 failures, 2 errors) across core modules.

## Known Failing Tests / Open Bugs
- `test_generate_strong_uses_strong_model` – model id placeholder used.
- Console notification tests – multiple `print` calls.
- SNS notification returns True when ARN missing.
- Email notification returns True when SMTP credentials missing.
- `style.py` adaptation respects custom communication style.
- `store.py` DynamoDB mock import (`mock_dynamodb2` missing) and missing `timedelta` import.

## Applied and Verified by a Passing Test
- None yet – awaiting bug fixes.

## Planned, Not Yet Applied
- Refactor console notifications to a single `print` for test capture.
- Adjust SNS and Email notifications to correctly fail when required env vars are absent.
- Fix `_should_adapt` logic to avoid unwanted adaptation for custom styles.
- Switch to `mock_dynamodb` (Moto v5) and add `timedelta` import for proper date filtering.

## Decisions Made & Why
- Updated `llm.py` to fetch model IDs from env at call time for correct tier handling (planned).
- Refactored console notifications to a single `print` for test capture (planned).
- Adjusted SNS and Email notifications to correctly fail when required env vars are absent (planned).
- Fixed `_should_adapt` logic to avoid unwanted adaptation for custom styles (planned).
- Switched to `mock_dynamodb` (Moto v5) and added `timedelta` import for proper date filtering (planned).

## AWS State
- **Deployed resources:** None (all mock).
- **Bedrock access:** Blocked; support case open.

## Open Questions for User
- None at this moment; proceed with the bug‑fix implementation.

---
*After each major change I will update this file.*