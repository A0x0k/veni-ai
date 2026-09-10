# Security Policy

We take the security of your codebase and your data seriously. Veni-AI is designed to interact with your local filesystem and execute shell commands, which necessitates strict safety boundaries.

## 🛡️ Approval Gates
Veni-AI includes a risk-tiered safety layer designed to intercept and prompt for approval before executing dangerous operations:
- **High-Risk Commands:** Commands like `rm -rf`, `format`, or recursive deletions require explicit user confirmation.
- **File System Limits:** All file read/write operations are constrained to the current working directory.

> ⚠️ **Warning:** The approval gate is a best-effort safety mechanism and does not provide a hard security boundary. If you are interacting with untrusted codebases, we strongly recommend running Veni-AI inside a containerized environment (e.g., Docker) or a dedicated virtual machine.

## Reporting Vulnerabilities
If you discover a security vulnerability in Veni-AI, please do not disclose it in a public issue. Instead, contact the maintainer directly.
