from __future__ import annotations

from typing import Dict, List, Set
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from graders import grade_final_submission
from models import OpsTriageAction, OpsTriageObservation
from tasks import TASKS, TASK_ORDER, TaskSpec


class OpsTriageEnvironment(Environment):
    """Real-world inspired operations incident triage environment."""

    def __init__(self, task_name: str | None = None):
        self._task_name = task_name or TASK_ORDER[0]
        self._task: TaskSpec = TASKS[self._task_name]
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._visible_ticket: Dict[str, str] = {}
        self._discovered_runbooks: List[str] = []
        self._revealed_hidden_fields: Set[str] = set()
        self._checklist: Dict[str, bool] = {
            "inspected": False,
            "used_runbook_lookup": False,
            "drafted_resolution": False,
            "finalized": False,
        }
        self._last_action_error: str | None = None
        self._loop_penalty_counter = 0
        self._cached_resolution = ""
        self._cached_owner = ""
        self._cached_severity = ""

    def _build_observation(
        self, message: str, reward: float, done: bool
    ) -> OpsTriageObservation:
        progress = sum(1.0 for v in self._checklist.values() if v) / len(self._checklist)
        return OpsTriageObservation(
            task_name=self._task.name,
            instruction=self._task.instruction,
            visible_ticket=self._visible_ticket,
            discovered_runbooks=self._discovered_runbooks,
            progress=progress,
            checklist=self._checklist,
            message=message,
            last_action_error=self._last_action_error,
            done=done,
            reward=round(reward, 4),
        )

    def reset(self) -> OpsTriageObservation:
        self._task = TASKS[self._task_name]
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._visible_ticket = dict(self._task.ticket)
        self._discovered_runbooks = []
        self._revealed_hidden_fields = set()
        self._checklist = {
            "inspected": False,
            "used_runbook_lookup": False,
            "drafted_resolution": False,
            "finalized": False,
        }
        self._last_action_error = None
        self._loop_penalty_counter = 0
        self._cached_resolution = ""
        self._cached_owner = ""
        self._cached_severity = ""
        return self._build_observation(
            message="Incident loaded. Start by inspecting fields or searching runbooks.",
            reward=0.0,
            done=False,
        )

    def _invalid(self, reason: str, penalty: float = -0.1, done: bool = False) -> OpsTriageObservation:
        self._last_action_error = reason
        self._loop_penalty_counter += 1
        extra_penalty = min(self._loop_penalty_counter * -0.01, -0.05)
        return self._build_observation(reason, penalty + extra_penalty, done)

    def step(self, action: OpsTriageAction) -> OpsTriageObservation:
        self._state.step_count += 1
        self._last_action_error = None

        if self._state.step_count > self._task.max_steps:
            return self._build_observation(
                "Step budget exceeded for this task.",
                reward=-0.2,
                done=True,
            )

        reward = -0.01
        done = False
        message = "Action processed."

        if action.action_type == "inspect_ticket":
            field = (action.focus_field or "").strip()
            if not field:
                return self._invalid("focus_field is required for inspect_ticket")
            if field in self._task.hidden_fields:
                self._visible_ticket[field] = self._task.hidden_fields[field]
                if field not in self._revealed_hidden_fields:
                    reward += 0.15
                    self._revealed_hidden_fields.add(field)
                    self._checklist["inspected"] = True
                    message = f"Revealed hidden field '{field}'."
                else:
                    reward -= 0.02
                    message = f"Field '{field}' was already revealed."
            elif field in self._visible_ticket:
                reward += 0.03
                self._checklist["inspected"] = True
                message = f"Field '{field}' is already visible."
            else:
                return self._invalid(f"Unknown field '{field}'")

        elif action.action_type == "lookup_runbook":
            query = (action.query or "").strip().lower()
            if not query:
                return self._invalid("query is required for lookup_runbook")
            matches = [rb for rb in self._task.runbooks if query in rb.lower()]
            if not matches:
                matches = self._task.runbooks[:1]
                reward -= 0.03
                message = "No exact match; returned most relevant default runbook."
            else:
                reward += 0.12
                message = f"Found {len(matches)} matching runbook(s)."
            for runbook in matches:
                if runbook not in self._discovered_runbooks:
                    self._discovered_runbooks.append(runbook)
                    reward += 0.04
            self._checklist["used_runbook_lookup"] = True

        elif action.action_type == "draft_resolution":
            text = (action.resolution_text or "").strip()
            if len(text) < 20:
                return self._invalid("resolution_text must be at least 20 characters")
            self._cached_resolution = text
            if action.proposed_owner:
                self._cached_owner = action.proposed_owner
            if action.proposed_severity:
                self._cached_severity = action.proposed_severity
            self._checklist["drafted_resolution"] = True
            # Dense signal: quality proxy from keyword overlap.
            preview_grade = grade_final_submission(
                task=self._task,
                proposed_owner=self._cached_owner or "unknown",
                proposed_severity=self._cached_severity or "unknown",
                resolution_text=self._cached_resolution,
            )
            reward += 0.08 + (0.15 * preview_grade.components["resolution"])
            message = "Resolution draft updated."

        elif action.action_type == "finalize":
            resolution_text = (action.resolution_text or self._cached_resolution or "").strip()
            proposed_owner = (action.proposed_owner or self._cached_owner or "").strip()
            proposed_severity = (action.proposed_severity or self._cached_severity or "").strip()
            if not resolution_text or not proposed_owner or not proposed_severity:
                return self._invalid(
                    "finalize requires resolution_text, proposed_owner, and proposed_severity",
                    penalty=-0.14,
                )
            grade = grade_final_submission(
                task=self._task,
                proposed_owner=proposed_owner,
                proposed_severity=proposed_severity,
                resolution_text=resolution_text,
            )
            self._checklist["finalized"] = True
            done = True
            time_bonus = max(0.0, (self._task.max_steps - self._state.step_count) / self._task.max_steps)
            reward = (0.8 * grade.score) + (0.2 * time_bonus)
            message = (
                f"Finalized with score={grade.score:.2f}; owner={grade.components['owner']:.2f}, "
                f"severity={grade.components['severity']:.2f}, resolution={grade.components['resolution']:.2f}"
            )
        else:
            return self._invalid(f"Unsupported action_type '{action.action_type}'")

        self._loop_penalty_counter = 0
        reward = min(max(reward, -1.0), 1.0)
        return self._build_observation(message=message, reward=reward, done=done)

    @property
    def state(self) -> State:
        return self._state
