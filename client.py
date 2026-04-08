from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient
from openenv.core.env_server.types import State

from models import OpsTriageAction, OpsTriageObservation


class OpsTriageEnv(EnvClient[OpsTriageAction, OpsTriageObservation, State]):
    def _step_payload(self, action: OpsTriageAction) -> dict:
        return action.model_dump()

    def _parse_result(self, payload: dict) -> StepResult[OpsTriageObservation]:
        obs_payload = payload.get("observation", {})
        observation = OpsTriageObservation(**obs_payload)
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
