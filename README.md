# IT Admin Agent

An AI agent that accepts natural-language IT support requests and autonomously carries them out on a web-based admin panel — navigating, clicking, and filling forms exactly as a human would.

> **Live demo:** [it-admin-panel-production.up.railway.app](https://it-admin-panel-production.up.railway.app)

---

## What it does

You type a plain-English request. The agent opens a browser, reads the screen, and completes the task — no direct API calls, no DOM shortcuts, no scripted selectors.

**Task 1 — Conditional user onboarding**
```
"Onboard Jane Smith (jane.smith@company.com) as an Engineer
 and assign her a GitHub Enterprise license"
```
The agent checks if the user already exists → creates them if not → navigates to licenses → assigns the product → confirms success.

**Task 2 — Security lockdown**
```
"Lock down Bob Martinez — revoke all sessions and reset MFA"
```
The agent navigates to the security page → clicks Revoke Sessions → clicks Reset MFA → confirms the status badge shows "Secured".

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Trigger Layer                         │
│   CLI (demo_tasks/)  ·  Slack /ittask slash command     │
└────────────────────────┬────────────────────────────────┘
                         │ plain-English task prompt
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                           │
│                                                         │
│   browser-use  ──►  Groq LLM (llama-3.3-70b)          │
│                     (reads page → decides action)       │
│                                                         │
│   loop.py      ──►  AgentLogger (screenshots + JSON)   │
│   tasks.py     ──►  plain-English step prompts          │
│   policy.py    ──►  guardrails (domain, max steps)      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (Playwright / Chromium)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Admin Panel                           │
│                                                         │
│   FastAPI  ──►  Jinja2 templates  ──►  SQLite DB        │
│                                                         │
│   /users      create · disable · enable · search        │
│   /licenses   assign · revoke                           │
│   /security   revoke sessions · reset MFA               │
│   /audit      full action log                           │
└─────────────────────────────────────────────────────────┘
```

---

## Why these tools

| Decision | Choice | Reason |
|----------|--------|--------|
| Agent framework | `browser-use` | Wraps Playwright + LLM into a ready-made loop. Cuts agent code from ~200 lines to ~30. The agent reads the page visually — no DOM selectors. |
| LLM | Groq `llama-3.3-70b-versatile` | Free tier, fast inference, handles structured output correctly with browser-use. No credit card needed. |
| Admin panel | FastAPI + Jinja2 | Lightweight, fast to build, renders server-side HTML that the agent can read visually. SQLite keeps deploy simple — no external DB needed. |
| Browser | Playwright (Chromium, headed) | Fixed 1280×800 viewport keeps agent coordinates consistent across runs. Headed mode makes the Loom recording visible. |
| Slack trigger | `slack-bolt` + Socket Mode | Socket Mode means no ngrok or public URL needed locally. ~50 lines for a full slash command integration. |
| Deploy | Railway + Nixpacks | Auto-detects Python, zero Docker config needed. Connects directly to GitHub for auto-deploy on push. |
| Logging | Custom `AgentLogger` | Per-step screenshots + JSON report give a full audit trail of every action the agent took. |

---

## Project structure

```
it-admin-agent/
│
├── app/                        # FastAPI admin panel
│   ├── main.py                 # All routes (users, licenses, security, audit)
│   ├── models.py               # SQLModel table definitions
│   ├── database.py             # SQLite engine + session factory
│   ├── seed.py                 # Demo data seeder
│   └── templates/
│       ├── base.html           # Shared dark-theme layout + sidebar
│       ├── users.html          # User management page
│       ├── licenses.html       # License assignment page
│       ├── security.html       # Session + MFA controls
│       ├── audit.html          # Audit log page
│       └── user_detail.html    # Per-user detail + actions
│
├── agent/                      # AI agent layer
│   ├── loop.py                 # Core agent runner (browser-use + Groq)
│   ├── tasks.py                # Plain-English task prompt templates
│   ├── logger.py               # Step logger — screenshots + JSON report
│   └── policy.py               # Guardrails (domain allowlist, max steps)
│
├── demo_tasks/                 # Runnable demo scripts
│   ├── task1_onboard.py        # Conditional user onboarding
│   └── task2_lockdown.py       # Security lockdown
│
├── slack_bot/
│   └── bot.py                  # Slack /ittask slash command handler
│
├── logs/                       # Auto-created — one folder per agent run
│   └── task1_onboard_YYYYMMDD_HHMMSS/
│       ├── report.json         # Full audit trail
│       └── screenshots/        # step_01.png, step_02.png ...
│
├── data/                       # Auto-created — SQLite database
├── Procfile                    # Railway start command
├── nixpacks.toml               # Railway build config
├── requirements.txt            # All dependencies
└── .env                        # Local secrets (never committed)
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/Rakesh-honawad/IT-admin-panel-.git
cd IT-admin-panel-

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
playwright install chromium
```

### 2. Set up environment

Create `.env` in the project root:

```env
GROQ_API_KEY=gsk_your-key-here
BASE_URL=http://localhost:8000

# Optional — Slack bot
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) — no credit card required.

### 3. Seed the database and start the panel

```bash
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) — you'll see the admin panel with Alice, Bob, and Carol loaded.

### 4. Run the agent demos

```bash
# Terminal 1 — keep the server running
uvicorn app.main:app --reload --port 8000

