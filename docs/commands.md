# Commands Reference

## Session

| Command | Action |
|---------|--------|
| `/new` | Start a new conversation |
| `/save [name]` | Save current session |
| `/load <name>` | Load a saved session |
| `/history` | List saved sessions |
| `/export <md\|txt\|json>` | Export session |
| `/quit` / `/exit` / `/q` | Exit Veni |

## AI Control

| Command | Action |
|---------|--------|
| `/model` | Switch provider and model |
| `/system` | Show system info |
| `/temperature [value]` | Set generation temperature |
| `/top_p [value]` | Set nucleus sampling |
| `/max_tokens [value]` | Set response length limit |
| `/plan [on\|off\|status]` | Toggle autonomous planning mode |

## Persona & Mode

| Command | Action |
|---------|--------|
| `/persona [name\|list\|current\|auto]` | Switch AI persona |
| `/mode [name\|list\|current]` | Switch response style |

## Skills

| Command | Action |
|---------|--------|
| `/skill list` | List all skills with active status |
| `/skill search <query>` | Find skills by keyword |
| `/skill enable <name>` | Enable a skill |
| `/skill disable <name>` | Disable a skill |

## Intelligence

| Command | Action |
|---------|--------|
| `/approve` | Toggle approval gate |
| `/debug` | Analyze error output |
| `/search <query>` | Web search |
| `/scrape <url>` | Scrape web page content |

## File & Project

| Command | Action |
|---------|--------|
| `/pwd` | Show working directory |
| `/ls` | List files |
| `/cd <path>` | Change directory |
| `/read <file>` | Read file into context |
| `/edit <file>` | Ask AI to edit a file |
| `/tree` | Show project structure |
| `/xref <symbol>` | Find symbol cross-references |

## Git

| Command | Action |
|---------|--------|
| `/diff` | Show git diff |
| `/commit` | AI generates commit message |
| `/log` | Show recent commit history |
