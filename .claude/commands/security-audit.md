---
description: Security, auth, permissions, CDD/consent auditor for project. Use on /security-audit , post-dep or form changes.
argument-hint: Focus, e.g. '2FA flows', 'Filament policies', 'artifact scan'
allowed-tools: Read, Grep, Glob, Bash
---

# Security Audit Agent

1. Run `/load-cache`.
2. Read and embody the full instructions in [`.claude/agents/security-audit.md`](../../.claude/agents/security-audit.md).
3. Enforce security checklist (ci_security_checklist.sh) for dep/form changes.
4. Flag high/critical immediately.
5. Read-only unless scoped; follow copilot-instructions §8,3.

Cite caches + artifacts in reports/security/.

User focus (optional): $ARGUMENTS
