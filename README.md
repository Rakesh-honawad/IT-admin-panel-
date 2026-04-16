# IT Admin Agent

An AI agent that autonomously operates a web-based IT admin panel
using Claude + browser-use. Triggered via CLI or Slack slash command.

## What it does

- **Task 1 — Conditional Onboarding**: checks if a user exists,
  creates them if not, then assigns a software license
- **Task 2 — Security Lockdown**: revokes all sessions and resets
  MFA for a target user, confirms "Secured" status

## Stack

| Layer | Tech |
|-------|------|
| Admin panel | FastAPI + Jinja2 + SQLite |
| AI agent | Claude Sonnet via browser-use |
| Browser | Playwright (Chromium, headed) |
| Trigger | CLI or Slack `/ittask` slash command |
| Logging | Per-step screenshots + JSON report |
| Deploy | Railway + Docker |

## Quickstart

```bash
# Install deps
pip install -r requirements.txt
playwright install chromium

# Set up env
cp .env.example .env
# → fill in ANTHROPIC_API_KEY

# Seed database
python -m app.seed

# Start admin panel
uvicorn app.main:app --reload --port 8000

# Run demo tasks
python demo_tasks/task1_onboard.py
python demo_tasks/task2_lockdown.py
```

## Slack trigger