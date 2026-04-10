from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from tasks import TaskSpec

# Phase 2 validators require every reported score strictly in (0, 1), not 0.0 / 1.0.
# Use 0.01 margin so values stay unambiguous even when formatted with :.2f in logs.
OPEN_INTERVAL_EPS = 0.01


def clamp_open_unit_interval(x: float) -> float:
    """Map any [0, 1] value into (0, 1) with a stable margin from the endpoints."""
    v = min(max(float(x), 0.0), 1.0)
    if v <= OPEN_INTERVAL_EPS:
        return OPEN_INTERVAL_EPS
    if v >= 1.0 - OPEN_INTERVAL_EPS:
        return 1.0 - OPEN_INTERVAL_EPS
    return v


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _keyword_coverage(text: str, keywords: List[str]) -> float:
    normalized = _normalize(text)
    hits = sum(1 for kw in keywords if _normalize(kw) in normalized)
    return hits / max(len(keywords), 1)


@dataclass(frozen=True)
class GradeBreakdown:
    score: float
    components: Dict[str, float]


def grade_final_submission(
    task: TaskSpec,
    proposed_owner: str,
    proposed_severity: str,
    resolution_text: str,
) -> GradeBreakdown:
    owner_score = 1.0 if _normalize(proposed_owner) == _normalize(task.expected_owner) else 0.0
    severity_score = (
        1.0 if _normalize(proposed_severity) == _normalize(task.expected_severity) else 0.0
    )
    resolution_score = _keyword_coverage(resolution_text, task.required_resolution_keywords)

    weighted = (0.35 * owner_score) + (0.30 * severity_score) + (0.35 * resolution_score)
    score = clamp_open_unit_interval(weighted)
    return GradeBreakdown(
        score=score,
        components={
            "owner": clamp_open_unit_interval(owner_score),
            "severity": clamp_open_unit_interval(severity_score),
            "resolution": clamp_open_unit_interval(resolution_score),
        },
    )
