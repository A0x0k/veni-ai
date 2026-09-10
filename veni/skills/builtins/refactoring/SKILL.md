---
name: "Refactoring"
description: "Safe, incremental code restructuring with diffs and rationale"
triggers: ["refactor", "clean up", "restructure", "extract", "simplify", "reorganize", "improve code"]
version: "1.0.0"
author: "veni-team"
---

# Refactoring Skill

## Rules Before Starting
- Never refactor and fix a bug in the same change — separate commits
- Always confirm tests pass before and after
- Show changes as diffs, not full rewrites
- One refactoring type per response — don't mix extract + rename + restructure

## When to Extract a Function
Extract when:
- The same logic appears 2+ times
- A block has a comment explaining what it does (the comment = the function name)
- A function is >40 lines
- A block can be named in one phrase without "and"

Don't extract when:
- It would only be called once and the name adds no clarity
- It would require passing 5+ parameters

## When to Extract a Class
Extract when:
- Multiple functions share the same state (dict/list passed around)
- A function has grown >3 related helper functions
- You need to mock or test a subsystem in isolation

Don't extract when:
- A dataclass or namedtuple would suffice
- The "class" would have only one method

## Naming
- Functions: verb phrase — `calculate_tax`, `fetch_user`, `is_valid`
- Classes: noun — `UserRepository`, `PaymentProcessor`
- Booleans: `is_`, `has_`, `can_`, `should_` prefix
- Never: `data`, `info`, `manager`, `handler`, `util` without a qualifier

## Circular Import Fix Pattern
```
# Before: a.py imports b.py, b.py imports a.py
# Fix: extract shared types to c.py, both import from c.py
```

## Output Format
Show each change as:
```
# Before
<old code>

# After
<new code>

# Why: one sentence
```
