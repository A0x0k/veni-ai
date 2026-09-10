"""
Proactive Heartbeat Scheduler for Veni AI.

Manages autonomous tasks that run in the background:
- Periodic project health checks
- Daily summaries
- Autonomous dependency monitoring
- Scheduled workflow execution
"""

import logging
from typing import Any, Callable, Dict, List, Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    BackgroundScheduler = None  # type: ignore[assignment]
    IntervalTrigger = None  # type: ignore[assignment]

logger = logging.getLogger("veni.scheduler")


class _NullScheduler:
    """Fallback scheduler used when APScheduler is not installed."""

    running = False

    def start(self):
        return None

    def shutdown(self):
        return None

    def add_job(self, *args: Any, **kwargs: Any):
        raise RuntimeError("APScheduler is not installed. Install veni-ai-chatbot[scheduler].")

    def remove_job(self, name: str):
        return None

    def get_jobs(self):
        return []


class VeniScheduler:
    """
    Manages background tasks for Veni AI.
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else _NullScheduler()
        self._tasks: Dict[str, str] = {}

    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Heartbeat scheduler started.")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Heartbeat scheduler stopped.")

    def add_task(
        self,
        name: str,
        func: Callable,
        minutes: int = 60,
        trigger: Optional[Any] = None,
    ):
        """Add a periodic task."""
        if IntervalTrigger is None:
            logger.warning("APScheduler not installed. Skipping proactive task: %s", name)
            return
        if not trigger:
            trigger = IntervalTrigger(minutes=minutes)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=name,
            replace_existing=True,
        )
        self._tasks[name] = str(trigger)
        logger.info("Added proactive task: %s (interval: %d min)", name, minutes)

    def remove_task(self, name: str):
        """Remove a scheduled task."""
        if name in self._tasks:
            self.scheduler.remove_job(name)
            del self._tasks[name]
            logger.info("Removed proactive task: %s", name)

    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all scheduled tasks."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run": (
                        job.next_run_time.isoformat() if job.next_run_time else "n/a"
                    ),
                    "trigger": str(job.trigger),
                }
            )
        return jobs


def setup_default_tasks(scheduler: VeniScheduler, bot: Any):
    """Setup initial proactive tasks for the bot."""
    # 1. Project Health Check (every 4 hours)
    scheduler.add_task(
        "health_check",
        lambda: _run_health_check(bot),
        minutes=240,
    )

    # 2. Workspace Indexing (every hour)
    scheduler.add_task(
        "auto_index",
        lambda: _run_auto_index(bot),
        minutes=60,
    )


def _run_health_check(bot: Any):
    """Perform a silent project health check."""
    logger.info("Starting proactive health check...")
    if hasattr(bot, "error_detector"):
        issues = bot.error_detector.scan_workspace()
        if issues:
            logger.warning("Found %d issues during proactive scan.", len(issues))
            # In a real OpenClaw scenario, this could trigger a notification
            # or an autonomous fix attempt if enabled.


def _run_auto_index(bot: Any):
    """Refresh the codebase index."""
    if hasattr(bot, "codebase_indexer") and bot.codebase_indexer:
        count = bot.codebase_indexer.scan()
        logger.info("Proactive indexing complete: %d files.", count)
