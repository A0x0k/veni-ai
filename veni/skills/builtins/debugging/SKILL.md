---
name: "Debugging"
description: "Systematic error diagnosis: stack traces, reproduction, root cause, fix"
triggers: ["error", "bug", "traceback", "exception", "not working", "broken", "crash", "fails", "debug", "why is"]
version: "1.0.0"
author: "veni-team"
---

# Debugging Skill

When given an error or unexpected behaviour, always follow this order:

## Step 1 — Read the Stack Trace Bottom-Up
The bottom frame is where the error *occurred*. The top is where it *originated*.
- Identify the first frame in *user code* (not library code)
- That's where to look first — not the library internals

## Step 2 — Identify the Error Type Before Guessing
- `AttributeError: 'NoneType' has no attribute X` → something returned None unexpectedly; find where it's set
- `KeyError: 'x'` → dict access on missing key; check where the dict is built
- `TypeError: unsupported operand` → type mismatch; check what's being passed
- `RecursionError` → infinite recursion; find the base case
- `ImportError` / `ModuleNotFoundError` → wrong env, missing install, or circular import
- `PermissionError` → file/socket permissions, not a code bug

## Step 3 — Reproduce Minimally
Before suggesting a fix, identify the minimal input that triggers the bug.
State it explicitly: "This fails when X is None / when the list is empty / when called twice."

## Step 4 — Suggest the Fix
- One fix at a time — don't suggest 3 possible causes simultaneously
- Show the exact line to change with before/after
- If the root cause is unclear, add a `print()` or `logging.debug()` to narrow it down — don't guess

## Never
- "Try restarting" as a first suggestion
- Suggest changing library versions before understanding the error
- Suggest `except Exception: pass` as a fix
- Blame the framework before checking user code
