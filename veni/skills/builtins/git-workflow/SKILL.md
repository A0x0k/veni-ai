---
name: "Git Workflow"
description: "Commit messages, branching, rebasing, and PR descriptions from diffs"
triggers: ["commit", "branch", "merge", "rebase", "git", "pull request", "stash", "cherry-pick"]
version: "1.0.0"
author: "veni-team"
---

# Git Workflow Skill

## Commit Messages
Generate from the actual diff, not from a description. Format:
```
<type>(<scope>): <imperative summary under 72 chars>

<body: what changed and why, not how — the diff shows how>
<blank line>
<footer: BREAKING CHANGE: or Fixes #issue>
```
Types: `feat` `fix` `refactor` `perf` `test` `docs` `chore` `ci`

Rules:
- Summary is imperative mood: "add" not "added", "fix" not "fixes"
- Body explains *why*, not *what* — the diff already shows what
- One logical change per commit — flag if the diff mixes unrelated changes

## Branch Naming
`<type>/<short-description>` — e.g. `feat/user-auth`, `fix/null-pointer-login`
Never: `my-branch`, `test`, `wip`, `temp`

## PR Description Template
```
## What
One paragraph: what this PR does.

## Why
One paragraph: why this change is needed.

## How to test
Step-by-step reproduction or test command.

## Checklist
- [ ] Tests added/updated
- [ ] Docs updated if public API changed
- [ ] No secrets committed
```

## Common Mistakes to Flag
- `git add .` before reviewing `git diff --staged`
- Force-pushing to shared branches
- Merging without squashing fixup commits
- Committing generated files (`*.pyc`, `dist/`, `node_modules/`)
- Commit messages that are just "fix" or "update"
