---
name: "Python Web Development"
description: "Django, Flask, FastAPI — patterns, pitfalls, and production concerns"
triggers: ["django", "flask", "fastapi", "web api", "orm", "web framework", "endpoint", "middleware", "pydantic"]
version: "2.0.0"
author: "veni-team"
---

# Python Web Development Skill

## FastAPI Specifics
- Use `Depends()` for auth, DB sessions, and shared logic — never global state
- Return Pydantic models, not dicts — enables automatic OpenAPI docs
- Use `BackgroundTasks` for fire-and-forget, `asyncio.create_task` for awaitable work
- `HTTPException` with `detail=` should be user-safe — never leak stack traces
- Use `lifespan` context manager for startup/shutdown, not deprecated `@app.on_event`

## Django Specifics
- Use `select_related` / `prefetch_related` — flag N+1 queries in views
- Never use `objects.all()` in a view without `.only()` or pagination
- Use `get_object_or_404` over bare `.get()` in views
- Custom managers over raw SQL unless performance demands it
- `settings.py` secrets must come from env vars — flag hardcoded `SECRET_KEY`

## Flask Specifics
- Use application factory pattern (`create_app()`) — never module-level `app = Flask(__name__)`
- Use `flask.g` for request-scoped state, not global variables
- Always set `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`

## Cross-Framework Rules
- Validate all input at the boundary — don't trust path params, query strings, or headers
- Paginate all list endpoints — flag any endpoint returning unbounded querysets
- Log request IDs for traceability — flag endpoints with no structured logging
- Rate-limit auth endpoints — flag `/login`, `/register`, `/reset-password` without limits
