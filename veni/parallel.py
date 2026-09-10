"""
Parallel Execution Engine for Veni AI.

Runs independent tasks concurrently:
- Multiple file analyses
- Parallel searches
- Concurrent API calls
- Batch operations
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class TaskResult:
    """Result of a parallel task."""

    task_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0


class ParallelEngine:
    """
    Execute tasks in parallel with result aggregation.

    Usage:
        engine = ParallelEngine(max_workers=4)
        results = engine.run_parallel([
            ("analyze_file", lambda: analyze("file1.py")),
            ("analyze_test", lambda: analyze("tests/test1.py")),
            ("search_docs", lambda: search("API reference")),
        ])
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._history: List[List[TaskResult]] = []

    def run_parallel(self, tasks: List[Tuple[str, Callable]]) -> List[TaskResult]:
        """Run multiple tasks in parallel."""
        results = []

        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(tasks))
        ) as executor:
            future_to_name = {}
            for name, func in tasks:
                future = executor.submit(self._safe_execute, name, func)
                future_to_name[future] = name

            for future in as_completed(future_to_name):
                result = future.result()
                results.append(result)

        self._history.append(results)
        return results

    def run_parallel_map(
        self, func: Callable, items: List[Any], name_template: str = "task_{}"
    ) -> List[TaskResult]:
        """Map a function over items in parallel."""
        tasks = [
            (name_template.format(i), lambda f=func, item=item: f(item))
            for i, item in enumerate(items)
        ]
        return self.run_parallel(tasks)

    def get_last_results(self) -> Optional[List[TaskResult]]:
        """Get results from the last parallel execution."""
        if self._history:
            return self._history[-1]
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get parallel execution statistics."""
        total_runs = len(self._history)
        total_tasks = sum(len(r) for r in self._history)
        total_success = sum(sum(1 for t in r if t.success) for r in self._history)
        total_failed = total_tasks - total_success
        avg_duration = sum(sum(t.duration for t in r) for r in self._history) / max(
            total_tasks, 1
        )

        return {
            "parallel_runs": total_runs,
            "total_tasks": total_tasks,
            "successful": total_success,
            "failed": total_failed,
            "avg_duration_s": round(avg_duration, 3),
            "max_workers": self.max_workers,
        }

    def set_workers(self, count: int):
        """Set the number of parallel workers."""
        self.max_workers = max(1, count)

    @staticmethod
    def _safe_execute(name: str, func: Callable) -> TaskResult:
        """Execute a function safely, catching all exceptions."""
        start = time.time()
        try:
            result = func()
            return TaskResult(
                task_name=name,
                success=True,
                result=result,
                duration=time.time() - start,
            )
        except Exception as e:
            return TaskResult(
                task_name=name,
                success=False,
                error=str(e),
                duration=time.time() - start,
            )
