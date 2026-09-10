---
name: "Code Review"
description: "Structured code review: bugs, performance, style, security, maintainability"
triggers: ["review", "code review", "pr", "pull request", "feedback", "lgtm", "critique"]
version: "1.0.0"
author: "veni-team"
---

# Code Review Skill

When reviewing code, always work through these layers in order:

## 1. Correctness (Bugs)
- Off-by-one errors in loops and slices
- Null/None dereference without guard
- Mutable default arguments: `def f(x=[])` → flag always
- Exception swallowed silently: bare `except: pass`
- Race conditions in shared state without locks
- Integer overflow in languages without arbitrary precision

## 2. Performance
- N+1 queries: loop calling DB/API per iteration
- Repeated computation inside a loop that could be hoisted
- Unnecessary list materialisation: `list(generator)` when iteration suffices
- Missing index on columns used in WHERE/JOIN
- Unbounded result sets: no LIMIT on queries

## 3. Security
- User input in shell commands, SQL, or file paths without sanitisation
- Hardcoded credentials or tokens
- Logging sensitive fields (passwords, tokens, PII)
- Missing auth check on state-mutating endpoints

## 4. Maintainability
- Function longer than ~40 lines without clear reason
- Magic numbers/strings without named constants
- Deeply nested conditionals (>3 levels) — suggest early return
- Duplicate logic that should be extracted
- Missing type hints on public functions

## Output Format
For each finding:
```
[BUG|PERF|SEC|STYLE] file.py:line — one-sentence description
Suggestion: concrete fix or code snippet
```
End with a one-line overall verdict: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION
