---
name: "Security Audit"
description: "Code review for vulnerabilities: injection, auth, secrets, path traversal"
triggers: ["security", "vulnerability", "audit", "owasp", "pentest", "cve", "exploit", "auth", "injection", "xss", "csrf"]
version: "2.0.0"
author: "veni-team"
---

# Security Audit Skill

When reviewing code for security, always check these in order:

## Injection (Highest Priority)
- SQL: flag any string formatting/concatenation in queries — require parameterized queries
- Shell: flag `subprocess.run(shell=True, ...)` with user input — require list form
- Path traversal: flag `open(user_input)` without `Path.resolve()` + workspace check
- Template injection: flag `render_template_string(user_input)` patterns

## Secrets & Credentials
- Flag any hardcoded string that looks like a key/token/password (regex: `[A-Za-z0-9+/]{20,}=*`)
- Flag `.env` files being committed (check `.gitignore`)
- Flag API keys in logs or error messages

## Authentication & Authorization
- Flag missing auth checks on endpoints that modify data
- Flag JWT verification that doesn't check `exp`, `iss`, or `aud`
- Flag session tokens that don't use `secrets.token_urlsafe()`
- Flag password comparison with `==` instead of `hmac.compare_digest()`

## Output Encoding (XSS)
- Flag `innerHTML =` with user data in JS
- Flag unescaped `{{ variable }}` in Jinja2 with `| safe` filter
- Flag `Response(user_input, mimetype='text/html')` without sanitization

## Response Format
For each finding, output exactly:
```
[SEVERITY] Location: file.py:line
Issue: one sentence
Fix: one sentence or code snippet
```
Severity levels: CRITICAL / HIGH / MEDIUM / LOW
