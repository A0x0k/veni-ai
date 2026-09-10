---
name: "Documentation"
description: "Docstrings, README, API docs — what to write and what to skip"
triggers: ["documentation", "docstring", "readme", "api docs", "write docs", "document", "mkdocs", "sphinx"]
version: "2.0.0"
author: "veni-team"
---

# Documentation Skill

## Docstrings — When and What
Write a docstring when:
- The function name alone doesn't explain *why* it exists
- The return value is non-obvious (e.g. returns `None` on failure vs raises)
- There are gotchas: side effects, mutates input, not thread-safe

Skip docstrings on:
- `__init__` when the class docstring covers it
- One-liner helpers where the name is self-documenting

Use Google style:
```python
def fetch_user(user_id: int) -> User | None:
    """Fetch a user by ID, returning None if not found (never raises).

    Args:
        user_id: Must be positive; negative IDs are reserved for system accounts.

    Returns:
        User object, or None if the ID doesn't exist in the database.
    """
```

## README — Required Sections in Order
1. One-line description (what it does, not what it is)
2. Install: `pip install x` — nothing else on this line
3. Quickstart: working code in < 5 lines
4. Configuration: only non-obvious options
5. Contributing: one sentence + link

Flag READMEs that: lead with architecture diagrams, require 10+ steps before first run, or have no code examples.

## API Docs
- Every public endpoint needs: method, path, auth requirement, request body schema, response schema, error codes
- Include a `curl` example for every endpoint — it's the fastest way to verify docs are correct
- Document what happens on partial failure, not just success

## What to Flag
- `# TODO` comments older than the last release — they're permanent lies
- Comments that restate the code: `i += 1  # increment i`
- Outdated parameter names in docstrings after a rename
