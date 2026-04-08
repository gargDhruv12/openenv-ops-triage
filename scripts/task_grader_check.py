from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graders import grade_final_submission
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
        assert 0.0 <= result.score <= 1.0, f"Score out of range for {task_name}"
        print(
            f"task={task_name} difficulty={task.difficulty} score={result.score:.2f} "
            f"owner={result.components['owner']:.2f} severity={result.components['severity']:.2f} "
            f"resolution={result.components['resolution']:.2f}"
        )


if __name__ == "__main__":
    main()
