"""
Workflow commands for Veni AI.

/workflow — Manage multi-step task orchestration.
"""

from typing import List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from veni.commands.base import BaseCommand, console


class WorkflowCommand(BaseCommand):
    """Manage workflows."""

    @property
    def name(self) -> str:
        return "/workflow"

    @property
    def description(self) -> str:
        return "Create, run, and manage multi-step workflows."

    @property
    def usage(self) -> str:
        return "/workflow [create|run|list|status|history]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            return self._show_usage()

        action = args[0].lower()

        if action == "create":
            return self._create_workflow(args[1:])
        elif action == "run":
            return self._run_workflow(args[1:])
        elif action == "list":
            return self._list_workflows()
        elif action == "status":
            return self._workflow_status(args[1:])
        elif action == "history":
            return self._workflow_history()
        else:
            return self._show_usage()

    def _create_workflow(self, args: List[str]) -> Optional[str]:
        """Create a new workflow: /workflow create <name> <desc> <steps>"""
        if len(args) < 2:
            self.show_error("Usage: /workflow create <name> <description>")
            return None

        name = args[0]
        description = " ".join(args[1:])

        # Check if already exists
        existing = self.bot.workflow_engine.get_workflow(name)
        if existing:
            self.show_error(f"Workflow '{name}' already exists.")
            return None

        # Create a basic workflow — AI will populate steps via tool calls
        self.bot.workflow_engine.create_workflow(name, description, [])
        self.show_success(f"Workflow created: {name}")
        return None

    def _run_workflow(self, args: List[str]) -> Optional[str]:
        """Run a workflow: /workflow run <name>"""
        if not args:
            self.show_error("Usage: /workflow run <name>")
            return None

        name = args[0]
        workflow = self.bot.workflow_engine.get_workflow(name)
        if not workflow:
            self.show_error(f"Workflow '{name}' not found.")
            return None

        if not workflow.steps:
            self.show_warning(
                f"Workflow '{name}' has no steps. " f"Ask the AI to define steps first."
            )
            return None

        console.print(
            Panel(
                Text.assemble(
                    (f"Running workflow: {name}\n", "bold cyan"),
                    (f"Steps: {len(workflow.steps)}\n\n", "white"),
                    *[
                        Text(f"  {i+1}. {s.name} — {s.description}\n", "dim")
                        for i, s in enumerate(workflow.steps)
                    ],
                ),
                title=" Workflow Execution ",
                border_style="cyan",
            )
        )

        self.bot.workflow_engine.execute(workflow)
        status = self.bot.workflow_engine.get_status(workflow)

        # Show results
        table = Table(title="Workflow Results", box="ROUNDED")
        table.add_column("Step", style="bold cyan")
        table.add_column("Status", style="white")
        table.add_column("Error", style="red")

        for step_info in status["steps"]:
            table.add_row(
                step_info["name"],
                step_info["status"],
                step_info.get("error", "") or "—",
            )

        console.print(table)
        return None

    def _list_workflows(self) -> Optional[str]:
        """List all registered workflows."""
        workflows = self.bot.workflow_engine.list_workflows()
        if not workflows:
            console.print("[dim]No workflows defined.[/dim]")
            return None

        table = Table(title="Registered Workflows", box="ROUNDED")
        table.add_column("Name", style="bold magenta")
        table.add_column("Description", style="white")
        table.add_column("Steps", style="cyan")
        table.add_column("Status", style="green")

        for name, wf in workflows.items():
            table.add_row(
                name,
                wf.description[:50],
                str(len(wf.steps)),
                wf.status.value,
            )

        console.print(table)
        return None

    def _workflow_status(self, args: List[str]) -> Optional[str]:
        """Show detailed status of a workflow."""
        if not args:
            self.show_error("Usage: /workflow status <name>")
            return None

        name = args[0]
        workflow = self.bot.workflow_engine.get_workflow(name)
        if not workflow:
            self.show_error(f"Workflow '{name}' not found.")
            return None

        status = self.bot.workflow_engine.get_status(workflow)

        console.print(
            Panel(
                Text.assemble(
                    (f"Workflow: {workflow.name}\n\n", "bold cyan"),
                    (f"Description: {workflow.description}\n", "white"),
                    (f"Status: {status['status']}\n\n", "bold yellow"),
                    "Steps:\n",
                    *[
                        Text(
                            f"  [{s['status']}] {s['name']}"
                            f" (retries: {s['retries']})\n"
                            + (f"    Error: {s['error']}\n" if s.get("error") else ""),
                            "white" if s["status"] == "completed" else "yellow",
                        )
                        for s in status["steps"]
                    ],
                ),
                title=" Workflow Status ",
                border_style="yellow",
            )
        )
        return None

    def _workflow_history(self) -> Optional[str]:
        """Show execution history."""
        history = self.bot.workflow_engine.get_history()
        if not history:
            console.print("[dim]No workflow execution history.[/dim]")
            return None

        table = Table(title="Execution History", box="ROUNDED")
        table.add_column("Workflow", style="bold magenta")
        table.add_column("Status", style="white")
        table.add_column("Steps", style="cyan")
        table.add_column("Timestamp", style="dim")

        for entry in history[-10:]:  # Last 10
            table.add_row(
                entry["name"],
                entry["status"],
                str(entry["results_count"]),
                entry.get("timestamp", "—"),
            )

        console.print(table)
        return None
