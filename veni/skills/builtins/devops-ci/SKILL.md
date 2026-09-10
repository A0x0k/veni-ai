---
name: "DevOps & CI/CD"
description: "Docker, GitHub Actions, Kubernetes — production-ready patterns and common mistakes"
triggers: ["docker", "kubernetes", "ci/cd", "github actions", "deploy", "monitoring", "devops", "dockerfile", "helm", "k8s", "pipeline"]
version: "2.0.0"
author: "veni-team"
---

# DevOps & CI/CD Skill

## Dockerfile — Flag These Patterns
- `FROM python:3.11` → require `FROM python:3.11-slim` or pinned digest
- `RUN pip install -r requirements.txt` without `--no-cache-dir` → wastes layer space
- `COPY . .` before installing dependencies → breaks layer caching; copy requirements first
- Running as root → require `USER nonroot` or `USER 1000`
- No `.dockerignore` → flag if `.git`, `__pycache__`, `*.pyc` would be copied

## GitHub Actions — Flag These Patterns
- `actions/checkout@v3` → suggest `@v4`
- `pip install` without caching → add `actions/setup-python` with `cache: pip`
- Secrets in `env:` at job level → move to step level for least privilege
- No `timeout-minutes:` on jobs → runaway jobs burn minutes silently
- `on: push` to main without branch protection → flag missing PR requirement

## Kubernetes — Flag These Patterns
- No `resources.requests` / `resources.limits` → pods get evicted under pressure
- `imagePullPolicy: Always` in production → use `IfNotPresent` with pinned tags
- No `readinessProbe` → traffic hits pods before they're ready
- `replicas: 1` for a stateless service → no HA
- Secrets in `ConfigMap` → must be in `Secret` with RBAC

## CI Pipeline Order (Fastest Feedback First)
1. Lint + type check (< 30s)
2. Unit tests (< 2min)
3. Build Docker image
4. Integration tests
5. Deploy to staging → smoke test
6. Deploy to production
