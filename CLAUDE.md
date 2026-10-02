# CLAUDE.md

## Project Overview
- **Project:** CareBridge – a wellbeing check‑in assistant for elderly people and caregivers.
- **Purpose:** A wellbeing check‑in assistant for elderly people and caregivers. It is **not** a medical or diagnostic tool and uses **synthetic data only**.
- **Stack:** Python 3.11+, MCP server (Streamable HTTP, stateless) on Lambda, Strands SDK + Amazon Bedrock, DynamoDB, EventBridge Scheduler, SNS/SES, AWS CDK (Python), two static web views (elder, caregiver).
- **MCP Tools:** `log_checkin`, `get_routine`, `adapt_style`, `get_pattern_summary`, `notify_caregiver`, `snooze_or_ack`.

## Architecture Rules
- **All model calls** go through `llm.py` only.
- **Business logic** stays free of MCP and AWS imports.
- **Default (offline) mode:** `USE_MOCK_BEDROCK=true`, `STORE=memory`.
- `MODEL_ID` and `MODEL_ID_STRONG` are taken from environment variables; they are **not** hard‑coded.
- **Honest limitation:** Alexa+ cannot start conversations through MCP, so proactive check‑ins come from our own scheduler into a simulated Alexa+ view.

## AWS PERMISSION PROTOCOL (full)
- **Default:** Offline/mock mode. All local commands (`pytest`, `ruff`, `cdk synth`, local servers, Moto tests) are free to run.
- **Before any AWS contact** (e.g., `cdk deploy`, `cdk destroy`, `aws` CLI, real Bedrock calls, any boto3 call to a live endpoint, or any test with `USE_MOCK_BEDROCK=false`), **STOP** and ask the user, providing:
  1. Exact command or code path.
  2. AWS resources it will create or call.
  3. Estimated cost (near zero or may cost money).
  4. Prerequisites (credentials, region, `MODEL_ID`).
  5. How to undo/tear down.
- The user must reply with an explicit **yes** for that single action; a yes does **not** cover future actions.
- Never read, print, create, or store AWS credentials or secrets.
- Never use the root user; request elevated permissions only if needed.
- **Live Bedrock calls:** Do **not** attempt until the user supplies a working `MODEL_ID` and confirms access. On failure, log the error in `FRICTION_LOG.md` and revert to mock mode.
- After any approved deploy, remind the user to tear it down and provide the destroy command. Keep a running list of "resources currently deployed".
- When offline work is finished, propose a short **live validation plan** listing AWS steps, costs, and teardown. Await user approval step‑by‑step.

## Account Facts
- **Region:** `ap-south-2` (no longer a hard assumption; AWS_REGION stays an environment variable).
- **Bedrock model access:** Anthropic (Claude) model access denied for new account with little usage history (AWS Support case 179077398900418). Advised to reapply after next billing cycle. Continuing in mock mode; will test Amazon Nova and other Regions (us-east-1, us-west-2) separately.

## Working Rules
- Inspect installed packages before using their APIs; adapt code if signatures differ.
- Run the full test suite after each stage; fix all failures before proceeding.
- Keep credit usage near zero: cheap models for routine messages, `MODEL_ID_STRONG` only for strong tier, DynamoDB on‑demand, no always‑on services.
- No extra features beyond the approved plan.

## Session Routine
- **Start of each session:** Read `PROGRESS.md` and announce where we left off.
- **End of each session & after every finished stage:** Update `PROGRESS.md` with the latest status.

## Git permission rule (new)
- You may run read‑only git commands freely: `git status`, `git diff`, `git log`, `git branch`.
- **Before `git add`, `git commit` or `git push`**, STOP and ask the user. Show:
  1. The list of files that will be included.
  2. The exact commit message.
  3. The exact commands.
  Wait for an explicit **yes**. One **yes** covers only that single commit and push.
- Use `git mv` for moves so history is kept.
- Never force‑push, never rewrite history, never commit `.env`, keys, `__pycache__`, or `debug_*.py` files.

