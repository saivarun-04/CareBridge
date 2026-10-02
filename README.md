# CareBridge

**CareBridge** provides a synthetic‑data wellbeing check‑in assistant for elderly users and their caregivers.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Why CareBridge](#why-carebridge)
- [What it does](#what-it-does)
- [Demo story (3 minutes)](#demo-story-3-minutes)
- [Architecture](#architecture)
- [Project status](#project-status)
- [Honest limitations](#honest-limitations)
- [Getting started](#getting-started)
- [Mock vs live mode](#mock-vs-live-mode)
- [Project layout](#project-layout)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Contributing](#contributing)

---

## Project Overview

CareBridge is **not** a medical or diagnostic tool – it works only with synthetic data. The goal is to showcase:
1. **Adaptive communication** – the system changes tone based on response time and confusion.
2. **Escalation logic** – missed check‑ins trigger re‑prompts, caregiver alerts, and urgent alerts.
3. **Pattern detection** – a weekly summary is generated for caregivers.

All model calls go through `src/carebridge/llm.py`. Business logic stays free of MCP/AWS imports.

---

## Why CareBridge

Many older adults live independently while family members cannot always be available to check on them. A missed response does not necessarily mean something is wrong, but repeated changes in routines or unanswered check‑ins can sometimes deserve attention. CareBridge helps families stay connected without turning elderly care into constant monitoring.

---

## What it does

CareBridge provides three core capabilities:

- **Adaptive Communication:** Remembers user preferences and interaction patterns and adapts communication accordingly, including preferred name, check‑in timing, prompt length, repetition, and interaction style.
- **Intelligent Check‑Ins:** Manages scheduled check‑ins for user‑defined routines such as meals and other everyday wellbeing activities. Responses are recorded to build useful context over time.
- **Tiered Escalation:** A single missed check‑in does not immediately trigger an alert. CareBridge can re‑prompt the user, evaluate surrounding context and previous patterns, and notify a caregiver when repeated or meaningful deviations warrant attention.

The system is designed as a **wellbeing‑awareness and caregiver coordination tool**, not a medical diagnostic or emergency‑response system.

---

## Demo story (3 minutes)

The demo script `scripts/demo.py` runs a three‑minute story that:
1. Shows an elder check‑in with normal and slow/confused tones (adaptive tone).
2. Simulates a missed check‑in, re‑prompt, caregiver alert, and urgent alert (escalation flow).
3. Generates a weekly pattern summary for the caregiver.

All output is printed to the console. No real AWS resources are used.

Run with:
```bash
python scripts/demo.py
```
or via the Makefile target `make demo`.

---

## Architecture

```mermaid
flowchart TD
    subgraph WebViews
        Elder[Elder web view] -->|HTTP| MCPServer
        Caregiver[Caregiver dashboard] -->|HTTP| MCPServer
    end

    subgraph Backend
        MCPServer[MCP Server (FastAPI)] -->|invokes| Agent[Strands Agent]
        MCPServer -->|uses| LLM[llm.py]
        MCPServer -->|uses| Store[Storage (DynamoDB/Memory)]
        MCPServer -->|uses| Style[Style adaptation]
        MCPServer -->|uses| Escalation[Escalation manager]
        MCPServer -->|uses| Patterns[Pattern detector]
        MCPServer -->|uses| Notify[Notifier (SNS/SES/Console)]
        Scheduler[EventBridge Scheduler] -->|triggers| LambdaScheduler[Lambda scheduler]
        LambdaScheduler -->|invokes| MCPServer
    end

    subgraph AWS
        DynamoDB[(DynamoDB)]
        SNS[(SNS)]
        SES[(SES)]
        EventBridge[(EventBridge Scheduler)]
    end

    Store -->|reads/writes| DynamoDB
    Notify -->|sends| SNS
    Notify -->|sends| SES
    Style -.-> Agent
    Escalation -.-> Agent
    Patterns -.-> Agent
    LLM -.-> Agent
```

**Components marked with dashed lines are internal to the agent or server.**
- **Built:** MCP server, Strands agent, llm.py, style.py, escalation.py, patterns.py, store.py, notify.py, web views, demo script.
- **Not yet built:** CDK infrastructure (Stage 6), enriched web views with authentication (Stage 5).

---

## Project status

| Component                  | Status       |
|----------------------------|--------------|
| Core modules (llm, style, escalation, patterns, store, notify) | Done |
| MCP server (`server.py`)   | Done |
| Lambda MCP handler         | Done |
| Lambda scheduler handler   | Done |
| Strands agent (`agent.py`) | Done |
| Demo script (`scripts/demo.py`) | Done |
| Web views (`web/elder.html`, `web/caregiver.html`, `web/dev_server.py`) | Done |
| CDK infrastructure (`infra/`) | Planned |
| Final documentation & report | Planned |

All tests pass (84/84).

---

## Honest limitations

- **Alexa+ cannot start conversations through MCP**, so proactive check‑ins come from our own scheduler into a simulated Alexa+ view.
- Not a medical or diagnostic tool; synthetic data only.
- The Bedrock integration is built and tested in mock mode, and live model access is pending on the AWS account (new‑account restrictions). The demo may run in mock mode.
- The code is model‑agnostic: any Bedrock model that works with the Converse API can be set through `MODEL_ID`.

---

## Getting started

### Prerequisites
- Python 3.11+
- Git

### Setup (offline/mock mode – default)
```bash
# Clone the repo (if not already done)
git clone https://github.com/saivarun-04/CareBridge.git
cd CareBridge

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e .[dev]
```

### Run the test suite
```bash
pytest
```
or via Makefile:
```bash
make test
```

### Run the demo
```bash
python scripts/demo.py
```
or:
```bash
make demo
```

### Start the MCP server (required for demo and web views)
```bash
uvicorn carebridge.server:app --host 0.0.0.0 --port 8000
```

### Serve the web views (development)
```bash
python web/dev_server.py   # runs on http://localhost:8001
```
Make sure the MCP server is running on port 8000.

---

## Mock vs live mode

- **Offline/mock mode (default):**  
  `USE_MOCK_BEDROCK=true`, `STORE=memory`  
  Uses canned, profile‑aware replies and in‑memory storage. No AWS contact.

- **Live mode:**  
  Set `USE_MOCK_BEDROCK=false`, provide `MODEL_ID` (and optionally `MODEL_ID_STRONG`) and `AWS_REGION` via environment variables or a `.env` file.  
  The code will call the real Bedrock Converse API and use DynamoDB (if `STORE=dynamodb`).  
  **Live mode contacts AWS and can incur costs.**  
  Before any live action, follow the AWS permission protocol in `CLAUDE.md`.

---

## Project layout

```
CareBridge/
├── README.md
├── LICENSE                  (MIT)
├── CLAUDE.md
├── PROGRESS.md
├── CONTRIBUTING.md
├── FRICTION_LOG.md
├── Makefile
├── pyproject.toml           (package metadata, pytest pythonpath config, ruff config)
├── requirements.txt
├── .env.example
├── .gitignore
├── src/carebridge/
│   ├── __init__.py
│   ├── llm.py
│   ├── style.py
│   ├── escalation.py
│   ├── patterns.py
│   ├── store.py
│   ├── notify.py
│   ├── agent.py
│   ├── lambda_mcp.py
│   ├── lambda_scheduler.py
│   └── server.py
├── tests/                   (unit tests, imports from carebridge package)
├── docs/
│   ├── plan.md
│   └── product_story.md     (renamed from CareBridge_Devpost_Project_Story.md)
├── web/                     (static HTML/JS and dev server – created later)
├── infra/                   (CDK infrastructure – to be created)
└── scripts/                 (demo script – created later)
```

*Notes:*
- `debug_*.py` scratch scripts are ignored by `.gitignore`.
- The `web/`, `infra/`, and `scripts/` directories exist but may be expanded in later stages.

---

## Roadmap

- [x] Core modules, MCP server, Lambda handlers, Strands agent, demo, web views (offline, tests passing)
- [ ] CDK infrastructure (`infra/`): synthesize, optionally deploy (requires user approval)
- [ ] Final documentation, polishing, and project hand‑off

---

## Disclaimer

CareBridge is a wellbeing check‑in tool designed to support caregivers and promote awareness. It is **not** a substitute for medical advice, diagnosis, or emergency response. Always consult qualified healthcare professionals for medical concerns.

---

## License

This project is released under the MIT License (see `LICENSE`).

---

## Contributing

Please read `CONTRIBUTING.md` for details. In summary:
- Fork the repository, create a branch, make changes, ensure tests pass, submit a pull request.
- Run `make test` locally before submitting.
- Respect the offline‑first approach.
- Include the attribution line in commits:
  ```
  Co-Authored-By: Claude Code <noreply@anthropic.com>
  ```