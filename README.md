# CareBridge

**CareBridge** provides a synthetic‑data wellbeing check‑in assistant for elderly users and their caregivers.  It demonstrates:
- MCP (Multi‑Channel Provider) tools for logging check‑ins, retrieving routines, adapting communication style, and summarising patterns.
- A Strands‑based agent that routes natural‑language intents to the MCP tools.
- A demo script (`scripts/demo.py`) that runs a 3‑minute story showing adaptive tone, escalation, and weekly summaries.
- Simple static web views (`web/elder.html`, `web/caregiver.html`) and a development server (`web/dev_server.py`).
- A fully mocked AWS environment (DynamoDB, SNS/SES, EventBridge) using **Moto** and `USE_MOCK_BEDROCK=true` for offline development.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Getting Started (offline)](#getting-started-offline)
- [Running the Demo](#running-the-demo)
- [Web Views (development)](#web-views-development)
- [Running Tests](#running-tests)
- [Next Stages](#next-stages)
- [AWS Permission Protocol](#aws-permission-protocol)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

CareBridge is **not** a medical or diagnostic tool – it works only with synthetic data.  The goal is to showcase:
1. **Adaptive communication** – the system changes tone based on response time and confusion.
2. **Escalation logic** – missed check‑ins trigger re‑prompts, caregiver alerts, and urgent alerts.
3. **Pattern detection** – a weekly summary is generated for caregivers.

All model calls go through `src/carebridge/llm.py`.  Business logic stays free of MCP/AWS imports.

---

## Architecture

```
src/carebridge/
├── agent.py            # Strands agent (rule‑based for demo)
├── escalation.py       # Tiered escalation state machine
├── llm.py              # Mock/real Bedrock wrapper
├── notify.py           # Console / SNS / Email notifier (mock mode prints only)
├── patterns.py         # Pattern detection & summary
├── store.py            # In‑memory or DynamoDB storage (mocked via Moto)
├── style.py            # Adaptive style manager
└── server.py           # FastAPI MCP server exposing 6 tools
```

The demo script uses these modules directly; the web views call the same MCP endpoints via HTTP.

---

## Getting Started (offline)

1. **Clone the repo** (already done).
2. **Install dependencies**
   ```bash
   make install   # pip install -r requirements.txt
   ```
3. **Set environment for mock mode** (default is fine):
   ```bash
   export USE_MOCK_BEDROCK=true
   export STORE=memory
   ```
4. **Run the MCP server** (required for the demo and web views):
   ```bash
   uvicorn carebridge.server:app --host 0.0.0.0 --port 8000
   ```

---

## Running the Demo

The demo script `scripts/demo.py` runs a three‑minute story that:
1. Shows an elder check‑in with normal and slow/confused tones.
2. Simulates a missed check‑in, re‑prompt, caregiver alert, and urgent alert.
3. Generates a weekly pattern summary for the caregiver.

```bash
make demo   # or: python scripts/demo.py
```
All output is printed to the console.  No real AWS resources are used.

---

## Web Views (development)

Two static HTML pages are provided:
- **Elder view** (`web/elder.html`) – a button triggers a mock `log_checkin` call.
- **Caregiver view** (`web/caregiver.html`) – a button fetches a weekly pattern summary.

To serve them locally:
```bash
python web/dev_server.py   # runs on http://localhost:8001
```
Make sure the MCP server is running on port 8000 (see above).

---

## Running Tests

All tests are written with `pytest`.  They use the mock storage and mock Bedrock.
```bash
make test   # runs pytest -q
```
The full suite should pass (77 tests as of the latest commit).

---

## Next Stages

- **Stage 5** – Build richer web views, add authentication, and connect to the MCP server.
- **Stage 6** – Define CDK infrastructure (`infra/`), synthesize, and optionally deploy.
- **Stage 7** – Final documentation, polishing, and project hand‑off.

---

## AWS Permission Protocol

The repository follows the strict AWS permission protocol defined in `CLAUDE.md`.  All commands are run in **offline/mock mode** by default.  Any operation that would contact real AWS services (e.g., `cdk deploy`, real Bedrock calls) requires explicit user approval, a summary of resources, cost estimate, and a teardown plan.

---

## Contributing

Please read `CLAUDE.md` for the full set of project rules and the Git permission rule.  Contributions should:
- Run `make test` locally before submitting PRs.
- Respect the offline‑first approach.
- Follow the commit attribution line:
  ```
  Co-Authored-By: Claude Code <noreply@anthropic.com>
  ```

---

## License

This project is released under the MIT License (see `LICENSE`).
