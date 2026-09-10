# Architecture

Veni AI follows a modular architecture designed for extensibility, safety, and agentic autonomy.

## Overview

```
veni/
├── core.py              # Bot wiring & orchestration
├── session.py           # Main run loop
├── chat_engine.py       # Streaming, retry, tool call loop
├── cli.py               # Typer CLI entry point
├── config.py            # YAML config management
├── approval.py          # Safety approval gate
│
├── providers/           # 12 AI provider implementations
│   ├── base.py          # AIClient ABC
│   └── factory.py       # Provider factory
│
├── commands/            # 45+ slash commands
│   └── base.py          # BaseCommand ABC + CommandRegistry
│
├── tools/               # 12 AI-accessible tools
│   └── base.py          # AITool ABC + ToolRegistry
│
├── skills/builtins/     # 21 built-in SKILL.md files
├── personas/builtins/   # 12 persona YAML files
├── modes/builtins/      # 10 mode YAML files
│
├── skill_manager.py     # Skill stacking & auto-detection
├── skill_registry.py    # AgentSkills-standard registry
├── personas/engine.py   # Persona engine
├── modes/engine.py      # Mode engine
│
├── memory.py            # Vector-based semantic memory
├── indexer.py           # Codebase indexing
├── mcp.py               # MCP client adapter
├── server.py            # FastAPI web dashboard
├── scheduler.py         # Background scheduler
└── gateways/            # Telegram bridge
```

## Design Patterns

- **Command Pattern**: `BaseCommand` ABC with `CommandRegistry` for slash command dispatch
- **Strategy Pattern**: `AIClient` ABC with factory for 12 provider implementations
- **Composite Pattern**: `SkillStack` with auto-detected + user-selected skills
- **Middleware Pattern**: `ApprovalGate` as safety interceptor
- **Dependency Injection**: `TerminalChatbot` receives `AIClient` instance
- **Lazy Loading**: Heavy dependencies loaded only when needed
