<p align="center">
  <img src="banner.png" alt="Veni AI Banner" width="600"/>
</p>

<p align="center">
  <strong>The most powerful AI assistant ever to live in a shell.</strong><br>
  <em>Multi-provider · Rich TUI · Project-aware · Extensible</em>
</p>

<p align="center">
  <a href="https://github.com/neoastra303/Veni-AI/stargazers">
    <img src="https://img.shields.io/github/stars/neoastra303/Veni-AI?style=flat&logo=github&color=6366f1" alt="Stars"/>
  </a>
  <a href="https://github.com/neoastra303/Veni-AI/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/neoastra303/Veni-AI/ci.yml?style=flat&logo=githubactions&logoColor=white&label=CI" alt="CI"/>
  </a>
  <a href="https://codecov.io/gh/neoastra303/Veni-AI">
    <img src="https://img.shields.io/codecov/c/github/neoastra303/Veni-AI?style=flat&logo=codecov&logoColor=white" alt="Coverage"/>
  </a>
  <a href="https://github.com/neoastra303/Veni-AI/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-10b981?style=flat" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-22c55e?style=flat&logo=python&logoColor=white" alt="Python"/>
  <a href="https://pypi.org/project/veni-ai/">
    <img src="https://img.shields.io/pypi/v/veni-ai?style=flat&logo=pypi&logoColor=white&color=f59e0b" alt="PyPI"/>
  </a>
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fneoastra303%2FVeni-AI%2Fmain%2FARCHITECTURE.md&query=%24&style=flat&label=tests&color=22c55e" alt="Tests"/>
  <img src="https://img.shields.io/badge/coverage-%3E70%25-22c55e?style=flat" alt="Coverage"/>
</p>

<br>

<div align="center">
  <table>
    <tr>
      <td align="center"><b>⚡ 12 Providers</b><br><sub>Ollama · OpenAI · Gemini · Anthropic<br>Groq · DeepSeek · Qwen · Mistral · free</sub></td>
      <td align="center"><b>🛠 45+ Commands</b><br><sub>Session · AI · Git · File · Web · UI</sub></td>
      <td align="center"><b>🧠 21 Skills</b><br><sub>Auto-detecting · Stackable · Context-aware</sub></td>
      <td align="center"><b>🎭 12 Personas</b><br><sub>Expert · Teacher · Critic · Coach · more</sub></td>
      <td align="center"><b>🔌 MCP + Plugins</b><br><sub>Extend with any tool server</sub></td>
    </tr>
  </table>
</div>

<br>

---

## ✨ Features

### 🎯 Core
| | |
|---|---|
| **🖥️ Shell Execution** | Run commands with approval gates, output limits, and risk-tiered safety |
| **📝 File Editing** | Write, patch, and diff — preview before applying |
| **🔎 Repo Search** | Read and index project files for context-aware answers |
| **🧭 Session Control** | Save, load, export, resume — never lose a thread |

### 🧩 Intelligence Layer
| | |
|---|---|
| **🧠 Skills System** | 21 skills auto-activate by context — debugging, data analysis, security, more |
| **🎭 Personas** | Switch AI behavior: Expert, Teacher, Critic, Coach, Creative... |
| **💬 Response Modes** | Detailed, Concise, Socratic, Step-by-Step, Academic... |
| **🔍 Cross-Reference** | Symbol search, import graph, impact analysis before changes |

### 🔌 Extensibility
| | |
|---|---|
| **🧩 Plugin System** | Drop a `.py` file in `plugins/` — instant new commands |
| **🔌 MCP Support** | Model Context Protocol — connect any MCP tool server |
| **📦 12 Providers** | Ollama (local), OpenAI, Gemini, Anthropic, Groq, free, and more |
| **📱 Telegram Gateway** | Chat with Veni from your phone |

### 🛡️ Safety
| | |
|---|---|
| **🛡️ Approval Gates** | Risk-tiered — blocks `rm -rf`, fork bombs, dangerous ops |
| **📁 Workspace Isolation** | All file ops constrained to your project |
| **🔒 PII Redaction** | API keys, tokens, emails auto-masked in exports |

> ⚠️ **Security Notice:** The approval gate is best-effort. For strong isolation, run in a container or VM.

---

## 🚀 Quick Start

```bash
# Install
pip install veni-ai

# Initialize (interactive wizard)
veni init

# Launch
veni chat --provider ollama --model llama3.2
```

### Try it now — no API key needed

```bash
# Free tier (no setup)
veni chat --provider duckduckgo
veni chat --provider free

# Or use Ollama (local)
ollama pull llama3.2
veni chat --provider ollama --model llama3.2
```

