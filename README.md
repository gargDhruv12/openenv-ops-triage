---
title: Ops Triage Env
emoji: 👀
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
---

# Ops Triage OpenEnv

OpenEnv environment for **production incident operations triage**: agents inspect ticket evidence, search runbooks, draft stakeholder-facing resolutions, and finalize owner, severity, and messaging—similar to real on-call / incident-commander workflows.

## Motivation and real-world utility

Most public RL/agent benchmarks avoid messy operational work. This environment targets a gap that teams actually care about: **structured triage under partial observability**. Tickets start with surface fields; critical diagnosis lives in hidden evidence until the agent chooses to inspect the right attributes. Runbook lookup is imperfect on purpose. The grader rewards correct routing (owner, severity) and concrete communication quality (keyword coverage for mitigation concepts), not trivia.

This is intended for **training and evaluating** agents that must combine information gathering, tool-like actions, and structured decisions—closer to reliability engineering practice than game-like MDPs.

## Action space (`OpsTriageAction`)

Defined in `models.py` (Pydantic, OpenEnv `Action` subtype):

| Field | Role |
|--------|------|
| `action_type` | One of: `inspect_ticket`, `lookup_runbook`, `draft_resolution`, `finalize` |
| `focus_field` | Ticket field name for `inspect_ticket` |
| `query` | Substring search for `lookup_runbook` |
| `resolution_text` | Draft or final stakeholder message |
| `proposed_owner` | Predicted owning team |
| `proposed_severity` | One of `low`, `medium`, `high`, `critical` |

## Observation space (`OpsTriageObservation`)

| Field | Role |
|--------|------|
| `task_name`, `instruction` | Task id and natural-language objective |
| `visible_ticket` | Fields currently visible (initial ticket + revealed hidden fields) |
| `discovered_runbooks` | Runbooks retrieved via lookup |
| `progress` | Scalar in `[0.0, 1.0]` from checklist completion |
| `checklist` | Booleans: inspected, runbook used, draft written, finalized |
| `message` | Environment feedback for the last action |
| `last_action_error` | Parse/validation error text if the action was invalid |
| `done`, `reward` | Episode termination and last-step reward |

## Tasks and difficulty

All tasks live in `tasks.py` (three tasks, increasing difficulty):

| Task id | Difficulty | Summary |
|---------|------------|---------|
| `payment-webhook-timeout-easy` | Easy | Single-merchant payment webhook delays; narrow blast radius |
| `login-outage-regional-medium` | Medium | Regional identity impact after deploy; broader user-facing risk |
| `data-corruption-multi-tenant-hard` | Hard | Multi-tenant analytics integrity; containment + comms bar is higher |

Each task defines: public ticket fields, **hidden** diagnostic fields, runbook catalog, gold owner/severity, required resolution phrases, and a step budget.

## Grading (deterministic, reproducible)

`graders.py` implements a **deterministic** scorer (no randomness, no network):

- **Owner** (35%): exact normalized match to expected team string  
- **Severity** (30%): exact normalized match to expected severity  
- **Resolution** (35%): fraction of required keywords present in normalized resolution text  

The weighted score is then passed through `clamp_open_unit_interval()` so reported values stay strictly inside **(0, 1)** for automated evaluation pipelines that reject exact `0.0` / `1.0` endpoints. Internally, grading logic is still the weighted mix above; the clamp only adjusts boundary cases for tooling compatibility.

Run a quick reproducibility check:

```bash
python scripts/task_grader_check.py
```

With **oracle** submissions (correct owner, severity, and all keywords in text), you should see composite scores **≈ 0.99** per task after the open-interval clamp (not exactly 1.0 by design).

## Reward shaping and episode boundaries

`server/ops_triage_environment.py`:

- **Sparse but not only terminal**: bonuses for revealing hidden fields, successful runbook matches, draft quality preview via grader resolution channel; penalties for invalid or loop-like actions.  
- **Terminal reward** on `finalize`: combines grader score and a mild time-efficiency term.  
- **`reset()`** rebuilds ticket visibility, runbooks, checklist, caches, and step state—clean episode start.  
- **Done** is set when `finalize` succeeds or step budget is exceeded.

## Baseline performance (`inference.py`)

The root **`inference.py`** is the hackathon baseline: it drives the Docker env via `OpsTriageEnv.from_docker_image`, uses the **OpenAI** client with platform-provided **`API_BASE_URL`** and **`API_KEY`** (LiteLLM proxy in evaluation), and prints strict stdout lines:

`[START]`, `[STEP]`, `[END]`

Reported **per-task score** in `[END]` is a normalized positive-reward proxy from environment steps, then clamped to the open interval **(0, 1)** for the same evaluation rules. Exact numbers **depend on the model**, Docker availability, and run length; they are **not** fixed constants across machines.

**Reference (deterministic grader only, oracle text):** see `python scripts/task_grader_check.py` output above—use that for “grader ceiling” reporting, not as a guarantee for LLM-driven `inference.py` runs.

## Setup and usage

### Local Python

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\python -m pip install -r requirements.txt
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Baseline inference

Set env vars as required by the platform (evaluation injects `API_BASE_URL`, `API_KEY`; local dev may use `HF_TOKEN` as fallback). Optional: `LOCAL_IMAGE_NAME`, `OPS_TRIAGE_TASKS`.

```bash
python inference.py
```

### Docker

```bash
docker build -t openenv-ops-triage:latest .
docker run --rm -p 8000:8000 openenv-ops-triage:latest
```

Hugging Face Spaces (Docker SDK) should bind **`PORT`**; this repo’s `Dockerfile` uses `${PORT:-7860}` for that.

### OpenEnv validation

With `openenv-core` installed:

```bash
openenv validate
```

## Project layout

- `openenv.yaml` — environment metadata  
- `server/app.py` — FastAPI app factory (`create_app`)  
- `server/ops_triage_environment.py` — environment logic  
- `models.py` — typed action/observation models  
- `tasks.py`, `graders.py` — task specs and grading  
- `client.py` — HTTP/Docker client helper  
- `inference.py` — baseline agent script (required name/location)  
- `scripts/task_grader_check.py` — grader smoke test  

## Originality (plagiarism-safe scope)

This repository implements a **specific scenario** (ops triage with hidden ticket fields, runbook search, draft/finalize lifecycle, and a three-part grader) on top of the public OpenEnv server patterns. It is **not** a copy-paste of another published OpenEnv environment: task narratives, hidden-field structure, keyword sets, runbook lists, and reward shaping are authored for this benchmark. If you extend it, keep attribution to OpenEnv and document new tasks/graders you add.

## License and citation

Use this environment under the terms of your hackathon / repo license. When citing, name the environment (**ops triage / incident triage OpenEnv**) and link this repository and the OpenEnv project you built upon.
