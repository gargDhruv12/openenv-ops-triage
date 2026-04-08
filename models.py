from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import Field

from openenv.core.env_server.types import Action, Observation


class OpsTriageAction(Action):
    """Action schema for the operations triage environment."""

    action_type: Literal[
        "inspect_ticket",
        "lookup_runbook",
        "draft_resolution",
        "finalize",
    ] = Field(..., description="Action type to execute")
    focus_field: Optional[str] = Field(
        None, description="Ticket field to inspect for inspect_ticket action"
    )
    query: Optional[str] = Field(
        None, description="Search query for lookup_runbook action"
    )
    resolution_text: Optional[str] = Field(
        None, description="Proposed operator response for draft_resolution or finalize action"
    )
    proposed_owner: Optional[str] = Field(
        None, description="Team owner proposed by the agent"
    )
    proposed_severity: Optional[str] = Field(
        None, description="Severity proposed by the agent: low, medium, high, critical"
    )


class OpsTriageObservation(Observation):
    """Observation payload returned to the agent."""

    task_name: str = Field(..., description="Current task identifier")
    instruction: str = Field(..., description="Task instruction for the agent")
    visible_ticket: Dict[str, str] = Field(
        default_factory=dict, description="Ticket fields currently visible to the agent"
    )
    discovered_runbooks: List[str] = Field(
        default_factory=list, description="Runbooks discovered via lookup actions"
    )
    progress: float = Field(..., description="Progress estimate in [0.0, 1.0]")
    checklist: Dict[str, bool] = Field(
        default_factory=dict, description="Checklist signals for partial progress"
    )
    message: str = Field(..., description="Server feedback about the latest action")
    last_action_error: Optional[str] = Field(
        None, description="Raw error string for the latest action"
    )
    done: bool = Field(False, description="Whether episode is finished")
    reward: Optional[float] = Field(None, description="Reward for latest action")