### One-shot / pipe mode

```bash
veni pipe "explain this error: TypeError: ..."
echo "review this code" | veni pipe
veni pipe "fix bugs in main.py" --provider openai
```

---

## 🧠 Provider Support

| Provider | Privacy | Tool Use | Cost | Quick Start |
|---|---|---|---|---|
| 🦙 **Ollama** | 🔒 100% Local | ✅ | 🆓 Free | `ollama pull llama3.2` |
| 🧠 **OpenAI** | ☁️ Cloud | ⚡ Native | 💸 Paid | set `OPENAI_API_KEY` |
| 💎 **Gemini** | ☁️ Cloud | ⚡ Native | 💸 Tiered | set `GEMINI_API_KEY` |
| 🤖 **Anthropic** | ☁️ Cloud | ⚡ Native | 💸 Paid | set `ANTHROPIC_API_KEY` |
| ⚡ **Groq** | ☁️ Cloud | ✅ | 🆓 Free | set `GROQ_API_KEY` |
| 🆓 **Free** | ☁️ Cloud | ⚠️ Limited | 🆓 Free | no key needed |
| 🌐 **DuckDuckGo** | ☁️ Cloud | ❌ | 🆓 Free | no key needed |
| 🔷 **DeepSeek** | ☁️ Cloud | ✅ | 💸 Paid | set `DEEPSEEK_API_KEY` |
| 🏔️ **Mistral** | ☁️ Cloud | ✅ | 💸 Paid | set `MISTRAL_API_KEY` |
| 🔀 **OpenRouter** | ☁️ Cloud | ✅ | 💸 Paid | set `OPENROUTER_API_KEY` |
| 🐪 **Qwen** | ☁️ Cloud | ✅ | 💸 Paid | set `QWEN_API_KEY` |
| 🔮 **Perplexity** | ☁️ Cloud | ❌ | 💸 Paid | set `PERPLEXITY_API_KEY` |

---

## 🎮 Command Reference

<details>
<summary><b>Session</b> — /new, /save, /load, /history, /export</summary>

| Command | Action |
|---|---|
| `/new` | Start a new conversation |
| `/save [name]` | Save current session |
| `/load <name>` | Load a saved session |
| `/history` | List saved sessions |
| `/export <md\|txt\|json>` | Export session |
| `/quit` / `/exit` / `/q` | Exit Veni |

</details>

<details>
<summary><b>AI Control</b> — /model, /temperature, /plan</summary>

| Command | Action |
|---|---|
| `/model` | Switch provider and model |
| `/system` | Show system info |
| `/temperature [value]` | Set generation temperature |
| `/top_p [value]` | Set nucleus sampling |
| `/max_tokens [value]` | Set response length limit |
| `/template` | Set prompt template |
| `/status` | Show session stats |
| `/plan [on\|off\|status]` | Toggle autonomous planning mode |

</details>

<details>
<summary><b>Persona & Mode</b> — /persona, /mode</summary>

| Command | Action |
|---|---|
| `/persona [name\|list\|current\|auto]` | Switch AI persona (12 built-in) |
| `/mode [name\|list\|current]` | Switch response style (11 modes) |

</details>

<details>
<summary><b>Skills</b> — /skill list, enable, disable, search</summary>

| Command | Action |
|---|---|
| `/skill list` | List all skills with active status |
| `/skill search <query>` | Find skills by keyword |
| `/skill enable <name>` | Enable a skill |
| `/skill disable <name>` | Disable a skill |
| `/skill status` | Show active skills |
| `/skill auto <query>` | Auto-detect skills for a query |

</details>

<details>
<summary><b>File & Project</b> — /read, /edit, /tree, /xref</summary>

| Command | Action |
|---|---|
| `/pwd` | Show working directory |
| `/ls` | List files |
| `/cd <path>` | Change directory |
| `/read <file>` | Read file into context |
| `/edit <file>` | Ask AI to edit a file |
| `/tree` | Show project structure |
| `/xref <symbol>` | Find symbol cross-references |

</details>

<details>
<summary><b>Git</b> — /diff, /commit, /log</summary>

| Command | Action |
|---|---|
| `/diff` | Show syntax-highlighted git diff |
| `/commit` | AI generates commit message |
| `/commit --review` | AI reviews changes before commit |
| `/log` | Show recent commit history |

</details>

<details>
<summary><b>Intelligence</b> — /search, /scrape, /debug</summary>

| Command | Action |
|---|---|
| `/approve` | Toggle approval gate |
| `/debug` | Analyze error output |
| `/search <query>` | Web search |
| `/scrape <url>` | Scrape web page content |
| `/pdf <url>` | Extract text from PDF URL |

