---
name: "Log Analysis"
description: "Parse logs, extract error patterns, summarise incidents, identify root cause"
triggers: ["logs", "log file", "analyze logs", "error rate", "log analysis", "incident", "syslog", "journalctl", "access log"]
version: "1.0.0"
author: "veni-team"
---

# Log Analysis Skill

## Approach
When given log output:
1. Identify the first error — not the most frequent, the *earliest*
2. Find the timestamp of the first anomaly
3. Look for what changed just before: deployment, config change, traffic spike
4. Distinguish symptoms (many 500s) from cause (DB connection pool exhausted)

## Common Log Formats

**nginx/Apache access log:**
```
# Error rate: count non-2xx
awk '$9 >= 400' access.log | wc -l

# Top error URLs
awk '$9 >= 400 {print $7}' access.log | sort | uniq -c | sort -rn | head 20

# Requests per minute
awk '{print $4}' access.log | cut -d: -f1,2 | uniq -c
```

**Python/gunicorn:**
- `[ERROR]` lines are actionable — `[WARNING]` may not be
- Tracebacks span multiple lines — the *last* line before the next timestamp is the error type
- `worker timeout` = request took too long, not a code bug

**systemd/journalctl:**
```bash
journalctl -u myservice --since "1 hour ago" -p err
journalctl -u myservice --since "2024-01-01" --until "2024-01-02"
```

## Summarising an Incident
Always output:
```
Timeline:
  HH:MM — first anomaly
  HH:MM — error rate exceeded X%
  HH:MM — service recovered / still ongoing

Root Cause: one sentence
Impact: X requests failed over Y minutes
Fix Applied: what was done
Prevention: what would stop recurrence
```

## Patterns That Indicate Specific Problems
- Repeated `Connection refused` → downstream service down or port wrong
- `Too many open files` → file descriptor leak, check `ulimit`
- `Out of memory` → memory leak or undersized instance
- `SSL handshake failed` → cert expired or clock skew
- Sudden spike then silence → process crashed and wasn't restarted
