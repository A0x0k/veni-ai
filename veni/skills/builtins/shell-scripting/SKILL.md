---
name: "Shell Scripting"
description: "Bash and PowerShell scripts with proper error handling, quoting, and safety"
triggers: ["bash", "shell script", "powershell", "automation", "cron", "sh", "zsh", "script"]
version: "1.0.0"
author: "veni-team"
---

# Shell Scripting Skill

## Bash — Always Start With
```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
```
- `set -e` — exit on error
- `set -u` — error on unset variables
- `set -o pipefail` — pipe failures propagate
- Flag any script missing these

## Quoting Rules — Flag These
```bash
# WRONG — word splitting and glob expansion
cp $file $dest
for f in $(ls *.txt)

# RIGHT
cp "$file" "$dest"
for f in *.txt
```
Always double-quote variable expansions. Use `$()` not backticks.

## Error Handling
```bash
# Trap for cleanup on exit
cleanup() { rm -f "$tmpfile"; }
trap cleanup EXIT

# Check command exists before using
command -v docker &>/dev/null || { echo "docker not found"; exit 1; }
```

## PowerShell — Always Include
```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
```
- Use `$PSScriptRoot` for script-relative paths, never hardcoded paths
- Use `[CmdletBinding()]` on functions that should support `-Verbose`
- Prefer `Get-ChildItem` over `ls`, `Remove-Item` over `rm` for clarity

## Common Mistakes to Flag
- `rm -rf $dir` without quoting — becomes `rm -rf` if `$dir` is empty
- Parsing `ls` output — use globs or `find` instead
- `if [ $var == "x" ]` — use `[[ ]]` in bash, or quote `"$var"`
- Hardcoded absolute paths like `/home/user/` — use `$HOME` or `$(pwd)`
- No `exit 1` on failure — scripts that always exit 0 hide errors in CI