</details>

<details>
<summary><b>Messages & UI</b> — /copy, /theme, /banner, /menu</summary>

| Command | Action |
|---|---|
| `/copy` | Copy last response to clipboard |
| `/pin` / `/unpin` / `/pins` | Pin/unpin responses |
| `/retry` | Re-generate last response |
| `/summary` | Summarize conversation |
| `/alias` | Create command alias |
| `/clear` | Clear screen |
| `/theme` | Switch theme |
| `/banner` | Toggle compact header mode |
| `/voice` | Toggle voice mode |
| `/image <path>` | Attach image |
| `/stats` | Show usage statistics |
| `/help` | Full help |

</details>

---

## 🔌 MCP Integration

Veni supports the **Model Context Protocol** for tool extensibility.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

MCP tools auto-register on startup alongside native tools.

---

## 🧩 Plugin System

Drop a Python file into `plugins/`:

```python
# plugins/my_plugin.py
PLUGIN_COMMANDS = {
    "/greet": lambda args: f"Hello, {args[0] if args else 'World'}!",
}
PLUGIN_HELP = {
    "/greet": "Say hello to someone.",
}
```

---

## 📊 vs Alternatives

| Feature | Veni AI | Claude Code | Aider | Open Interpreter |
|---|---|---|---|---|
| Shell Execution | ✅ | ✅ | ✅ | ✅ |
| Multi-File Editing | ✅ | ✅ | ✅ | ✅ |
| Local Models | ✅ | ❌ | ✅ | ✅ |
| Free Tier | ✅ | ❌ | ❌ | ✅ |
| MCP Support | ✅ | ✅ | ❌ | ❌ |
| Plugin System | ✅ | ✅ | ❌ | ❌ |
| **Skills System** | **✅** | ❌ | ❌ | ❌ |
| **Personas & Modes** | **✅** | ❌ | ❌ | ❌ |
| Voice Mode | Optional | ❌ | ❌ | ❌ |
| Pipe/CI Mode | ✅ | ❌ | ❌ | ❌ |
| Approval Gates | ✅ | ✅ | ❌ | ❌ |
| Web Dashboard | Optional | ❌ | ❌ | ❌ |
| **12 AI Providers** | **✅** | ❌ | ❌ | ❌ |
| **Semantic Memory** | Optional | ❌ | ❌ | ❌ |

---

## 🏗️ Architecture

```
veni/
├── core.py              # Bot orchestration
├── session.py           # Main run loop
├── chat_engine.py       # Streaming, retry, tool calls
├── cli.py               # Typer CLI entry point
├── config.py            # YAML config management
├── approval.py          # Safety approval gate
├── providers/           # 12 AI provider implementations
├── commands/            # 45+ slash commands
├── tools/               # 12 AI-accessible tools
├── skills/builtins/     # 21 SKILL.md definitions
├── personas/builtins/   # 12 persona YAML files
├── modes/builtins/      # 11 mode YAML files
├── memory.py            # Vector semantic memory
├── indexer.py           # Codebase indexer (10+ langs)
├── mcp.py               # MCP client adapter
├── server.py            # FastAPI dashboard
├── scheduler.py         # Background tasks
├── gateways/            # Telegram bridge
├── plugins/             # Drop-in plugin directory
└── tests/               # 286+ tests
```

---

## 🛠 Development

```bash
git clone https://github.com/neoastra303/Veni-AI.git && cd Veni-AI
pip install -e ".[dev]"
pre-commit install

# Full quality check
make check

# Or individual steps
make format       # black
make lint         # ruff
make typecheck    # mypy
make test         # pytest with coverage
make security     # bandit scan
```

**286+ tests** · **70%+ coverage** · **CI/CD** · **CodeQL** · **Dependabot**

---

## 🤝 Contributing

| | |
|---|---|
| 🐛 [Report Bug](https://github.com/neoastra303/Veni-AI/issues) | 💡 [Request Feature](https://github.com/neoastra303/Veni-AI/issues) |
| 🔧 [Open PR](https://github.com/neoastra303/Veni-AI/pulls) | ⭐ [Star the Repo](https://github.com/neoastra303/Veni-AI) |
| 📖 [Contributing Guide](CONTRIBUTING.md) | 🏗️ [Architecture](ARCHITECTURE.md) |

---

<p align="center">
  <a href="https://github.com/neoastra303/Veni-AI">
    <img src="https://img.shields.io/badge/Veni,_Vidi,_Vici.-6366f1?style=for-the-badge" alt="Veni, Vidi, Vici"/>
  </a>
  <br>
  <sub>Designed for engineers. Built for the terminal.</sub>
</p>
