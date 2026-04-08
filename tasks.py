from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TaskSpec:
    name: str
    difficulty: str
    instruction: str
    ticket: Dict[str, str]
    hidden_fields: Dict[str, str]
    runbooks: List[str]
    expected_owner: str
    expected_severity: str
    required_resolution_keywords: List[str]
    max_steps: int


TASKS: Dict[str, TaskSpec] = {
    "payment-webhook-timeout-easy": TaskSpec(
        name="payment-webhook-timeout-easy",
        difficulty="easy",
        instruction=(
            "Triage this incident ticket. Identify severity, owner team, and a concrete "
            "resolution message to send to internal stakeholders."
        ),
        ticket={
            "id": "INC-2401",
            "title": "Payment webhook retries spiking for one merchant",
            "service": "payments-ingest",
            "region": "ap-south",
            "impact": "single merchant sees delayed order confirmation",
        },
        hidden_fields={
            "error_signature": "GatewayTimeout after upstream WAF challenge",
            "suspected_cause": "merchant allow-list mismatch",
            "mitigation_hint": "rotate endpoint key and refresh allow-list",
        },
        runbooks=[
            "RB-PAY-17: Merchant webhook authentication repair",
            "RB-NET-03: Edge gateway timeout diagnostics",
            "RB-OBS-11: Alert fatigue triage",
        ],
        expected_owner="payments-platform",
        expected_severity="medium",
        required_resolution_keywords=[
            "allow-list",
            "endpoint key",
            "merchant",
            "monitoring",
        ],
        max_steps=8,
    ),
    "login-outage-regional-medium": TaskSpec(
        name="login-outage-regional-medium",
        difficulty="medium",
        instruction=(
            "Triage and prepare operator response. Consider broad user impact, assign the "
            "right owner, and provide near-term mitigation steps."
        ),
        ticket={
            "id": "INC-3174",
            "title": "Regional login failures after identity deploy",
            "service": "identity-api",
            "region": "eu-west",
            "impact": "35% login failure for consumer traffic",
        },
        hidden_fields={
            "error_signature": "JWT audience mismatch for mobile clients",
            "suspected_cause": "stale edge config after staged rollout",
            "mitigation_hint": "rollback edge config and force token re-issue",
        },
        runbooks=[
            "RB-ID-22: Identity incident rollback procedure",
            "RB-CDN-08: Regional config rollback",
            "RB-SRE-02: Incident communication playbook",
        ],
        expected_owner="identity-sre",
        expected_severity="high",
        required_resolution_keywords=[
            "rollback",
            "token",
            "mobile",
            "status page",
            "reissue",
        ],
        max_steps=10,
    ),
    "data-corruption-multi-tenant-hard": TaskSpec(
        name="data-corruption-multi-tenant-hard",
        difficulty="hard",
        instruction=(
            "Critical multi-tenant data integrity incident. Produce a high-quality triage with "
            "containment, ownership, and communication specifics."
        ),
        ticket={
            "id": "INC-4099",
            "title": "Tenant analytics rows duplicated and partially overwritten",
            "service": "warehouse-sync",
            "region": "multi-region",
            "impact": "12 enterprise tenants report incorrect dashboards",
        },
        hidden_fields={
            "error_signature": "Idempotency key collision in retry worker",
            "suspected_cause": "clock skew + dedupe key truncation",
            "mitigation_hint": "pause retries, isolate bad partitions, replay from checkpoint",
        },
        runbooks=[
            "RB-DATA-41: Corruption containment and replay",
            "RB-QUEUE-19: Worker idempotency safeguards",
            "RB-SEC-05: Enterprise customer communication protocol",
        ],
        expected_owner="data-reliability",
        expected_severity="critical",
        required_resolution_keywords=[
            "pause retries",
            "isolate",
            "checkpoint",
            "idempotency",
            "enterprise",
            "postmortem",
        ],
        max_steps=12,
    ),
}


TASK_ORDER = [
    "payment-webhook-timeout-easy",
    "login-outage-regional-medium",
    "data-corruption-multi-tenant-hard",
]
