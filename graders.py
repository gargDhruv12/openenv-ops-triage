from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from tasks import TaskSpec


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
    score = min(max(weighted, 0.0), 1.0)
    return GradeBreakdown(
        score=score,
        components={
            "owner": owner_score,
            "severity": severity_score,
            "resolution": resolution_score,
        },
    )
