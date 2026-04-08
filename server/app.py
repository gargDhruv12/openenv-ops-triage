from __future__ import annotations

import os

from openenv.core.env_server import create_app
import uvicorn

from models import OpsTriageAction, OpsTriageObservation
from server.ops_triage_environment import OpsTriageEnvironment


def _create_env() -> OpsTriageEnvironment:
    task_name = os.getenv("OPS_TRIAGE_TASK", "payment-webhook-timeout-easy")
    return OpsTriageEnvironment(task_name=task_name)


app = create_app(_create_env, OpsTriageAction, OpsTriageObservation, env_name="ops_triage_env")


def main() -> None:
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
