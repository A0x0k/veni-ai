# Changelog

All notable changes to Veni AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-01

### Added
- **21 builtin skills** covering: Code Review, Debugging, Git Workflow, Refactoring, Database, Testing, Security Audit, Python Web Dev, DevOps & CI/CD, Data Analysis, Documentation, Jupyter, ML Workflow, Shell Scripting, Log Analysis, Explain Code, Writing Assistant, Research Assistant, Productivity, Learning Assistant, Problem Solving
- **11 personas** with specific behavioral directives: Expert, Teacher, Analyst, Critic, Coach, Creative, Advisor, Strategist, Philosopher, Journalist, Translator, Scientist
- All builtin skills auto-enabled on startup — no manual activation required
- `/skill search <query>` — discover skills by keyword
- `/copy session` — copy full conversation to clipboard
- `/plan [on|off|status]` — autonomous planning mode
- `veni --version` / `veni -V` flag
- `veni init` interactive wizard — provider selection, API key prompt, `.env` write
- DuckDuckGo provider (`--provider duckduckgo`, no API key required)
- Active skills indicator in bottom toolbar (`🛠 skill-name`)
- Word-boundary trigger matching for skills (prevents false positives)
- `scripts/update_changelog.py` — automated changelog generation from git log
- `__version__` in `veni/__init__.py`

### Architecture
- Extracted `core.py` god object into focused modules:
  - `veni/tool_executor.py` — tool call parsing and dispatch
  - `veni/plugin_loader.py` — plugin discovery and loading
  - `veni/ui.py` — all Rich display methods
  - `veni/chat_engine.py` — streaming, retry, tool loop
  - `veni/startup.py` — session resume, indexer init, autosave
  - `veni/session.py` — main run loop and per-turn helpers
- `core.py` reduced from 41KB god object to ~250 lines of wiring

### Improved
- Streaming now renders directly into the final response panel — no spinner-then-swap
- `show_success/error/warning` replaced panels with clean inline `✔/✖/⚠` prefix lines
- Removed single-char shortcut footgun (`n`, `s`, `q` etc. no longer hijack input)
- Banner version reads from `__version__` instead of hardcoded string
- All 11 persona yaml files rewritten with specific behavioral rules
- All 6 original skill SKILL.md files rewritten with actionable, specific instructions
- `/export` command fixed for Windows (removed `NamedTemporaryFile` double-open bug)
- Memory eviction now reliably targets oldest entries (sorted by timestamp)
- Scheduler task callbacks wrapped in `try/except` — a failing task can no longer kill the heartbeat loop
- Stream retry: up to 2 retries with backoff on transient provider errors (429, 503, connection reset)
- Tool call timeout: 30s hard limit per tool call via `ThreadPoolExecutor`
- Tool call recursion cap raised to 10 with user warning when limit reached

### Fixed
- `cli.py` — `_version_callback` and `@app.callback()` were defined twice (silent overwrite)
- `cli.py` — pipe mode sent empty history to model; user message was never passed
- `cli.py` — duplicate `from veni import __version__` import
- `cli.py` — `Table(box="ROUNDED")` string instead of `box.ROUNDED` object
- `commands/intelligence.py` — `/skill <name>` crashed: `skill.description` → `skill.metadata.description`
- `commands/intelligence.py` — `/plan` crashed: `bot.planning_mode` attribute never existed
- `commands/intelligence.py` — `PlanCommand` was defined but never imported or registered
- `history.py` — orphaned syntax fragment caused `SyntaxError` on import
- `tools/shell.py` — `_BLOCKED_TOKEN_PATTERNS` referenced but never defined (crash on any blocked command)
- `tools/shell.py` — `_contains_token_pattern` returned `""` instead of `False`
- `tools/shell.py` — orphaned indentation error from deleted code
- `tools/shell.py` — Windows shell detection hardcoded to `powershell.exe`; now probes `pwsh > powershell > cmd.exe`
- `commands/intelligence.py` — `Table(box="ROUNDED")` string bug in persona/mode/skill list commands
- `providers/duckduckgo.py` — fully implemented but unreachable (not registered in factory)
- `server.py` — dashboard bound to `0.0.0.0` (exposed to network); changed to `127.0.0.1`

### Security
- Dashboard bind address changed from `0.0.0.0` to `127.0.0.1`
- Added `SECURITY NOTICE` to `approval.py` and `tools/shell.py` — blocklist is best-effort, not a hard boundary
- Added 14 PowerShell-aware blocked command patterns (`Remove-Item -Recurse`, `ri -r`, `del /s`, etc.)

### Package
- Version bumped to `1.0.0`
- `pyproject.toml` — all 22 dependencies pinned with upper bounds (`>=x,<y`)
- `pyproject.toml` — added `[project.urls]` (Homepage, Repository, Issues, Changelog)
- `pyproject.toml` — package discovery changed to `find: include = ["veni*"]`
- `pyproject.toml` — added `package-data` to include `SKILL.md`, templates, personas, modes in wheel
- `pypdf>=4.0.0` replaces deprecated `PyPDF2`
- `watchdog>=4.0.0` added (was only in `requirements.txt`)
- `requirements.txt` deleted (superseded by `pyproject.toml`)
- `.gitignore` — added `temp_pytest_runtime/` and `.pytest_cache_local/`

### Tests
- 191 tests, all passing
- New test files: `test_tool_executor.py`, `test_plugin_loader.py`, `test_commands_smoke.py`, `test_tools_and_providers.py`
- Fixed 5 pre-existing test failures caused by refactoring

---

## [0.9.0] - 2026-03-24 (pre-release)

### Added
- Native tool calling support for autonomous AI actions
- Tool call pattern detection (CALL: and JSON formats)
- Recursive tool execution with loop prevention
- `APIError` exception class with retry information
- Multiple endpoint fallback for free provider
- CONTRIBUTING.md documentation

### Changed
- Free provider now uses multiple endpoints for reliability
- OpenAI provider now properly buffers streaming tool calls
- Enhanced HTTP retry logic with specific error handling

### Fixed
- Free AI provider 404 errors with URL encoding fix
- Tool call argument parsing with spaces
- Security vulnerability: Removed exposed API key from .env

## [0.8.0] - 2026-03-13

### Added
- Command pattern architecture with `BaseCommand` and `CommandRegistry`
- Modular command system in `veni/commands/`
- Tool registry for AI-accessible tools
- File read/write tools
- Web search tool using DuckDuckGo
- Voice tool for text-to-speech
- Security redaction layer for sensitive data
- Provider capability system

## [0.7.0] - 2026-02-20

### Added
- Multi-provider support (Ollama, OpenAI, Gemini, Anthropic, Groq, DeepSeek, Qwen)
- Rich TUI with gradients and panels
- Token counting with tiktoken
- Session save/load functionality
- Pin messages to prevent pruning
- Export sessions to MD/TXT/JSON

## [0.1.0] - 2026-01-15

### Added
- Initial release
- Basic chat functionality
- Ollama provider support
- Command system (`/help`, `/quit`, `/model`, etc.)
- Configuration management
- Chat history persistence

---

| Version | Date | Key Features |
|---|---|---|
| 1.0.0 | 2026-05-01 | Skills system, persona overhaul, architecture refactor, 191 tests |
| 0.9.0 | 2026-03-24 | Native tool calling, retry logic |
| 0.8.0 | 2026-03-13 | Modular architecture, tool registry |
| 0.7.0 | 2026-02-20 | Multi-provider, Rich UI |
| 0.1.0 | 2026-01-15 | Initial release |
