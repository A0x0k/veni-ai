---
name: "Testing"
description: "pytest patterns, fixture design, mocking strategy, and coverage"
triggers: ["test", "pytest", "tdd", "mock", "coverage", "unit test", "integration test", "assert", "fixture"]
version: "2.0.0"
author: "veni-team"
---

# Testing Skill

When helping with tests, always:

## Code Generation Rules
- Generate tests in the same file structure as the source: `src/auth.py` → `tests/test_auth.py`
- Use `pytest` fixtures over `setUp`/`tearDown` — prefer `conftest.py` for shared fixtures
- Name tests as `test_<what>_<when>_<expected>`: `test_login_with_expired_token_raises_401`
- Use `pytest.mark.parametrize` when testing the same logic with 3+ inputs
- Use `pytest.raises(ExceptionType, match="regex")` — always include `match` to avoid false passes

## What to Mock
- Mock at the boundary: patch `requests.get`, not internal helpers that call it
- Use `unittest.mock.patch` as a decorator for class-level patches, context manager for local
- Never mock `datetime.datetime.now` directly — mock the module that imports it
- Prefer `MagicMock(spec=RealClass)` over bare `MagicMock()` to catch attribute typos

## What NOT to Mock
- Don't mock the thing you're testing
- Don't mock `pathlib.Path` — use `tmp_path` fixture instead
- Don't mock `json.loads` — use real data

## Coverage
- Run with `pytest --cov=src --cov-branch --cov-report=term-missing`
- Focus coverage on: error paths, edge cases, conditional branches
- A test that only covers the happy path is worth less than its line count suggests

## Common Mistakes to Flag
- `assert mock.called` — use `mock.assert_called_once_with(...)` instead
- Testing private methods directly — test through the public interface
- `time.sleep` in tests — use `freezegun` or mock the clock
- Assertions after `return` in a helper — they'll never run
