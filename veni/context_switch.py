"""
Smart Context Switching for Veni AI.

Automatically detects project type and loads appropriate context:
- Framework detection
- Language detection
- Project-specific preferences
- Auto-loaded tool configurations
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Project type detection rules
PROJECT_SIGNATURES = {
    "python_django": {
        "files": ["manage.py", "settings.py"],
        "requirements": ["django"],
    },
    "python_flask": {
        "files": ["app.py", "wsgi.py"],
        "requirements": ["flask"],
    },
    "python_fastapi": {
        "files": ["main.py"],
        "requirements": ["fastapi"],
    },
    "python_package": {
        "files": ["setup.py", "pyproject.toml", "setup.cfg"],
        "requirements": [],
    },
    "node_react": {
        "files": ["package.json"],
        "requirements": ["react"],
    },
    "node_express": {
        "files": ["package.json"],
        "requirements": ["express"],
    },
    "node_nextjs": {
        "files": ["next.config.js", "next.config.mjs"],
        "requirements": ["next"],
    },
    "rust_cargo": {
        "files": ["Cargo.toml"],
        "requirements": [],
    },
    "go_module": {
        "files": ["go.mod"],
        "requirements": [],
    },
    "java_gradle": {
        "files": ["build.gradle", "build.gradle.kts"],
        "requirements": [],
    },
    "java_maven": {
        "files": ["pom.xml"],
        "requirements": [],
    },
}

# Project-specific system prompts
PROJECT_PROMPTS = {
    "python_django": (
        "This is a Django project. "
        "Use Django ORM patterns, follow Django conventions. "
        "Commands: python manage.py ..."
    ),
    "python_flask": (
        "This is a Flask project. "
        "Use Flask patterns with blueprints. "
        "Commands: flask run, flask shell"
    ),
    "python_fastapi": (
        "This is a FastAPI project. "
        "Use async patterns, Pydantic models, dependency injection."
    ),
    "node_react": (
        "This is a React project. "
        "Use JSX, hooks, functional components. "
        "Commands: npm start, npm test, npm run build"
    ),
    "node_express": (
        "This is an Express.js project. " "Use middleware patterns, async/await."
    ),
    "rust_cargo": (
        "This is a Rust project. " "Use cargo commands, follow Rust ownership patterns."
    ),
    "go_module": ("This is a Go project. " "Use go modules, follow Go conventions."),
}


class ProjectContext:
    """Detected and managed project context."""

    def __init__(
        self,
        project_type: str,
        root: Path,
        language: str,
        frameworks: List[str],
        prompt_addition: str,
    ):
        self.project_type = project_type
        self.root = root
        self.language = language
        self.frameworks = frameworks
        self.prompt_addition = prompt_addition
        self.detected_at = __import__("time").time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_type": self.project_type,
            "language": self.language,
            "frameworks": self.frameworks,
            "prompt_addition": self.prompt_addition,
        }


class ContextSwitcher:
    """
    Automatically detects and switches project contexts.

    Usage:
        switcher = ContextSwitcher(bot)
        context = switcher.detect(Path.cwd())
        bot.system_prompt += context.prompt_addition
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._current_context: Optional[ProjectContext] = None
        self._context_history: List[ProjectContext] = []

    def detect(self, path: Optional[Path] = None) -> ProjectContext:
        """Detect the project type at the given path."""
        path = path or self.bot.workspace_root
        path = path.resolve()

        project_type, frameworks = self._detect_project_type(path)
        language = self._detect_language(path)
        prompt = PROJECT_PROMPTS.get(project_type, "")

        context = ProjectContext(
            project_type=project_type,
            root=path,
            language=language,
            frameworks=frameworks,
            prompt_addition=prompt,
        )

        if self._current_context and self._current_context.root != path:
            self._context_history.append(self._current_context)

        self._current_context = context
        return context

    def get_context(self) -> Optional[ProjectContext]:
        """Get the current project context."""
        return self._current_context

    def get_history(self) -> List[Dict[str, Any]]:
        """Get context switch history."""
        return [c.to_dict() for c in self._context_history]

    def get_system_prompt_addition(self) -> str:
        """Get the additional system prompt for current context."""
        if self._current_context:
            return self._current_context.prompt_addition
        return ""

    def _detect_project_type(self, path: Path) -> Tuple[str, List[str]]:
        """Detect the project type based on file signatures."""
        best_match = "unknown"
        best_frameworks: List[str] = []
        best_score = 0

        for proj_type, signatures in PROJECT_SIGNATURES.items():
            score = 0
            frameworks = []

            # Check for signature files
            for sig_file in signatures["files"]:
                if (path / sig_file).exists():
                    score += 10

            # Check requirements/dependencies
            for req in signatures["requirements"]:
                if self._has_dependency(path, req):
                    score += 5
                    frameworks.append(req)

            if score > best_score:
                best_score = score
                best_match = proj_type
                best_frameworks = frameworks

        return best_match, best_frameworks

    def _detect_language(self, path: Path) -> str:
        """Detect the primary language of the project."""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript (React)",
            ".jsx": "javascript (React)",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".rb": "ruby",
        }

        counts: Dict[str, int] = {}
        for ext, lang in extensions.items():
            count = len(list(path.rglob(f"*{ext}")))
            if count > 0:
                counts[lang] = count

        if counts:
            return max(counts, key=counts.get)
        return "unknown"

    def _has_dependency(self, path: Path, dep: str) -> bool:
        """Check if a project has a specific dependency."""
        dep_lower = dep.lower()

        # Check requirements.txt
        req_file = path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text(encoding="utf-8").lower()
            if dep_lower in content:
                return True

        # Check package.json
        pkg_file = path / "package.json"
        if pkg_file.exists():
            try:
                import json

                data = json.loads(pkg_file.read_text(encoding="utf-8"))
                all_deps = {}
                all_deps.update(data.get("dependencies", {}))
                all_deps.update(data.get("devDependencies", {}))
                if dep_lower in all_deps:
                    return True
            except Exception as exc:
                logger.debug("Failed to check dependency %s in %s: %s", dep, pkg_file, exc)

        # Check Cargo.toml
        cargo_file = path / "Cargo.toml"
        if cargo_file.exists():
            content = cargo_file.read_text(encoding="utf-8").lower()
            if dep_lower in content:
                return True

        # Check go.mod
        go_file = path / "go.mod"
        if go_file.exists():
            content = go_file.read_text(encoding="utf-8").lower()
            if dep_lower in content:
                return True

        return False
