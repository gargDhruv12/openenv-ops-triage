---
title: Ops Triage Env
emoji: 👀
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
---

# Ops triage (OpenEnv)

Small OpenEnv benchmark around **incident triage**: you get a ticket, dig for missing context, skim runbooks, draft something you’d actually paste in Slack, then lock in owner + severity. Nothing fancy—just closer to on-call work than picking moves in a gridworld.

Built for the Meta × Scaler OpenEnv track: typed `step`/`reset`, Docker Space, and a root `inference.py` that talks to the hosted LLM proxy like the sample.

## What it does

- Ticket fields are partly **hidden** until you `inspect_ticket` the right keys.
- Runbook search is a **substring match**—you can whiff and still get a default hit.
- Rewards aren’t only at the end: small nudges for useful inspection, runbook use, draft quality; slaps for garbage or repeat junk.
- Three episodes in `tasks.py`: **easy / medium / hard** (payment noise → regional login pain → ugly multi-tenant data mess).

## Actions (`models.py` → `OpsTriageAction`)

| Field | Notes |
|-------|--------|
| `action_type` | `inspect_ticket`, `lookup_runbook`, `draft_resolution`, `finalize` |
| `focus_field` | For inspect: which ticket field |
| `query` | For runbook search |
| `resolution_text` | Draft or final text |
| `proposed_owner` / `proposed_severity` | Your call |

## Observations (`OpsTriageObservation`)

| Field | Notes |
|-------|--------|
| `task_name`, `instruction` | What you’re solving |
| `visible_ticket` | What you’re allowed to see right now |
| `discovered_runbooks` | What lookup returned |
| `progress`, `checklist` | Rough completion signal |
| `message`, `last_action_error` | Feedback / why an action failed |
| `done`, `reward` | Episode over? last step reward |

## Tasks

| Id | Level | One-liner |
|----|-------|-----------|
| `payment-webhook-timeout-easy` | easy | Webhook pain, one merchant, smaller blast radius |
| `login-outage-regional-medium` | medium | Identity deploy, chunk of users unhappy |
| `data-corruption-multi-tenant-hard` | hard | Enterprise-y data integrity; more keywords and sharper comms expected |

Gold labels and required phrases live next to each task in `tasks.py`.

## Grader

`graders.py` — all string math, **deterministic**, same input → same score:

- 35% owner string match  
- 30% severity match  
- 35% share of required keywords in the resolution text  

Final number gets nudged to sit **just inside** 0 and 1 (not exactly 0.0 or 1.0) because the auto-grader was picky about endpoints. Doesn’t change ordering meaningfully.

Sanity check:

```bash
python scripts/task_grader_check.py
```

Oracle-style answers land around **~0.99** per task after that nudge.

## Baseline (`inference.py`)

Runs the env in Docker, calls the model through **`OpenAI`** with **`API_BASE_URL`** + **`API_KEY`** when the platform sets them (local hack: `HF_TOKEN` still works). Stdout lines must look like:

`[START] …` → `[STEP] …` → `[END] …`

Per-task score in `[END]` comes from summed positive rewards, normalized, then the same inner (0,1) clip. **Your mileage varies** with model and whether Docker actually comes up—don’t expect identical digits to my laptop.

**Baseline performance scores (reference):** run `python scripts/task_grader_check.py` with oracle owner/severity and all required keywords in the resolution text. On my side that reports about **0.99** composite per task (after the score nudge). LLM-driven `inference.py` runs won’t match that unless the model nails every field and keyword.

## Run it

**Server**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\python -m pip install ...
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

**Baseline**

```bash
python inference.py
```

**Docker**

```bash
docker build -t openenv-ops-triage:latest .
docker run --rm -p 8000:8000 openenv-ops-triage:latest
```

HF Space uses **`PORT`**; Dockerfile listens on `${PORT:-7860}`.

**Validate (if you have the CLI)**

```bash
openenv validate
```

## Repo map

- `openenv.yaml` — metadata  
- `server/app.py` — app entry  
- `server/ops_triage_environment.py` — env logic + rewards  
- `models.py` — Pydantic action/obs  
- `tasks.py` / `graders.py` — specs + scoring  
- `client.py` — env client  
- `inference.py` — baseline agent  
- `scripts/task_grader_check.py` — quick grader pass  
