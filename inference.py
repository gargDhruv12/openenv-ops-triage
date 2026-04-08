from __future__ import annotations

import asyncio
import json
import os
from typing import List, Optional

from openai import OpenAI

from client import OpsTriageEnv
from models import OpsTriageAction
from tasks import TASK_ORDER

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("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")
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "openenv-ops-triage:latest")
BENCHMARK = "ops_triage_env"
MAX_STEPS = 12


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def _build_prompt(observation: dict, task_name: str) -> str:
    return (
        "You are an incident response agent. Return ONLY valid minified JSON with keys "
        "action_type, focus_field, query, resolution_text, proposed_owner, proposed_severity. "
        "Choose one action at a time.\n"
        f"Task: {task_name}\n"
        f"Observation: {json.dumps(observation, ensure_ascii=True)}\n"
        "Use finalize when you have enough confidence."
    )


def _safe_action_parse(text: str) -> OpsTriageAction:
    try:
        payload = json.loads(text)
        return OpsTriageAction(**payload)
    except Exception:
        # Deterministic fallback action when model output is malformed.
        return OpsTriageAction(action_type="inspect_ticket", focus_field="error_signature")


def _get_model_action(client: OpenAI, task_name: str, observation: dict) -> OpsTriageAction:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": "You produce strict JSON only.",
            },
            {
                "role": "user",
                "content": _build_prompt(observation=observation, task_name=task_name),
            },
        ],
    )
    content = (completion.choices[0].message.content or "").strip()
    return _safe_action_parse(content)


async def run_task(task_name: str, client: OpenAI) -> float:
    env = await OpsTriageEnv.from_docker_image(IMAGE_NAME, env_vars={"OPS_TRIAGE_TASK": task_name})
    rewards: List[float] = []
    success = False
    score = 0.0
    steps = 0

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    try:
        result = await env.reset()
        for step_idx in range(1, MAX_STEPS + 1):
            obs_dict = result.observation.model_dump()
            action = _get_model_action(client=client, task_name=task_name, observation=obs_dict)
            result = await env.step(action)
            reward = float(result.reward or 0.0)
            rewards.append(reward)
            steps = step_idx
            err = result.observation.last_action_error
            log_step(
                step=step_idx,
                action=action.model_dump_json(),
                reward=reward,
                done=result.done,
                error=err,
            )
            if result.done:
                break

        # Final score is normalized cumulative positive reward proxy.
        clipped_positive = sum(max(0.0, r) for r in rewards)
        score = min(clipped_positive / max(len(rewards), 1), 1.0)
        success = score >= 0.65
    finally:
        try:
            await env.close()
        finally:
            log_end(success=success, steps=steps, score=score, rewards=rewards)
    return score


async def main() -> None:
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN environment variable is required")
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    task_names = os.getenv("OPS_TRIAGE_TASKS")
    selected_tasks = [t.strip() for t in task_names.split(",")] if task_names else TASK_ORDER
    for task in selected_tasks:
        await run_task(task_name=task, client=client)


if __name__ == "__main__":
    asyncio.run(main())
