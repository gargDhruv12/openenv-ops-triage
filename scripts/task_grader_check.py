from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graders import OPEN_INTERVAL_EPS, grade_final_submission
from tasks import TASK_ORDER, TASKS


def main() -> None:
    for task_name in TASK_ORDER:
        task = TASKS[task_name]
        result = grade_final_submission(
            task=task,
            proposed_owner=task.expected_owner,
            proposed_severity=task.expected_severity,
            resolution_text=" ".join(task.required_resolution_keywords),
        )
        lo, hi = OPEN_INTERVAL_EPS, 1.0 - OPEN_INTERVAL_EPS
        assert lo <= result.score <= hi, f"Score out of open interval for {task_name}"
        print(
            f"task={task_name} difficulty={task.difficulty} score={result.score:.6f} "
            f"owner={result.components['owner']:.6f} severity={result.components['severity']:.6f} "
            f"resolution={result.components['resolution']:.6f}"
        )


if __name__ == "__main__":
    main()
