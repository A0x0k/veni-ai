"""
Multi-Step Workflow Orchestration for Veni AI.

Handles complex multi-step tasks autonomously:
- Task decomposition
- Dependency tracking
- Sequential/parallel execution
- Error recovery
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DependencyType(Enum):
    SEQUENTIAL = "sequential"  # Must complete in order
    PARALLEL = "parallel"  # Can run simultaneously
    CONDITIONAL = "conditional"  # Depends on previous result


@dataclass
class TaskStep:
    """A single step in a workflow."""

    name: str
    description: str
    action: Callable
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class Workflow:
    """A multi-step workflow with tracking."""

    name: str
    description: str
    steps: List[TaskStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class WorkflowEngine:
    """
    Executes multi-step workflows with dependency tracking.

    Usage:
        engine = WorkflowEngine(bot)
        workflow = engine.create_workflow(
            "add_auth",
            "Add user authentication",
            steps=[
                TaskStep("analyze", "Analyze existing patterns", analyze_auth),
                TaskStep("create_models", "Create models", create_models,
                         depends_on=["analyze"]),
                TaskStep("write_tests", "Write tests", write_tests,
                         depends_on=["create_models"]),
                TaskStep("run_tests", "Run tests", run_tests,
                         depends_on=["write_tests"]),
            ]
        )
        result = engine.execute(workflow)
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._workflows: Dict[str, Workflow] = {}
        self._history: List[Dict[str, Any]] = []

    def create_workflow(
        self, name: str, description: str, steps: List[TaskStep]
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description,
            steps=steps,
        )
        self._workflows[name] = workflow
        return workflow

    def execute(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute a workflow step by step."""
        workflow.status = TaskStatus.RUNNING
        results = {}

        for step in workflow.steps:
            # Check dependencies
            if not self._dependencies_met(step, workflow):
                step.status = TaskStatus.SKIPPED
                step.error = "Dependencies not met"
                continue

            # Execute step
            step.status = TaskStatus.RUNNING
            try:
                result = step.action()
                step.result = result
                step.status = TaskStatus.COMPLETED
                results[step.name] = result
            except Exception as e:
                # Retry logic
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    try:
                        result = step.action()
                        step.result = result
                        step.status = TaskStatus.COMPLETED
                        results[step.name] = result
                        continue
                    except Exception as retry_e:
                        step.error = str(retry_e)

                step.status = TaskStatus.FAILED
                step.error = str(e)
                workflow.status = TaskStatus.FAILED
                workflow.completed_at = datetime.now()

                self._record_execution(workflow, results)
                return results

        workflow.status = TaskStatus.COMPLETED
        workflow.completed_at = datetime.now()
        self._record_execution(workflow, results)
        return results

    def _dependencies_met(self, step: TaskStep, workflow: Workflow) -> bool:
        """Check if all dependencies for a step are met."""
        for dep_name in step.depends_on:
            dep_step = next((s for s in workflow.steps if s.name == dep_name), None)
            if dep_step is None or dep_step.status != TaskStatus.COMPLETED:
                return False
        return True

    def _record_execution(self, workflow: Workflow, results: Dict[str, Any]):
        """Record workflow execution for learning."""
        entry = {
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error,
                }
                for s in workflow.steps
            ],
            "results_count": len(results),
            "timestamp": (
                workflow.created_at.isoformat() if workflow.created_at else None
            ),
        }
        self._history.append(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        return list(self._history)

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get a workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> Dict[str, Workflow]:
        """List all registered workflows."""
        return dict(self._workflows)

    def get_status(self, workflow: Workflow) -> Dict[str, Any]:
        """Get detailed status of a workflow."""
        return {
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error,
                    "retries": s.retry_count,
                }
                for s in workflow.steps
            ],
        }