# Terminal 2 — run the agent
python demo_tasks/task1_onboard.py
python demo_tasks/task2_lockdown.py
```

A Chromium window opens and the agent navigates the panel automatically.

---

## Demo tasks

### Task 1 — Conditional onboarding

```python
# Triggered with:
python demo_tasks/task1_onboard.py

# What the agent does:
# 1. Goes to /users — checks if jane.smith@company.com exists
# 2. If not → clicks "+ Add user" → fills form → submits
# 3. Goes to /licenses → clicks "+ Assign license"
# 4. Selects Jane Smith + GitHub Enterprise → assigns
# 5. Reports: "Onboarding complete. User created: yes. License assigned: GitHub Enterprise."
```

### Task 2 — Security lockdown

```python
# Triggered with:
python demo_tasks/task2_lockdown.py

# What the agent does:
# 1. Goes to /security — finds Bob Martinez
# 2. Clicks "Revoke sessions" → confirms sessions = 0
# 3. Clicks "Reset MFA" → confirms status = "Secured"
# 4. Reports: "Security lockdown complete. Sessions revoked: yes. MFA reset: yes."
```

---

## Slack trigger

Add the app to your Slack workspace and use:

```
/ittask onboard Jane Smith jane.smith@company.com Engineer
/ittask lockdown Bob Martinez 2
/ittask help
```

The bot sends an immediate acknowledgment, runs the agent in a background thread, and posts the result when done.

**Setup:**
1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add scopes: `commands`, `chat:write`, `files:write`
3. Enable Socket Mode → generate `xapp-` token
4. Create `/ittask` slash command
5. Install to workspace → copy `xoxb-` bot token
6. Add all three tokens to `.env`
7. Run: `python slack_bot/bot.py`

---

## Audit trail

Every agent run creates a timestamped folder in `logs/`:

```
logs/task1_onboard_20260418_115553/
├── report.json          # full run summary
└── screenshots/
    ├── step_01.png      # users page loaded
    ├── step_02.png      # user not found
    ├── step_03.png      # modal opened
    ├── step_04.png      # form filled
    ├── step_05.png      # user created confirmed
    ├── step_06.png      # licenses page
    ├── step_07.png      # license modal
    └── step_08.png      # license assigned confirmed
```

`report.json` example:
```json
{
  "run_id": "task1_onboard_20260418_115553",
  "task": "task1_onboard",
  "success": true,
  "duration_seconds": 119.44,
  "total_steps": 8,
  "final_result": "Onboarding complete for Jane Smith. User created: yes. License assigned: GitHub Enterprise.",
  "steps": [
    {
      "step": 1,
      "timestamp": "2026-04-18T11:55:53",
      "url": "https://it-admin-panel-production.up.railway.app/users",
      "action": "navigate to users page",
      "result": "page loaded",
      "screenshot": "logs/.../screenshots/step_01.png"
    }
  ]
}
```

---

## Guardrails

Defined in `agent/policy.py`:

| Guardrail | Value |
|-----------|-------|
| Allowed domains | `localhost:8000` or Railway URL only |
| Max steps per task | 30 |
| Task timeout | 120 seconds |
| Confirm before | Disable, Delete, Revoke actions |
| Vision | Disabled (Groq doesn't support image inputs) |

---

## Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set these environment variables in the Railway dashboard:

```
GROQ_API_KEY=gsk_...
BASE_URL=https://your-app.up.railway.app
```

Railway auto-deploys on every `git push` to `main`.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Admin panel | FastAPI 0.111 + Jinja2 + SQLModel |
| Database | SQLite (auto-created, seeded on startup) |
| Agent framework | browser-use 0.1.40 |
| LLM | Groq `llama-3.3-70b-versatile` (free) |
| Browser automation | Playwright + Chromium |
| Slack integration | slack-bolt + Socket Mode |
| Logging | Custom per-step screenshot logger |
| Deploy | Railway + Nixpacks (auto Python detection) |

---

## Key design decisions

**Why browser-use instead of raw Playwright?**
browser-use wraps the screenshot → LLM → action loop automatically. Without it, you'd write ~200 lines of manual loop code. With it, the agent is `await agent.run()`.

**Why Groq instead of OpenAI or Anthropic?**
Free tier with no credit card. `llama-3.3-70b-versatile` handles structured output correctly with browser-use and is fast enough for multi-step tasks.

**Why SQLite instead of Postgres?**
The admin panel is a demo target for the agent, not a production system. SQLite keeps the deploy to a single Railway service with zero configuration. The DB seeds itself on every cold start.

**Why `use_vision=False`?**
Groq's models don't support image inputs in the message history. Disabling vision makes the agent read the page as HTML text, which works perfectly for a well-structured admin panel.

**Why Socket Mode for Slack?**
No ngrok, no public URL, no webhook config. The bot connects outward to Slack — works locally and in production without any networking changes.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Free at console.groq.com |
| `BASE_URL` | ✅ Yes | `http://localhost:8000` or Railway URL |
| `SLACK_BOT_TOKEN` | Optional | `xoxb-...` from Slack app settings |
| `SLACK_SIGNING_SECRET` | Optional | From Slack app Basic Information |
| `SLACK_APP_TOKEN` | Optional | `xapp-...` from Socket Mode settings |

---

## Author

**Rakesh Honawad**
Built for the Decawork AI engineering challenge.
